import re

tokens = [                
    ('NUMBER',  r'[+-]?\d+(\.\d+)?'),
    ('NATURAL', r'\d+'),
    ('ID', r'\$[a-zA-Z_][a-zA-Z0-9_]*'),
    ('LT', r'<'),
    ('GT', r'>'),
    ('TYPES', r'\b(float|int|string|bool)\b'),
    ('OP', r'[=;+-*]'), 
    ('NEWLINE', r'\n'),
    ('COMMENT', r'>>>.*'),
    ('SKIP', r'[ \t]+'),
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
        elif kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Erro léxico na linha {line_num}: caractere inesperado {value!r}')
        else:
            tokens.append((kind, value, line_num))
    return tokens


code = '''
$idade<int> = 25;
$altura<float> = 1.75;
$nome<string> = "Eric";
$ativo<bool> = true;
$lista<int[]> = {1, 2, 3, 4, 5};

$entrada<int> = read(“Digite sua idade: ”);

$idade += 1;
$altura *= 1.01;

if($entrada == $idade) {
    print("Mesma idade!");
} else if($entrada > $idade) {
    print("Você é mais velho.");
} else {
    print("Você é mais novo.");
}

if($idade > 30) {
    print("Idade não é maior que 30.");
}

if (idade % 2 == 0){
    print("Idade par");
}

for ($i<int> = 0; $i < 5; $i += 1) {
    print("for: " + $lista[$i]);
}

$i<int> = 0;
while ($i < 3) {
    print("while: " + $i);
    $i += 1;
}

foreach ($item<tipo> in $lista) {
    print("foreach: " + $item);
}
'''

tokens = tokenize(code)
for t in tokens:
    print(t)