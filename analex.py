import re

tokens = [      
    ('NEWLINE', r'\n'),
    ('SKIP', r'[ \t]+'),
    ('COMENTARIO', r'>>>[^\n]*'),

    ('NUMERO',  r'[+-]?\d+(\.\d+)?'),
    ('NATURAL', r'\d+'),

    ('STRING', r'"[^"\n]*"'),

    ('TIPO', r'\b(float|int|string|bool)\b'),
    ('VETOR', r'\[\]'),
    ('BREAK', r'\bbreak\b'),
    ('CONTINUE', r'\bcontinue\b'),
    ('TRUE', r'\btrue\b'),
    ('FALSE', r'\bfalse\b'),
    ('FOR', r'\bfor\b'),
    ('IF', r'\bif\b'),
    ('ELSEIF', r'\belse\s+if\b'),
    ('ELSE', r'\belse\b'),
    ('WHILE', r'\bwhile\b'),
    ('READ', r'\bread\b'),
    ('PRINT', r'\bprint\b'),
    
    ('ID', r'\$[a-zA-Z_][a-zA-Z0-9_]*'),

    ('INCREMENTO', r'\+\+'),
    ('DECREMENTO', r'--'),
    ('IGUAL', r'=='),
    ('DIFERENTE', r'!='),
    ('MAIOR_IGUAL', r'>='),
    ('MENOR_IGUAL', r'<='),
    ('MAIS_IGUAL', r'\+='),
    ('MENOS_IGUAL', r'-='),
    ('MULT_IGUAL', r'\*='),
    ('DIV_IGUAL', r'/='),
    ('POT_IGUAL', r'\^='),
    ('AND_LOGICO', r'&&'),
    ('OR_LOGICO', r'\|\|'),
    ('MODULO', r'%'),
    ('POTENCIA', r'\^'),
    ('NOT', r'!'),
    ('MAIS', r'\+'),
    ('MENOS', r'-'),
    ('MULT', r'\*'),
    ('DIV', r'/'),
    
    # Operadores relacionais
    ('MENOR', r'<'),
    ('MAIOR', r'>'),
    
    # Símbolos especiais
    ('ATRIBUICAO', r'='),
    ('PONTO_VIRGULA', r';'),
    ('VIRGULA', r','),
    ('ABRE_PAREN', r'\('),
    ('FECHA_PAREN', r'\)'),
    ('ABRE_COLCHETE', r'\['),
    ('FECHA_COLCHETE', r'\]'),
    ('ABRE_CHAVE', r'\{'),
    ('FECHA_CHAVE', r'\}'),

    ('MISMATCH', r'.')
]

tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in tokens)

def tokenize(code):
    line_num = 1
    tokens = []
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NEWLINE':
            line_num += 1
        elif kind == 'SKIP' or kind == 'COMENTARIO': 
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Erro léxico na linha {line_num}: caractere inesperado {value!r}')
        else:
            tokens.append((kind, value, line_num))
    return tokens