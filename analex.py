import re

tokens = [      
    ('NEWLINE', r'\n'),
    ('SKIP', r'[ \t]+'),
    ('COMENTARIO', r'>>>[^\n]*'),

    ('NUMERO',  r'[+-]?\d+(\.\d+)'),
    ('NATURAL', r'\d+'),

    ('STRING', r'"[^"\n]*"'),

    ('TIPO', r'\b(float|int|string|bool)\b'),
    ('BREAK', r'\bbreak\b'),
    ('CONTINUE', r'\bcontinue\b'),
    ('TRUE', r'\btrue\b'),
    ('FALSE', r'\bfalse\b'),
    ('RETURN', r'\breturn\b'),
    ('FOR', r'\bfor\b'),
    ('IF', r'\bif\b'),
    ('ELSEIF', r'\belse if\b'),
    ('ELSE', r'\belse\b'),
    ('WHILE', r'\bwhile\b'),
    ('READ', r'\bread\b'),
    ('PRINT', r'\bprint\b'),
    
    ('ID', r'\$[a-zA-Z_][a-zA-Z0-9_]*'),

    ('ARIT_OP', r'\+\+|--|==|!=|>=|<=|\+=|-=|\*=|/=|\^=|%|&&|\|\||\+|-|\*|/|!'),
    ('LT', r'<'),
    ('GT', r'>'),

    ('OP', r'[=;,\[\]\{\}\(\)]'),

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
        elif kind == 'SKIP': # or kind == 'COMMENT'
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Erro léxico na linha {line_num}: caractere inesperado {value!r}')
        else:
            tokens.append((kind, value, line_num))
    return tokens