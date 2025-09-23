from collections import defaultdict
import pandas as pd

grammar = {
    "Programa": [["ListaDados", "ListaComandos"]],
    "Tipo": [["Primitivos", "SufixoTipo"]],
    "Primitivos": [["int"], ["float"], ["string"], ["bool"]],
    "SufixoTipo": [["[", "]"], ["ε"]],
    "ListaDados": [["Dado", "ListaDados"], ["ε"]],
    "Dado": [["$id", "<", "Tipo", ">", "AtribuicaoVariavel", ";"]],
    "AtribuicaoVariavel": [["OPERADOR_ATRIB", "Expr"], ["ε"]],

    "ListaComandos": [["Comando", "ListaComandos"], ["ε"]],
    "Comando": [
        ["Atribuicao"],
        ["if", "(", "Expr", ")", "Comando", "RestoIf"],
        ["while", "(", "Expr", ")", "Comando"],
        ["for", "(", "ForInit", ";", "Expr", ";", "Atribuicao", ")"],
        ["{", "ListaComandos", "}"],
        ["read", "(", "id", ")", ";"],
        ["print", "(", "string", "PRINT_TAIL", ")", ";"]
    ],

    "PRINT_TAIL": [["+", "Factor", "PRINT_TAIL"], ["ε"]],
    "RestoIf": [["else", "Comando"], ["ε"]],
    "Atribuicao": [["$id", "OPERADOR_ATRIB", "Expr"]],
    "ForInit": [["Dado"], ["Atribuicao"]],

    "OPERADOR_LOGICO": [["!="], ["<"], [">"], ["=="], [">="], ["<="]],
    "OPERADOR_ATRIB": [["="], ["+="], ["-="], ["*="], ["/="], ["%="]],

    "Expr": [["ExpressaoAritmetica", "ExprR"]],
    "ExprR": [["OPERADOR_LOGICO", "ExpressaoAritmetica"], ["ExprPrime"]],
    "ExprPrime": [["AddOp", "Term", "ExprPrime"], ["ε"]],
    "AddOp": [["+"], ["-"]],

    "ExpressaoAritmetica": [["Term", "ExprPrime"]],
    "Term": [["Factor", "TermPrime"]],
    "TermPrime": [["MulOp", "Factor", "TermPrime"], ["ε"]],
    "MulOp": [["*"], ["/"], ["%"]],

    "Factor": [
        ["(", "Expr", ")"],
        ["$id"],
        ["num"],
        ["string"],
        ["bool"],
        ["AtrRead"],
        ["ArrayLiteral"],
        ["IndexAccess"]
    ],
    "bool": [["true"], ["false"]],
    "ArrayLiteral": [["{", "ListaExpr", "}"]],
    "IndexAccess": [["$id", "[", "Expr", "]"]],
    "ListaExpr": [["Expr", "ListaExprTail"], ["ε"]],
    "ListaExprTail": [[",", "Expr", "ListaExprTail"], ["ε"]],
    "AtrRead": [["read", "(", "string", ")"]],
    "int": [["[0-9]+"]],
    "float": [["[+-]?[0-9]+(\\.[0-9]+)?"]],
    "id": [["\\$?[a-zA-Z_][a-zA-Z0-9_]*"]],
    "string": [["\"([^\"\\n])*\""]],
    "Comentario": [['>>>[^\\n]*']]
}

non_terminals = list(grammar.keys())
terminals = set()
for prods in grammar.values():
    for prod in prods:
        for sym in prod:
            if sym not in grammar and sym != "ε":
                terminals.add(sym)

FIRST = defaultdict(set)
FOLLOW = defaultdict(set)

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

for nt in non_terminals:
    compute_first(nt)

compute_follow()

# print(f"{'Não-Terminal':<10} {'First':<20} {'Follow'}")
# for nt in non_terminals:
#     print(f"{nt:<10} {str(FIRST[nt]):<20} {str(FOLLOW[nt])}")

data = []
for nt in non_terminals:
    data.append([nt, ", ".join(sorted(FIRST[nt])), ", ".join(sorted(FOLLOW[nt]))])

df = pd.DataFrame(data, columns=["Não-Terminal", "FIRST", "FOLLOW"])
df.to_excel("first_follow_tabela.xlsx", index=False)

print("Tabela salva em 'first_follow_tabela.xlsx'")
