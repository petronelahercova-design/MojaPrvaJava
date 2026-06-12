print("--- TVOJ RANNÝ INTELIGENTNÝ SUMÁR ---")

# 1. Otvoríme súbor a načítame z neho všetky riadky
with open("moje_poznamky.txt", "r", encoding="utf-8") as subbor:
    vsetky_riadky = subbor.readlines()

# Pripravíme si tri prázdne zoznamy (krabičky) na roztriedenie úloh
vysoka_priorita = []
stredna_priorita = []
nizka_priorita = []

# 2. Prejdeme riadok po riadku a roztriedime ich podľa toho, čo je na začiatku
for riadok in vsetky_riadky:
    if "[1]" in riadok:
        vysoka_priorita.append(riadok.strip())
    elif "[2]" in riadok:
        stredna_priorita.append(riadok.strip())
    elif "[3]" in riadok:
        nizka_priorita.append(riadok.strip())

# 3. VYPĽUTIE SUMÁRU NA OBRAZOVKU
print("\n🔥 TOTO SÚ TVOJE NAJDÔLEŽITEJŠIE ÚLOHY NA DNES (Priorita 1):")
for uloha in vysoka_priorita:
    print(f"  • {uloha.replace('[1] - ', '')}")

print("\n⚡ STREDNÁ PRIORITA (Priorita 2):")
for uloha in stredna_priorita:
    print(f"  • {uloha.replace('[2] - ', '')}")

print("\n☕ AK ZVÝŠI ČAS (Priorita 3):")
for uloha in nizka_priorita:
    print(f"  • {uloha.replace('[3] - ', '')}")