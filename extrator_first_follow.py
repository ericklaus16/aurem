from collections import defaultdict
import pandas as pd

grammar = {
    "Programa": [["ListaComandos"]],
    "ListaComandos": [["Comando", "ListaComandos"], ["ε"]],

    "Comando": [["IfCommand"], ["Other"]],

    # If com else opcional
    "IfCommand": [["if", "(", "Expr", ")", "Comando", "RestoIf"]],
    "RestoIf": [["else", "Comando"], ["ε"]],

    "Other": [
        ["$id", "SufixoId"],
        ["WhileCommand"],
        ["ForCommand"],
        ["BlockCommand"],
        ["ReadCommand"],
        ["PrintCommand"]
    ],

    "SufixoId": [
        ["<", "Tipo", ">", "AtribuicaoVariavel", ";"],
        ["OPERADOR_ATRIB", "Expr", ";"]
    ],

    "Tipo": [["Primitivos", "SufixoTipo"]],
    "Primitivos": [["int"], ["float"], ["string"], ["bool"]],
    "SufixoTipo": [["[", "]"], ["ε"]],
    "AtribuicaoVariavel": [["OPERADOR_ATRIB", "Expr"], ["ε"]],

    "WhileCommand": [["while", "(", "Expr", ")", "Comando"]],
    "ForCommand": [["for", "(", "ForInit", ";", "Expr", ";", "Atribuicao", ")"]],
    "BlockCommand": [["{", "ListaComandos", "}"]],
    "ReadCommand": [["read", "(", "$id", ")", ";"]],
    "PrintCommand": [["print", "(", "string", "PRINT_TAIL", ")", ";"]],
    "Atribuicao": [["$id", "OPERADOR_ATRIB", "Expr"]],

    "ForInit": [["$id", "ForInitAfter"]],
    "ForInitAfter": [["<", "Tipo", ">", "AtribuicaoVariavel"], ["OPERADOR_ATRIB", "Expr"]],
    "PRINT_TAIL": [["+", "Factor", "PRINT_TAIL"], ["ε"]],

    "OPERADOR_LOGICO": [["!="], ["<"], [">"], ["=="], [">="], ["<="]],
    "OPERADOR_ATRIB": [["="], ["+="], ["-="], ["*="], ["/="], ["%="]],

    "Expr": [["ExpressaoAritmetica", "ExprLogicTail"]],
    "ExprLogicTail": [["OPERADOR_LOGICO", "ExpressaoAritmetica"], ["ε"]],

    "ExpressaoAritmetica": [["Term", "ExprPrime"]],
    "ExprPrime": [["AddOp", "Term", "ExprPrime"], ["ε"]],
    "AddOp": [["+"], ["-"]],

    "Term": [["Factor", "TermPrime"]],
    "TermPrime": [["MulOp", "Factor", "TermPrime"], ["ε"]],
    "MulOp": [["*"], ["/"], ["%"]],

    "Factor": [
        ["(", "Expr", ")"],
        ["$id", "FactorPrime"],
        ["num"],
        ["string"],
        ["BoolLiteral"],
        ["AtrRead"],
        ["ArrayLiteral"]
    ],
    "FactorPrime": [["[", "Expr", "]"], ["ε"]],
    "BoolLiteral": [["true"], ["false"]],
    "ArrayLiteral": [["{", "ListaExpr", "}"]],
    "ListaExpr": [["Expr", "ListaExprTail"], ["ε"]],
    "ListaExprTail": [[",", "Expr", "ListaExprTail"], ["ε"]],
    "AtrRead": [["read", "(", "string", ")"]],
}

non_terminals = list(grammar.keys())
terminals = set()
for prods in grammar.values():
    for prod in prods:
        for sym in prod:
            if sym not in grammar and sym != "ε":
                terminals.add(sym)

terminals.update(['=', '+=', '-=', '*=', '/=', '%=', '!=', '<', '>', '==', '>=', '<=', '+', '-', '*', '/', '%'])

FIRST = defaultdict(set)
FOLLOW = defaultdict(set)
PARSE_TABLE = defaultdict(dict)
CONFLICTS = []

def _add_entry(A, t, prod):
    if t in PARSE_TABLE[A] and PARSE_TABLE[A][t] != prod:
        CONFLICTS.append((A, t, " ".join(PARSE_TABLE[A][t]), " ".join(prod)))
        return
    PARSE_TABLE[A][t] = prod

def compute_first(symbol):
    if symbol in terminals:
        return {symbol}
    if symbol == "ε":
        return {"ε"}
    if symbol in FIRST and FIRST[symbol]:
        return FIRST[symbol]

    result = set()
    for prod in grammar[symbol]:
        for sym in prod:
            sym_first = compute_first(sym)
            result |= (sym_first - {"ε"})
            if "ε" not in sym_first:
                break
        else:
            result.add("ε")
    FIRST[symbol] = result
    return result

def compute_follow():
    FOLLOW["Programa"].add("$")  
    updated = True
    while updated:
        updated = False
        for A in grammar:
            for prod in grammar[A]:
                for i, B in enumerate(prod):
                    if B in non_terminals:
                        # Símbolos depois de B
                        beta = prod[i+1:]
                        if beta:
                            first_beta = set()
                            for sym in beta:
                                sym_first = compute_first(sym)
                                first_beta |= (sym_first - {"ε"})
                                if "ε" in sym_first:
                                    continue
                                else:
                                    break
                            else:
                                if not FOLLOW[B] >= FOLLOW[A]:
                                    FOLLOW[B] |= FOLLOW[A]
                                    updated = True
                            if not first_beta <= FOLLOW[B]:
                                FOLLOW[B] |= first_beta
                                updated = True
                        else:
                            if not FOLLOW[A] <= FOLLOW[B]:
                                FOLLOW[B] |= FOLLOW[A]
                                updated = True

def compute_parse_table():
    for A in grammar:
        for prod in grammar[A]:
            # Regra 1: Para cada terminal x em FIRST(α)
            first_alpha = set()
            for sym in prod:
                sym_first = compute_first(sym)
                first_alpha |= (sym_first - {"ε"})
                if "ε" not in sym_first:
                    break
            else:
                first_alpha.add("ε")
            for terminal in first_alpha:
                if terminal != "ε":
                    _add_entry(A, terminal, prod)
            # Regra 2: Se ε ∈ FIRST(α), para cada b em FOLLOW(A)
            if "ε" in first_alpha:
                for b in FOLLOW[A]:
                    if b not in PARSE_TABLE[A]:       
                        PARSE_TABLE[A][b] = prod

for nt in non_terminals:
    compute_first(nt)

compute_follow()
compute_parse_table()

# print(f"{'Não-Terminal':<10} {'First':<20} {'Follow'}")
# for nt in non_terminals:
#     print(f"{nt:<10} {str(FIRST[nt]):<20} {str(FOLLOW[nt])}")

data = []
for nt in non_terminals:
    data.append([nt, ", ".join(sorted(FIRST[nt])), ", ".join(sorted(FOLLOW[nt]))])

with pd.ExcelWriter("tabela_completa.xlsx") as writer:
    # Aba FIRST/FOLLOW
    df = pd.DataFrame(
        [[nt, ", ".join(sorted(FIRST[nt])), ", ".join(sorted(FOLLOW[nt]))] for nt in non_terminals],
        columns=["Não-Terminal", "FIRST", "FOLLOW"]
    )
    df.to_excel(writer, sheet_name="FIRST_FOLLOW", index=False)

    # Aba Tabela Sintática Preditiva (matriz)
    all_terminals = sorted(terminals | {"$"})
    matrix = []
    for nt in non_terminals:
        row = []
        for t in all_terminals:
            prod = PARSE_TABLE[nt].get(t)
            if prod:
                row.append(" ".join(prod))
            else:
                row.append("")
        matrix.append(row)
    df_matrix = pd.DataFrame(matrix, columns=all_terminals, index=non_terminals)
    df_matrix.index.name = "Não-Terminal"
    df_matrix.to_excel(writer, sheet_name="PARSE_TABLE", index=True)

print("Tudo salvo em 'tabela_completa.xlsx'")

if CONFLICTS:
    print("Aviso: conflitos LL(1) detectados (mantida a 1ª produção):")
    for A, t, p1, p2 in CONFLICTS:
        print(f"M[{A}, {t}] já tinha '{p1}', ignorando '{p2}'")