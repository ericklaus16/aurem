"""
Gerador de Código Intermediário de 3 Endereços para a linguagem AUREM
Baseado nos conceitos de código intermediário apresentados nos PDFs de referência.

Tipos de instruções geradas:
- Atribuição: x = y op z
- Cópia: x = y
- Atribuição unária: x = op y
- Desvio incondicional: goto L
- Desvio condicional: if x relop y goto L / ifFalse x goto L
- Acesso a arrays: x = y[i] / x[i] = y
- Entrada/Saída: read x / print x
- Labels: L:
"""


class GeradorCodigoIntermediario:
    """Gerador de Código Intermediário de 3 Endereços"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.codigo = []  # Lista de instruções de 3 endereços
        self.temp_count = 0  # Contador de temporários
        self.label_count = 0  # Contador de labels
        self.tabela_simbolos = {}  # {nome_var: {'tipo': tipo, 'is_array': bool}}

    def novo_temp(self):
        """Gera um novo temporário"""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def novo_label(self):
        """Gera um novo label"""
        self.label_count += 1
        return f"L{self.label_count}"

    def emitir(self, instrucao):
        """Emite uma instrução de código intermediário"""
        self.codigo.append(instrucao)

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

    def gerar(self):
        """Gera o código intermediário para todo o programa"""
        self.emitir("# Início do Programa AUREM")
        self.emitir("")
        
        while self.pos < len(self.tokens):
            self.gerar_comando()
        
        self.emitir("")
        self.emitir("# Fim do Programa")
        
        return self.codigo

    def gerar_comando(self):
        """Gera código para um comando"""
        kind, value, linha = self.token_atual()

        if kind == 'id':
            self.gerar_declaracao_ou_atribuicao()
        elif kind == 'IF':
            self.gerar_if()
        elif kind == 'WHILE':
            self.gerar_while()
        elif kind == 'FOR':
            self.gerar_for()
        elif kind == 'READ':
            self.gerar_read()
        elif kind == 'PRINT':
            self.gerar_print()
        elif kind == 'ABRE_CHAVE':
            self.gerar_bloco()
        elif kind == 'FECHA_CHAVE':
            self.avancar()
        else:
            self.avancar()

    def gerar_declaracao_ou_atribuicao(self):
        """Gera código para declaração de variável ou atribuição"""
        kind, nome_var, linha = self.token_atual()
        self.avancar()

        prox_kind, prox_value, _ = self.token_atual()

        # É declaração: $var<tipo>
        if prox_kind == 'MENOR':
            self.avancar()  # consome '<'
            tipo, is_array = self.extrair_tipo()
            
            # Registra na tabela de símbolos
            self.tabela_simbolos[nome_var] = {'tipo': tipo, 'is_array': is_array}

            # Verifica se fecha o tipo com '>'
            if self.token_atual()[0] == 'MAIOR':
                self.avancar()  # consome '>'

            # Verifica se há atribuição
            if self.token_atual()[1] == '=':
                self.avancar()  # consome '='
                
                # Verifica se é inicialização de array
                if self.token_atual()[0] == 'ABRE_CHAVE':
                    self.gerar_inicializacao_array(nome_var)
                else:
                    temp_expr, _ = self.gerar_expressao()
                    self.emitir(f"{nome_var} = {temp_expr}")

        # É atribuição simples ou com índice de array
        elif prox_kind in ['ATRIBUICAO', 'OP_REL', 'ABRE_COLCHETE']:
            # Verifica se é acesso a array
            if prox_kind == 'ABRE_COLCHETE':
                self.avancar()  # consome '['
                indice_temp, _ = self.gerar_expressao()
                
                if self.token_atual()[0] == 'FECHA_COLCHETE':
                    self.avancar()  # consome ']'
                
                if self.token_atual()[0] in ['ATRIBUICAO', 'OP_REL']:
                    op = self.token_atual()[1]
                    self.avancar()  # consome operador
                    
                    if op == '=':
                        temp_expr, _ = self.gerar_expressao()
                        self.emitir(f"{nome_var}[{indice_temp}] = {temp_expr}")
                    else:
                        # Operador composto em array (+=, -=, etc.)
                        op_base = op[0]  # '+=' -> '+'
                        temp_atual = self.novo_temp()
                        self.emitir(f"{temp_atual} = {nome_var}[{indice_temp}]")
                        temp_expr, _ = self.gerar_expressao()
                        temp_result = self.novo_temp()
                        self.emitir(f"{temp_result} = {temp_atual} {op_base} {temp_expr}")
                        self.emitir(f"{nome_var}[{indice_temp}] = {temp_result}")
            else:
                op = prox_value
                self.avancar()  # consome operador
                
                if op == '=':
                    # Verifica se é atribuição de array
                    if self.token_atual()[0] == 'ABRE_CHAVE':
                        self.gerar_inicializacao_array(nome_var)
                    else:
                        temp_expr, _ = self.gerar_expressao()
                        self.emitir(f"{nome_var} = {temp_expr}")
                elif op == '++':
                    self.emitir(f"{nome_var} = {nome_var} + 1")
                elif op == '--':
                    self.emitir(f"{nome_var} = {nome_var} - 1")
                else:
                    # Operador composto (+=, -=, *=, /=, %=)
                    op_base = op[0]  # '+=' -> '+'
                    temp_expr, _ = self.gerar_expressao()
                    temp_result = self.novo_temp()
                    self.emitir(f"{temp_result} = {nome_var} {op_base} {temp_expr}")
                    self.emitir(f"{nome_var} = {temp_result}")

        # Pula até o ponto e vírgula
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
            if self.token_atual()[0] == 'NUMERO':
                self.avancar()
            if self.token_atual()[0] == 'FECHA_COLCHETE':
                self.avancar()  # consome ']'
            is_array = True

        return tipo_base, is_array

    def gerar_inicializacao_array(self, nome_var):
        """Gera código para inicialização de array literal"""
        self.avancar()  # consome '{'
        
        indice = 0
        while self.pos < len(self.tokens) and self.token_atual()[0] != 'FECHA_CHAVE':
            temp_elem, _ = self.gerar_expressao()
            self.emitir(f"{nome_var}[{indice}] = {temp_elem}")
            indice += 1

            if self.token_atual()[0] == 'VIRGULA':
                self.avancar()  # consome ','

        if self.token_atual()[0] == 'FECHA_CHAVE':
            self.avancar()  # consome '}'

    def gerar_expressao(self):
        """Gera código para uma expressão e retorna (temporário, tipo)"""
        return self.gerar_expressao_or()

    def gerar_expressao_or(self):
        """Gera código para expressão com || (OR lógico)"""
        temp_esq, tipo_esq = self.gerar_expressao_and()

        while self.pos < len(self.tokens) and self.token_atual()[1] == '||':
            self.avancar()  # consome '||'
            temp_dir, tipo_dir = self.gerar_expressao_and()
            temp_result = self.novo_temp()
            self.emitir(f"{temp_result} = {temp_esq} || {temp_dir}")
            temp_esq = temp_result
            tipo_esq = 'bool'

        return temp_esq, tipo_esq

    def gerar_expressao_and(self):
        """Gera código para expressão com && (AND lógico)"""
        temp_esq, tipo_esq = self.gerar_expressao_relacional()

        while self.pos < len(self.tokens) and self.token_atual()[1] == '&&':
            self.avancar()  # consome '&&'
            temp_dir, tipo_dir = self.gerar_expressao_relacional()
            temp_result = self.novo_temp()
            self.emitir(f"{temp_result} = {temp_esq} && {temp_dir}")
            temp_esq = temp_result
            tipo_esq = 'bool'

        return temp_esq, tipo_esq

    def gerar_expressao_relacional(self):
        """Gera código para expressão relacional"""
        temp_esq, tipo_esq = self.gerar_expressao_aditiva()

        while self.pos < len(self.tokens):
            _, value, _ = self.token_atual()
            if value in ['==', '!=', '<', '>', '<=', '>=']:
                op = value
                self.avancar()
                temp_dir, tipo_dir = self.gerar_expressao_aditiva()
                temp_result = self.novo_temp()
                self.emitir(f"{temp_result} = {temp_esq} {op} {temp_dir}")
                temp_esq = temp_result
                tipo_esq = 'bool'
            else:
                break

        return temp_esq, tipo_esq

    def gerar_expressao_aditiva(self):
        """Gera código para expressão com + e -"""
        temp_esq, tipo_esq = self.gerar_expressao_multiplicativa()

        while self.pos < len(self.tokens):
            _, value, _ = self.token_atual()
            if value in ['+', '-']:
                op = value
                self.avancar()
                temp_dir, tipo_dir = self.gerar_expressao_multiplicativa()
                temp_result = self.novo_temp()
                self.emitir(f"{temp_result} = {temp_esq} {op} {temp_dir}")
                temp_esq = temp_result
                # Determina tipo resultado
                if tipo_esq == 'string' or tipo_dir == 'string':
                    tipo_esq = 'string'
                elif tipo_esq == 'float' or tipo_dir == 'float':
                    tipo_esq = 'float'
                else:
                    tipo_esq = 'int'
            else:
                break

        return temp_esq, tipo_esq

    def gerar_expressao_multiplicativa(self):
        """Gera código para expressão com *, / e %"""
        temp_esq, tipo_esq = self.gerar_expressao_unaria()

        while self.pos < len(self.tokens):
            _, value, _ = self.token_atual()
            if value in ['*', '/', '%']:
                op = value
                self.avancar()
                temp_dir, tipo_dir = self.gerar_expressao_unaria()
                temp_result = self.novo_temp()
                self.emitir(f"{temp_result} = {temp_esq} {op} {temp_dir}")
                temp_esq = temp_result
                # Determina tipo resultado
                if tipo_esq == 'float' or tipo_dir == 'float':
                    tipo_esq = 'float'
                else:
                    tipo_esq = 'int'
            else:
                break

        return temp_esq, tipo_esq

    def gerar_expressao_unaria(self):
        """Gera código para expressão unária"""
        kind, value, _ = self.token_atual()

        if value == '-':
            self.avancar()
            temp_operando, tipo = self.gerar_fator()
            temp_result = self.novo_temp()
            self.emitir(f"{temp_result} = - {temp_operando}")
            return temp_result, tipo
        elif value == '!':
            self.avancar()
            temp_operando, _ = self.gerar_fator()
            temp_result = self.novo_temp()
            self.emitir(f"{temp_result} = ! {temp_operando}")
            return temp_result, 'bool'
        else:
            return self.gerar_fator()

    def gerar_fator(self):
        """Gera código para um fator e retorna (temporário, tipo)"""
        kind, value, linha = self.token_atual()

        if kind == 'NUMERO':
            self.avancar()
            if '.' in value:
                return value, 'float'
            return value, 'int'

        elif kind == 'STRING':
            self.avancar()
            return value, 'string'

        elif kind == 'TRUE':
            self.avancar()
            return 'true', 'bool'
            
        elif kind == 'FALSE':
            self.avancar()
            return 'false', 'bool'

        elif kind == 'id':
            nome_var = value
            self.avancar()

            # Verifica se é acesso a array
            if self.token_atual()[0] == 'ABRE_COLCHETE':
                self.avancar()  # consome '['
                indice_temp, _ = self.gerar_expressao()
                
                if self.token_atual()[0] == 'FECHA_COLCHETE':
                    self.avancar()  # consome ']'

                temp_result = self.novo_temp()
                self.emitir(f"{temp_result} = {nome_var}[{indice_temp}]")
                
                # Obtém tipo do elemento
                tipo = 'unknown'
                if nome_var in self.tabela_simbolos:
                    tipo = self.tabela_simbolos[nome_var]['tipo']
                return temp_result, tipo

            # Variável simples
            tipo = 'unknown'
            if nome_var in self.tabela_simbolos:
                info = self.tabela_simbolos[nome_var]
                tipo = info['tipo']
            return nome_var, tipo

        elif kind == 'ABRE_PAREN':
            self.avancar()  # consome '('
            temp, tipo = self.gerar_expressao()
            if self.token_atual()[0] == 'FECHA_PAREN':
                self.avancar()  # consome ')'
            return temp, tipo

        elif kind == 'READ':
            return self.gerar_read_expressao()

        else:
            self.avancar()
            return '?', 'unknown'

    def gerar_read_expressao(self):
        """Gera código para read() como expressão"""
        self.avancar()  # consome 'read'
        
        prompt = '""'
        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()  # consome '('
            
        if self.token_atual()[0] == 'STRING':
            prompt = self.token_atual()[1]
            self.avancar()
            
        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()  # consome ')'

        temp_result = self.novo_temp()
        self.emitir(f"param {prompt}")
        self.emitir(f"{temp_result} = call read, 1")
        return temp_result, 'any'

    def gerar_if(self, label_fim_externo=None):
        """Gera código para comando if"""
        self.avancar()  # consome 'if'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()  # consome '('

        # Gera código para condição
        temp_cond, _ = self.gerar_expressao()

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()  # consome ')'

        label_else = self.novo_label()
        # Usa label externo se existir (para else if encadeado)
        label_fim = label_fim_externo if label_fim_externo else self.novo_label()

        # Desvio condicional: se falso, vai para else
        self.emitir(f"ifFalse {temp_cond} goto {label_else}")

        # Gera código do bloco then
        self.gerar_comando()

        # Após then, desvia para o fim
        self.emitir(f"goto {label_fim}")

        # Label do else
        self.emitir(f"{label_else}:")

        # Verifica se tem else if (token ELSEIF) ou else
        if self.token_atual()[0] == 'ELSEIF':
            # else if encadeado - passa o label_fim para compartilhar
            self.avancar()  # consome 'else' do ELSEIF
            # O próximo já será 'if' por causa do normalize_tokens no aurem.py
            # Mas aqui temos tokens originais, então precisamos tratar
            self.gerar_if(label_fim)
            return  # Não emite label_fim aqui, será emitido pelo último if
        elif self.token_atual()[0] == 'ELSE':
            self.avancar()  # consome 'else'
            
            # Verifica se é else if (token IF após ELSE)
            if self.token_atual()[0] == 'IF':
                self.gerar_if(label_fim)
                return  # Não emite label_fim aqui
            else:
                self.gerar_comando()
                # Label do fim após o else
                self.emitir(f"{label_fim}:")
                return

        # Label do fim (apenas se não tinha else nem else if encadeado)
        self.emitir(f"{label_fim}:")

    def gerar_while(self):
        """Gera código para comando while"""
        self.avancar()  # consome 'while'

        label_inicio = self.novo_label()
        label_fim = self.novo_label()

        # Label de início do loop
        self.emitir(f"{label_inicio}:")

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        # Gera código para condição
        temp_cond, _ = self.gerar_expressao()

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        # Se condição falsa, sai do loop
        self.emitir(f"ifFalse {temp_cond} goto {label_fim}")

        # Gera código do corpo
        self.gerar_comando()

        # Volta para o início
        self.emitir(f"goto {label_inicio}")

        # Label do fim
        self.emitir(f"{label_fim}:")

    def gerar_for(self):
        """Gera código para comando for"""
        self.avancar()  # consome 'for'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        # Inicialização
        if self.token_atual()[0] == 'id':
            nome_var = self.token_atual()[1]
            self.avancar()

            if self.token_atual()[0] == 'MENOR':
                # Declaração com tipo
                self.avancar()  # consome '<'
                tipo, is_array = self.extrair_tipo()
                self.tabela_simbolos[nome_var] = {'tipo': tipo, 'is_array': is_array}

                if self.token_atual()[0] == 'MAIOR':
                    self.avancar()  # consome '>'

                if self.token_atual()[0] == 'ATRIBUICAO':
                    self.avancar()  # consome '='
                    temp_init, _ = self.gerar_expressao()
                    self.emitir(f"{nome_var} = {temp_init}")
            else:
                # Atribuição simples
                if self.token_atual()[0] in ['ATRIBUICAO', 'OP_REL']:
                    self.avancar()
                    temp_init, _ = self.gerar_expressao()
                    self.emitir(f"{nome_var} = {temp_init}")

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()  # consome ';'

        # Labels para o loop
        label_inicio = self.novo_label()
        label_fim = self.novo_label()

        # Label de início
        self.emitir(f"{label_inicio}:")

        # Condição
        temp_cond, _ = self.gerar_expressao()

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()  # consome ';'

        # Se condição falsa, sai
        self.emitir(f"ifFalse {temp_cond} goto {label_fim}")

        # Salva a posição para processar incremento depois
        pos_incremento = self.pos

        # Pula o incremento para processar o corpo primeiro
        while self.pos < len(self.tokens) and self.token_atual()[0] != 'FECHA_PAREN':
            self.avancar()
        
        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        # Gera código do corpo
        self.gerar_comando()

        # Agora processa o incremento
        # Volta para a posição do incremento
        pos_corpo = self.pos
        self.pos = pos_incremento

        # Gera código do incremento
        if self.token_atual()[0] == 'id':
            nome_inc = self.token_atual()[1]
            self.avancar()

            if self.token_atual()[0] in ['ATRIBUICAO', 'OP_REL']:
                op = self.token_atual()[1]
                self.avancar()

                if op == '=':
                    temp_val, _ = self.gerar_expressao()
                    self.emitir(f"{nome_inc} = {temp_val}")
                elif op == '++':
                    self.emitir(f"{nome_inc} = {nome_inc} + 1")
                elif op == '--':
                    self.emitir(f"{nome_inc} = {nome_inc} - 1")
                else:
                    # Operador composto
                    op_base = op[0]
                    temp_val, _ = self.gerar_expressao()
                    temp_result = self.novo_temp()
                    self.emitir(f"{temp_result} = {nome_inc} {op_base} {temp_val}")
                    self.emitir(f"{nome_inc} = {temp_result}")

        # Restaura posição
        self.pos = pos_corpo

        # Volta para o início
        self.emitir(f"goto {label_inicio}")

        # Label do fim
        self.emitir(f"{label_fim}:")

    def gerar_read(self):
        """Gera código para comando read"""
        self.avancar()  # consome 'read'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        if self.token_atual()[0] == 'id':
            nome_var = self.token_atual()[1]
            self.avancar()
            
            temp = self.novo_temp()
            self.emitir(f"param \"\"")
            self.emitir(f"{temp} = call read, 1")
            self.emitir(f"{nome_var} = {temp}")

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()

    def gerar_print(self):
        """Gera código para comando print"""
        self.avancar()  # consome 'print'

        if self.token_atual()[0] == 'ABRE_PAREN':
            self.avancar()

        # Gera código para a expressão a ser impressa
        temp_expr, _ = self.gerar_expressao()

        if self.token_atual()[0] == 'FECHA_PAREN':
            self.avancar()

        if self.token_atual()[0] == 'PONTO_VIRGULA':
            self.avancar()

        self.emitir(f"param {temp_expr}")
        self.emitir(f"call print, 1")

    def gerar_bloco(self):
        """Gera código para um bloco de comandos"""
        self.avancar()  # consome '{'

        while self.pos < len(self.tokens) and self.token_atual()[0] != 'FECHA_CHAVE':
            self.gerar_comando()

        if self.token_atual()[0] == 'FECHA_CHAVE':
            self.avancar()  # consome '}'


def gerar_codigo_intermediario(tokens):
    """Função principal para gerar código intermediário"""
    gerador = GeradorCodigoIntermediario(tokens)
    codigo = gerador.gerar()
    return codigo


def formatar_codigo(codigo):
    """Formata o código intermediário para exibição"""
    resultado = []
    num_instrucao = 0
    
    for linha in codigo:
        if linha.strip() == '' or linha.startswith('#'):
            resultado.append(linha)
        elif linha.endswith(':'):
            # Labels não são numerados
            resultado.append(linha)
        else:
            num_instrucao += 1
            resultado.append(f"({num_instrucao:3d}) {linha}")
    
    return resultado


def salvar_codigo(codigo, nome_arquivo):
    """Salva o código intermediário em um arquivo"""
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        for linha in codigo:
            f.write(linha + '\n')


# Teste se executado diretamente
if __name__ == "__main__":
    import analex
    
    # Código de teste
    codigo_teste = '''
    $x<int> = 10;
    $y<int> = 20;
    $z<int> = $x + $y * 2;
    
    if ($z > 30) {
        print("Z é maior que 30");
    } else {
        print("Z é menor ou igual a 30");
    }
    
    for ($i<int> = 0; $i < 5; $i += 1) {
        print($i);
    }
    '''
    
    tokens = analex.tokenize(codigo_teste)
    codigo = gerar_codigo_intermediario(tokens)
    codigo_formatado = formatar_codigo(codigo)
    
    print("\n" + "="*60)
    print("CÓDIGO INTERMEDIÁRIO DE 3 ENDEREÇOS")
    print("="*60)
    for linha in codigo_formatado:
        print(linha)
