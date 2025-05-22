# aurem_file_location = str(input("Type the aurem source code location: "))


with open("teste.rem", "r", encoding="utf-8") as aurem_file:
    for line in aurem_file:
        print(line.strip()) 