import analex
from extrator_first_follow import PARSE_TABLE, terminals, FOLLOW
from anasem import analisar_semantica

# aurem_file_location = str(input("Type the aurem source code location: "))
code = []

aurem_file_location = "primeiro.rem"

with open(aurem_file_location, "r", encoding="utf-8") as aurem_file:
    for line in aurem_file:
        code.append(line)

# Análise léxica
print("\n" + "="*50)
print("ANÁLISE LÉXICA")
print("="*50)
tokens = analex.tokenize("".join(code))
print(f"✓ {len(tokens)} tokens identificados")


def normalize_tokens(tokens):
    out = []
    for kind, value, line in tokens:
        if kind == 'id':
            out.append(("$id", value, line))
        elif kind == 'NUMERO':
            out.append(("num", value, line))
        elif kind == 'STRING':
            out.append(("string", value, line))
        elif kind == 'TRUE':
            out.append(("true", value, line))
        elif kind == 'FALSE':
            out.append(("false", value, line))
        elif kind == 'TIPO':  # int|float|string|bool
            out.append((value, value, line))
        elif kind == 'VETOR':  # '[]' -> '[' ']'
            out.append(("[", "[", line))
            out.append(("]", "]", line))
        elif kind == 'ELSEIF':
            out.append(("else", "else", line))
            out.append(("if", "if", line))
        elif kind in ['FOR', 'IF', 'ELSE', 'WHILE', 'READ', 'PRINT']:
            out.append((value, value, line))
        elif kind in ['MENOR', 'MAIOR', 'ATRIBUICAO', 'PONTO_VIRGULA', 'VIRGULA',
                      'ABRE_PAREN', 'FECHA_PAREN', 'ABRE_COLCHETE', 'FECHA_COLCHETE',
                      'ABRE_CHAVE', 'FECHA_CHAVE']:
            out.append((value, value, line))
        elif kind in ['OP_REL', 'OP_ARIT']:  # '==', '+=', '*', '%', etc.
            out.append((value, value, line))
        else:
            out.append((value, value, line))
    return out


def parse(tokens, parse_table, start_symbol="Programa"):
    toks = normalize_tokens(tokens)
    toks.append(("$", "$", -1))

    stack = ["$", start_symbol]
    i = 0
    derivation = []
    errors = []

    def top():
        return stack[-1] if stack else None

    while stack:
        X = top()
        a_sym, a_lex, a_line = toks[i]

        if X == "$":
            if a_sym == "$":
                break
            else:
                errors.append(
                    f"Linha {a_line}: entrada não consumida a partir de '{a_lex}'")
                i += 1
                continue

        # caso terminal
        if X in terminals:
            if X == a_sym:
                stack.pop()
                i += 1
            else:
                errors.append(
                    f"Linha {a_line}: esperado '{X}', encontrado '{a_lex}' — inserindo '{X}'")
                stack.pop()  # insere o terminal faltante (recuperação por inserção)
            continue

        # caso não-terminal
        prod = parse_table[X].get(a_sym)
        if prod:
            stack.pop()
            derivation.append(f"{X} → {' '.join(prod)}")
            for s in reversed(prod):
                if s != "ε":
                    stack.append(s)
        else:
            # recuperação: modo pânico com FOLLOW(X)
            followX = FOLLOW[X] | {";", "}", "$"}
            if a_sym in followX:
                errors.append(
                    f"Linha {a_line}: sincronizando — descartando não-terminal {X}")
                stack.pop()  # descarta X
            else:
                errors.append(
                    f"Linha {a_line}: símbolo inesperado '{a_lex}', descartando token")
                i += 1

            # evita loop infinito
            if i >= len(toks):
                break

    if errors:
        print("Erros encontrados:")
        for e in errors:
            print("-", e)
    else:
        print("✓ Sentença aceita!")

    return derivation, errors


# Análise sintática
print("\n" + "="*50)
print("ANÁLISE SINTÁTICA")
print("="*50)
resultado, erros_sintaticos = parse(tokens, PARSE_TABLE, "Programa")

# Análise semântica
print("\n" + "="*50)
print("ANÁLISE SEMÂNTICA")
print("="*50)
erros_semanticos, avisos = analisar_semantica(tokens)

if erros_semanticos:
    print("Erros semânticos encontrados:")
    for erro in erros_semanticos:
        print(f"  ✗ {erro}")
else:
    print("✓ Nenhum erro semântico encontrado!")

if avisos:
    print("\nAvisos:")
    for aviso in avisos:
        print(f"  ⚠ {aviso}")

# Resumo final
print("\n" + "="*50)
print("RESUMO DA COMPILAÇÃO")
print("="*50)
total_erros = len(erros_sintaticos) + len(erros_semanticos)
if total_erros == 0:
    print("✓ Programa válido! Nenhum erro encontrado.")
else:
    print(f"✗ {total_erros} erro(s) encontrado(s):")
    print(f"  - Erros sintáticos: {len(erros_sintaticos)}")
    print(f"  - Erros semânticos: {len(erros_semanticos)}")

if resultado:
    print("\n" + "="*50)
    print("DERIVAÇÃO (primeiras 20 produções)")
    print("="*50)
    for passo in resultado[:20]:
        print(passo)
    if len(resultado) > 20:
        print(f"... e mais {len(resultado) - 20} produções")
