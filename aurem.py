import analex
from extrator_first_follow import PARSE_TABLE, terminals, non_terminals

# aurem_file_location = str(input("Type the aurem source code location: "))
aurem_file_location = "./primeiro.rem"
code = []

with open(aurem_file_location, "r", encoding="utf-8") as aurem_file:
    for line in aurem_file:
        code.append(line)

# Análise léxica
tokens = analex.tokenize("".join(code))

# for t in tokens:
#     print(t)

def normalize_tokens(tokens):
    out = []
    for kind, value, line in tokens:
        if kind == 'id':
            out.append('$id')
        elif kind == 'NUMERO':
            out.append('num')
        elif kind == 'STRING':
            out.append('string')
        elif kind == 'TRUE':
            out.append('true')
        elif kind == 'FALSE':
            out.append('false')
        elif kind == 'TIPO':                  # int|float|string|bool
            out.append(value)
        elif kind == 'VETOR':                 # '[]' vira '[' ']'
            out.extend(['[', ']'])
        elif kind == 'ELSEIF':                # seu léxico gera 'else if' junto
            out.extend(['else', 'if'])
        elif kind in ['FOR','IF','ELSE','WHILE','READ','PRINT']:
            out.append(value)
        elif kind in ['MENOR','MAIOR','ATRIBUICAO','PONTO_VIRGULA','VIRGULA',
                      'ABRE_PAREN','FECHA_PAREN','ABRE_COLCHETE','FECHA_COLCHETE',
                      'ABRE_CHAVE','FECHA_CHAVE']:
            out.append(value)
        elif kind == 'OP_REL':                # '==', '!=', '>=', '<=', '+=', '-=', '*=', '/='
            out.append(value)
        elif kind == 'OP_ARIT':               # '+', '-', '*', '/', '%'
            out.append(value)
        else:
            out.append(value)
    return out

def parse(tokens, parse_table, start_symbol="Programa"):
    stack = ["$", start_symbol]
    input_tokens = normalize_tokens(tokens)
    input_buffer = input_tokens + ["$"]
    pointer = 0
    derivation = []

    while stack:
        X = stack.pop()
        a = input_buffer[pointer]

        if X == "$":
            if a == "$":
                print("Sentença aceita!")
                return derivation
            else:
                print("Erro: entrada não consumida totalmente.")
                return None

        if X in terminals:
            if X == a:
                pointer += 1
            else:
                print(f"Erro: esperado '{X}', encontrado '{a}'")
                return None
        elif X in non_terminals:
            prod = parse_table[X].get(a)
            if prod:
                derivation.append(f"{X} → {' '.join(prod)}")
                for symbol in reversed(prod):
                    if symbol != "ε":
                        stack.append(symbol)
            else:
                print(f"Erro: não há produção para M[{X}, {a}]")
                return None
        else:
            print(f"Erro: símbolo desconhecido '{X}'")
            return None

    print("Erro: pilha esvaziou antes do fim da entrada.")
    return None

resultado = parse(tokens, PARSE_TABLE, "Programa")  # Símbolo inicial corrigido
if resultado:
    print("Derivação:")
    for passo in resultado:
        print(passo)
