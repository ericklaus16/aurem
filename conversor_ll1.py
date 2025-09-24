from copy import deepcopy
from collections import OrderedDict

def remove_left_recursion(grammar):
    """
    Remove recursão à esquerda direta.
    Retorna nova gramática sem recursão à esquerda.
    """
    new_grammar = {}
    
    for nt, prods in grammar.items():
        left_recursive = []
        non_recursive = []
        
        for prod in prods:
            if prod and prod[0] == nt:
                left_recursive.append(prod[1:])
            else:
                non_recursive.append(prod)
        
        if left_recursive:
            nt_prime = nt + "_prime"
            new_grammar[nt] = []
            
            for prod in non_recursive:
                new_grammar[nt].append(prod + [nt_prime])
            
            new_grammar[nt_prime] = []
            for prod in left_recursive:
                new_grammar[nt_prime].append(prod + [nt_prime])
            new_grammar[nt_prime].append(["ε"])
        else:
            new_grammar[nt] = prods
    
    return new_grammar


def left_factoring(grammar):
    """
    Left factoring com expansão do prefixo:
    - Expande cadeias unitárias iniciais (A -> α, onde α é única) para comparar prefixos reais.
    - Se encontrar prefixo comum, cria nt' e coloca os sufixos em nt'.
    - Trata padrão 'id(... )' como ['id', '(...)'].
    """
    def longest_common_prefix(seqs):
        if not seqs:
            return []
        prefix = list(seqs[0])
        for seq in seqs[1:]:
            i = 0
            while i < len(prefix) and i < len(seq) and prefix[i] == seq[i]:
                i += 1
            prefix = prefix[:i]
            if not prefix:
                break
        return prefix

    def split_id_call(symbol):
        # Converte "id(exp-list)" -> ["id", "(exp-list)"]
        if isinstance(symbol, str) and symbol.startswith("id(") and symbol.endswith(")"):
            return ["id", symbol[2:]]  # symbol[2:] == "(exp-list)" no exemplo
        return [symbol]

    def expand_front(prod):
        """
        Expande o início da produção substituindo não-terminais unitários por sua única produção.
        Apenas no front (enquanto o primeiro símbolo for um NT com 1 produção não-ε).
        """
        out = list(prod)
        while out and out[0] in grammar and len(grammar[out[0]]) == 1:
            only = grammar[out[0]][0]
            if only == ["ε"]:
                break
            out = only + out[1:]
        # Também normaliza um possível 'id(...)' no início
        if out:
            head = split_id_call(out[0])
            out = head + out[1:]
        return out

    new_grammar = OrderedDict()

    for nt, prods in grammar.items():
        # Mapeia produção original -> produção expandida para o front
        expanded = [(prod, expand_front(prod)) for prod in prods]

        # Agrupa por primeiro símbolo expandido
        groups = OrderedDict()
        for orig, exp in expanded:
            key = exp[0] if exp else "ε"
            if key not in groups:
                groups[key] = []
            groups[key].append((orig, exp))

        new_prods_nt = []
        used_prime_names = set(list(grammar.keys()) + list(new_grammar.keys()))

        def fresh_prime_name(base):
            cand = base + "'"
            i = 1
            while cand in used_prime_names or cand in new_grammar:
                i += 1
                cand = f"{base}'{i}"
            used_prime_names.add(cand)
            return cand

        for key, group in groups.items():
            if len(group) > 1:
                seqs = [exp for _, exp in group]
                prefix = longest_common_prefix(seqs)
                if prefix:
                    nt_prime = fresh_prime_name(nt)
                    new_prods_nt.append(prefix + [nt_prime])

                    prods_prime = []
                    for _, exp in group:
                        suffix = exp[len(prefix):]
                        prods_prime.append(suffix or ["ε"])
                    new_grammar[nt_prime] = prods_prime  # nt' vem logo após nt
                    continue
            for _, exp in group:
                new_prods_nt.append(exp or ["ε"])

        new_grammar[nt] = new_prods_nt

    return new_grammar

def prune_unreachable(grammar, start_symbol):
    reachable = set()
    work = [start_symbol]
    while work:
        A = work.pop()
        if A in reachable or A not in grammar:
            continue
        reachable.add(A)
        for prods in grammar.get(A, []):
            for s in prods:
                if s in grammar and s not in reachable:
                    work.append(s)
    # Reconstroi seguindo a ordem do grammar original
    pruned = OrderedDict()
    for A in grammar.keys():
        if A in reachable:
            pruned[A] = grammar[A]
    return pruned

def convert_to_LL1(grammar, start_symbol=None):
    if start_symbol is None:
        start_symbol = next(iter(grammar.keys()))
    grammar_no_left = remove_left_recursion(grammar)    
    grammar_factored = left_factoring(grammar_no_left)  
    grammar_pruned = prune_unreachable(grammar_factored, start_symbol)
    return grammar_pruned


# Exemplo pedido
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

grammar_ll1 = convert_to_LL1(grammar)

if __name__ == "__main__":
    import pprint
    pprint.pprint(grammar_ll1)