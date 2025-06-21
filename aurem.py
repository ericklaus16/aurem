import analex

aurem_file_location = str(input("Type the aurem source code location: "))

code = []
tokens = []


with open(aurem_file_location, "r", encoding="utf-8") as aurem_file:
    for line in aurem_file:
        code.append(line)

tokens = analex.tokenize("".join(code))

for t in tokens:
    print(t)
