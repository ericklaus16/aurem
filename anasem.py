"""
Analisador Semântico para a linguagem AUREM
Verifica:
1. Declaração de variáveis antes do uso
2. Redeclaração de variáveis (erro)
3. Compatibilidade de tipos em atribuições
4. Compatibilidade de tipos em operações aritméticas
5. Compatibilidade de tipos em operações lógicas/relacionais
6. Acesso a arrays com índices inteiros
7. Atribuição de arrays com tipos compatíveis
"""


class TabelaSimbolos:
    """Tabela de símbolos para armazenar variáveis e seus tipos"""

    def __init__(self):
        self.simbolos = {}  # {nome_var: {'tipo': tipo, 'is_array': bool, 'linha_decl': int}}
        self.escopos = [{}]  # Pilha de escopos (para blocos)

    def entrar_escopo(self):
        """Cria um novo escopo (ex: ao entrar em um bloco {})"""
        self.escopos.append({})

    def sair_escopo(self):
        """Remove o escopo atual"""
        if len(self.escopos) > 1:
            self.escopos.pop()

    def declarar(self, nome, tipo, is_array, linha):
        """Declara uma variável no escopo atual"""
        # Verifica se já existe no escopo atual
        if nome in self.escopos[-1]:
            return False, f"Variável '{nome}' já declarada neste escopo (linha {self.escopos[-1][nome]['linha_decl']})"

        self.escopos[-1][nome] = {
            'tipo': tipo,
            'is_array': is_array,
            'linha_decl': linha
        }
        return True, None

    def buscar(self, nome):
        """Busca uma variável em todos os escopos (do mais interno ao mais externo)"""
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

    def existe(self, nome):
        """Verifica se uma variável existe"""
        return self.buscar(nome) is not None


class AnalisadorSemantico:
    """Analisador semântico para AUREM"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.tabela = TabelaSimbolos()
        self.erros = []
        self.avisos = []

    def token_atual(self):
        """Retorna o token atual"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF', 'EOF', -1)

    def avancar(self):
        """Avança para o próximo token"""
        self.pos += 1

    def olhar_adiante(self, n=1):
        """Olha n tokens à frente sem consumir"""
        pos_futuro = self.pos + n
        if pos_futuro < len(self.tokens):
            return self.tokens[pos_futuro]
        return ('EOF', 'EOF', -1)

    def erro(self, mensagem, linha):
        """Registra um erro semântico"""
        self.erros.append(f"Erro semântico na linha {linha}: {mensagem}")

    def aviso(self, mensagem, linha):
        """Registra um aviso"""
        self.avisos.append(f"Aviso na linha {linha}: {mensagem}")

    def analisar(self):
        """Executa a análise semântica"""
        while self.pos < len(self.tokens):
            self.analisar_comando()
        return self.erros, self.avisos

    def analisar_comando(self):
        """Analisa um comando"""
        kind, value, linha = self.token_atual()

        if kind == 'id':
            self.analisar_declaracao_ou_atribuicao()
        elif kind == 'IF':
            self.analisar_if()
        elif kind == 'WHILE':
            self.analisar_while()
        elif kind == 'FOR':
            self.analisar_for()
        elif kind == 'READ':
            self.analisar_read()
        elif kind == 'PRINT':
            self.analisar_print()
        elif kind == 'ABRE_CHAVE':
            self.analisar_bloco()
        elif kind == 'FECHA_CHAVE':
            self.avancar()
        else:
            self.avancar()

    def analisar_declaracao_ou_atribuicao(self):
        """Analisa declaração de variável ou atribuição"""
        kind, nome_var, linha = self.token_atual()
        self.avancar()

        prox_kind, prox_value, _ = self.token_atual()

        # É declaração: $var<tipo>
        if prox_kind == 'MENOR':
            self.avancar()  # consome '<'
            tipo, is_array = self.extrair_tipo()

            # Verifica se fecha o tipo com '>'
            if self.token_atual()[0] == 'MAIOR':
                self.avancar()  # consome '>'

            # Tenta declarar a variável
            sucesso, msg_erro = self.tabela.declarar(
                nome_var, tipo, is_array, linha)
            if not sucesso:
                self.erro(msg_erro, linha)

            # Verifica se há atribuição
            if self.token_atual()[1] == '=':
                self.avancar()  # consome '='
                tipo_expr = self.analisar_expressao()
                self.verificar_compatibilidade_atribuicao(
                    tipo, is_array, tipo_expr, nome_var, linha)

        # É atribuição: $var = expr ou $var += expr, etc.
        elif prox_kind in ['ATRIBUICAO', 'OP_REL']:
            op = prox_value

            # Verifica se variável foi declarada
            info_var = self.tabela.buscar(nome_var)
            if info_var is None:
                self.erro(f"Variável '{nome_var}' não foi declarada", linha)
                # Pula até o próximo ponto e vírgula
                while self.pos < len(self.tokens) and self.token_atual()[0] != 'PONTO_VIRGULA':
                    self.avancar()
                if self.pos < len(self.tokens):
                    self.avancar()  # consome ';'
                return

            self.avancar()  # consome operador

            # Operadores compostos (+=, -=, etc.) requerem tipo numérico
            if op in ['+=', '-=', '*=', '/=', '%=']:
                if info_var['tipo'] not in ['int', 'float']:
                    self.erro(
                        f"Operador '{op}' requer tipo numérico, mas '{nome_var}' é do tipo '{info_var['tipo']}'", linha)

            tipo_expr = self.analisar_expressao()
            if op == '=':
                self.verificar_compatibilidade_atribuicao(
                    info_var['tipo'], info_var['is_array'], tipo_expr, nome_var, linha)
            else:
                # Para operadores compostos, verifica se expressão é numérica
                if tipo_expr not in ['int', 'float', 'unknown']:
                    self.erro(
                        f"Operador '{op}' requer expressão numérica, encontrado tipo '{tipo_expr}'", linha)

        # Pula até o ponto e vírgula se existir
        while self.pos < len(self.tokens) and self.token_atual()[0] != 'PONTO_VIRGULA':
            self.avancar()
        if self.pos < len(self.tokens):
            self.avancar()  # consome ';'

    def extrair_tipo(self):
        """Extrai o tipo da declaração e retorna (tipo_base, is_array)"""
        kind, value, _ = self.token_atual()
        tipo_base = None
        is_array = False

        if kind == 'TIPO':
            tipo_base = value
            self.avancar()
        elif value in ['int', 'float', 'string', 'bool']:
            tipo_base = value
            self.avancar()

        # Verifica se é array
        if self.token_atual()[0] == 'VETOR':
            is_array = True
            self.avancar()
        elif self.token_atual()[0] == 'ABRE_COLCHETE':
            self.avancar()  # consome '['
            # Pode ter um número opcional
            if self.token_atual()[0] == 'NUMERO':
                self.avancar()
            if self.token_atual()[0] == 'FECHA_COLCHETE':
                self.avancar()  # consome ']'
            is_array = True

        return tipo_base, is_array

    def verificar_compatibilidade_atribuicao(self, tipo_var, is_array_var, tipo_expr, nome_var, linha):
        """Verifica se a atribuição é compatível"""
        if tipo_expr == 'unknown':
            return  # Não conseguimos determinar o tipo, ignora

        # 'any' é compatível com qualquer tipo (usado por read())
        if tipo_expr == 'any':
            return

        # Se é array, tipo_expr deve ser 'array_X' compatível
        if is_array_var:
            if tipo_expr.startswith('array_'):
                tipo_elem_expr = tipo_expr[6:]  # remove 'array_'
                if not self.tipos_compativeis(tipo_var, tipo_elem_expr):
                    self.erro(
                        f"Tipo incompatível: '{nome_var}' é array de '{tipo_var}', mas recebeu array de '{tipo_elem_expr}'", linha)
            else:
                # Tentando atribuir valor não-array a uma variável array
                self.erro(
                    f"Tipo incompatível: '{nome_var}' é um array de '{tipo_var}', mas recebeu '{tipo_expr}' (esperado array)", linha)
        else:
            # Variável simples
            if tipo_expr.startswith('array_'):
                self.erro(
                    f"Não é possível atribuir array a variável simples '{nome_var}'", linha)
            elif not self.tipos_compativeis(tipo_var, tipo_expr):
                self.erro(
                    f"Tipo incompatível: '{nome_var}' é do tipo '{tipo_var}', mas recebeu '{tipo_expr}'", linha)

    def tipos_compativeis(self, tipo1, tipo2):
        """Verifica se dois tipos são compatíveis para ATRIBUIÇÃO"""
        if tipo1 == tipo2:
            return True
        # 'any' é compatível com qualquer tipo (usado por read())
        if tipo1 == 'any' or tipo2 == 'any':
            return True
        # int e float são compatíveis (coerção numérica)
        if {tipo1, tipo2} == {'int', 'float'}:
            return True
        # Para atribuição, tipos devem ser iguais (exceto int/float)
        return False

    def tipos_compativeis_operacao(self, tipo1, tipo2, operador):
        """Verifica se dois tipos são compatíveis para uma OPERAÇÃO específica"""
        if tipo1 == tipo2:
            return True
        # 'any' é compatível com qualquer tipo
        if tipo1 == 'any' or tipo2 == 'any':
            return True
        # int e float são compatíveis em operações aritméticas
        if {tipo1, tipo2} == {'int', 'float'}:
            return True
        # Concatenação de string com + aceita qualquer tipo
        if operador == '+' and (tipo1 == 'string' or tipo2 == 'string'):
            return True
        return False

    def verificar_compatibilidade_comparacao(self, tipo1, tipo2, operador, linha):
        """Verifica se dois tipos são compatíveis para uma COMPARAÇÃO"""
        if tipo1 == 'unknown' or tipo2 == 'unknown':
            return  # Não conseguimos determinar o tipo, ignora

        # 'any' é compatível com qualquer tipo (usado por read())
        if tipo1 == 'any' or tipo2 == 'any':
            return

        # Tipos iguais podem ser comparados
        if tipo1 == tipo2:
            return

        # int e float podem ser comparados entre si
        if {tipo1, tipo2} == {'int', 'float'}:
            return

        # Operadores de igualdade (== e !=) entre tipos incompatíveis
        if operador in ['==', '!=']:
            self.erro(
                f"Comparação '{operador}' entre tipos incompatíveis: '{tipo1}' e '{tipo2}'", linha)
        # Operadores de ordenação (<, >, <=, >=) requerem tipos comparáveis
        elif operador in ['<', '>', '<=', '>=']:
            self.erro(
                f"Operador '{operador}' não pode comparar '{tipo1}' com '{tipo2}'", linha)
        # Operadores lógicos (&& e ||) requerem booleanos
        elif operador in ['&&', '||']:
            if tipo1 != 'bool' or tipo2 != 'bool':
                self.erro(
                    f"Operador '{operador}' requer operandos booleanos, encontrado '{tipo1}' e '{tipo2}'", linha)

    def analisar_expressao(self):
        """Analisa uma expressão e retorna seu tipo"""
        tipo_esq = self.analisar_termo()

        while self.pos < len(self.tokens):
            kind, value, linha = self.token_atual()

            # Operadores aritméticos
            if value in ['+', '-']:
                self.avancar()
                tipo_dir = self.analisar_termo()
                tipo_esq = self.tipo_resultado_aritmetico(
                    tipo_esq, tipo_dir, value, linha)
            # Operadores relacionais/lógicos
            elif value in ['==', '!=', '<', '>', '<=', '>=', '&&', '||']:
                self.avancar()
                tipo_dir = self.analisar_termo()
                # Verifica compatibilidade de tipos na comparação
                self.verificar_compatibilidade_comparacao(
                    tipo_esq, tipo_dir, value, linha)
                tipo_esq = 'bool'  # Resultado de comparação é sempre bool
            else:
                break

        return tipo_esq

    def analisar_termo(self):
        """Analisa um termo e retorna seu tipo"""
        tipo_esq = self.analisar_fator()

        while self.pos < len(self.tokens):
            kind, value, _ = self.token_atual()

            if value in ['*', '/', '%']:
                linha = self.token_atual()[2]
                self.avancar()
                tipo_dir = self.analisar_fator()
                tipo_esq = self.tipo_resultado_aritmetico(
                    tipo_esq, tipo_dir, value, linha)
            else:
                break

        return tipo_esq

    def analisar_fator(self):
        """Analisa um fator e retorna seu tipo"""
        kind, value, linha = self.token_atual()

        if kind == 'NUMERO':
            self.avancar()
            # Verifica se é float ou int
            if '.' in value:
                return 'float'
            return 'int'

        elif kind == 'STRING':
            self.avancar()
            return 'string'

        elif kind == 'TRUE' or kind == 'FALSE':
            self.avancar()
            return 'bool'

        elif kind == 'id':
            nome_var = value
            self.avancar()

            info = self.tabela.buscar(nome_var)
            if info is None:
                self.erro(f"Variável '{nome_var}' não foi declarada", linha)
                return 'unknown'

            # Verifica se é acesso a array
            if self.token_atual()[0] == 'ABRE_COLCHETE':
                self.avancar()  # consome '['
                tipo_indice = self.analisar_expressao()

                if tipo_indice not in ['int', 'unknown']:
                    self.erro(
                        f"Índice de array deve ser inteiro, encontrado '{tipo_indice}'", linha)

                if self.token_atual()[0] == 'FECHA_COLCHETE':
                    self.avancar()  # consome ']'

                if not info['is_array']:
                    self.erro(f"Variável '{nome_var}' não é um array", linha)

                return info['tipo']  # Retorna tipo do elemento

            if info['is_array']:
                return f"array_{info['tipo']}"
            return info['tipo']

        elif kind == 'ABRE_PAREN':
            self.avancar()  # consome '('
            tipo = self.analisar_expressao()
            if self.token_atual()[0] == 'FECHA_PAREN':
                self.avancar()  # consome ')'
            return tipo

        elif kind == 'ABRE_CHAVE':
            # Array literal
            return self.analisar_array_literal()

        elif kind == 'READ':
            return self.analisar_read_expressao()

        elif kind == 'OP_ARIT' and value in ['+', '-']:
            # Operador unário
            self.avancar()
            return self.analisar_fator()

        else:
            self.avancar()
            return 'unknown'

    def analisar_array_literal(self):
        """Analisa um literal de array e retorna seu tipo"""
        self.avancar()  # consome '{'
        linha = self.token_atual()[2]

        tipos_elementos = []
        while self.pos < len(self.tokens) and self.token_atual()[0] != 'FECHA_CHAVE':
            tipo_elem = self.analisar_expressao()
            tipos_elementos.append(tipo_elem)

            if self.token_atual()[0] == 'VIRGULA':
                self.avancar()  # consome ','

        if self.token_atual()[0] == 'FECHA_CHAVE':
            self.avancar()  # consome '}'

        # Determina tipo do array
        if not tipos_elementos:
            return 'array_unknown'

        tipo_base = tipos_elementos[0]
        for t in tipos_elementos[1:]:
            if t != tipo_base and t != 'unknown' and tipo_base != 'unknown':
                if not self.tipos_compativeis(tipo_base, t):
                    self.aviso(
                        f"Array com elementos de tipos mistos: '{tipo_base}' e '{t}'", linha)
                # Promove para tipo mais abrangente
                if 'float' in [tipo_base, t]:
                    tipo_base = 'float'

        return f"array_{tipo_base}"

    def analisar_read_expressao(self):
        """Analisa read() como expressão e retorna seu tipo"""
        self.avancar()  # consome 'read'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()  # consome '('

        # Pula a string do prompt
        if self.token_atual()[0] == 'STRING':
            self.avancar()

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()  # consome ')'

        # read() retorna um valor que será convertido conforme contexto
        # Em AUREM, read() é polimórfico - o tipo é determinado pela variável de destino
        return 'any'  # Tipo especial que é compatível com qualquer tipo

    def tipo_resultado_aritmetico(self, tipo1, tipo2, operador, linha):
        """Determina o tipo resultado de uma operação aritmética"""
        if tipo1 == 'unknown' or tipo2 == 'unknown':
            return 'unknown'

        # Concatenação de string
        if operador == '+' and (tipo1 == 'string' or tipo2 == 'string'):
            return 'string'

        # Operações numéricas
        if tipo1 in ['int', 'float'] and tipo2 in ['int', 'float']:
            if operador == '%':
                if tipo1 == 'float' or tipo2 == 'float':
                    self.aviso(
                        f"Operador '%' com float pode ter comportamento inesperado", linha)
            if tipo1 == 'float' or tipo2 == 'float':
                return 'float'
            return 'int'

        # Erro: operação aritmética inválida
        if tipo1 not in ['int', 'float', 'string'] or tipo2 not in ['int', 'float', 'string']:
            self.erro(
                f"Operador '{operador}' não pode ser aplicado entre '{tipo1}' e '{tipo2}'", linha)

        return 'unknown'

    def analisar_if(self):
        """Analisa comando if"""
        self.avancar()  # consome 'if'
        linha = self.token_atual()[2]

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()  # consome '('

        tipo_condicao = self.analisar_expressao()

        # Condição deve ser booleana (ou conversível)
        if tipo_condicao not in ['bool', 'int', 'unknown']:
            self.aviso(
                f"Condição do 'if' deveria ser booleana, encontrado '{tipo_condicao}'", linha)

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()  # consome ')'

        # Analisa o corpo do if
        self.analisar_comando()

        # Verifica else
        if self.token_atual()[0] == 'ELSE':
            self.avancar()  # consome 'else'
            self.analisar_comando()

    def analisar_while(self):
        """Analisa comando while"""
        self.avancar()  # consome 'while'
        linha = self.token_atual()[2]

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        tipo_condicao = self.analisar_expressao()

        if tipo_condicao not in ['bool', 'int', 'unknown']:
            self.aviso(
                f"Condição do 'while' deveria ser booleana, encontrado '{tipo_condicao}'", linha)

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        self.analisar_comando()

    def analisar_for(self):
        """Analisa comando for"""
        self.avancar()  # consome 'for'

        # O for cria seu próprio escopo para a variável de controle
        self.tabela.entrar_escopo()

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        # Inicialização (pode ser declaração ou atribuição)
        if self.token_atual()[0] == 'id':
            nome_var = self.token_atual()[1]
            linha_var = self.token_atual()[2]
            self.avancar()

            if self.token_atual()[0] == 'MENOR':
                # Declaração
                self.avancar()  # consome '<'
                tipo, is_array = self.extrair_tipo()

                if self.token_atual()[0] == 'MAIOR':
                    self.avancar()  # consome '>'

                sucesso, msg_erro = self.tabela.declarar(
                    nome_var, tipo, is_array, linha_var)
                if not sucesso:
                    self.erro(msg_erro, linha_var)

                if self.token_atual()[0] == 'ATRIBUICAO':
                    self.avancar()  # consome '='
                    self.analisar_expressao()
            else:
                # Atribuição - variável deve existir
                info = self.tabela.buscar(nome_var)
                if info is None:
                    self.erro(
                        f"Variável '{nome_var}' não foi declarada", linha_var)

                if self.token_atual()[0] in ['ATRIBUICAO', 'OP_REL']:
                    self.avancar()
                    self.analisar_expressao()

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()  # consome ';'

        # Condição
        linha_cond = self.token_atual()[2]
        tipo_condicao = self.analisar_expressao()

        if tipo_condicao not in ['bool', 'int', 'unknown']:
            self.aviso(
                f"Condição do 'for' deveria ser booleana, encontrado '{tipo_condicao}'", linha_cond)

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()  # consome ';'

        # Incremento
        if self.token_atual()[0] == 'id':
            nome_inc = self.token_atual()[1]
            linha_inc = self.token_atual()[2]
            self.avancar()

            info = self.tabela.buscar(nome_inc)
            if info is None:
                self.erro(
                    f"Variável '{nome_inc}' não foi declarada", linha_inc)

            if self.token_atual()[0] in ['ATRIBUICAO', 'OP_REL']:
                self.avancar()
                self.analisar_expressao()

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()  # consome ')'

        # Corpo do for
        self.analisar_comando()

        # Sai do escopo do for
        self.tabela.sair_escopo()

    def analisar_read(self):
        """Analisa comando read"""
        self.avancar()  # consome 'read'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        if self.token_atual()[0] == 'id':
            nome_var = self.token_atual()[1]
            linha = self.token_atual()[2]
            self.avancar()

            if not self.tabela.existe(nome_var):
                self.erro(f"Variável '{nome_var}' não foi declarada", linha)

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()

    def analisar_print(self):
        """Analisa comando print"""
        self.avancar()  # consome 'print'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        # Primeiro argumento deve ser string
        if self.token_atual()[0] == 'STRING':
            self.avancar()

        # Pode ter concatenações
        while self.token_atual()[1] == '+':
            self.avancar()  # consome '+'
            self.analisar_expressao()

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()

    def analisar_bloco(self):
        """Analisa um bloco de comandos"""
        self.avancar()  # consome '{'
        self.tabela.entrar_escopo()

        while self.pos < len(self.tokens) and self.token_atual()[0] != 'FECHA_CHAVE':
            self.analisar_comando()

        self.tabela.sair_escopo()

        if self.token_atual()[0] == 'FECHA_CHAVE':
            self.avancar()  # consome '}'


def analisar_semantica(tokens):
    analisador = AnalisadorSemantico(tokens)
    erros, avisos = analisador.analisar()
    return erros, avisos
