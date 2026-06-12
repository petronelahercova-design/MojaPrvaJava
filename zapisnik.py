import datetime

print("--- MOJ INTELIGENTNÝ ZÁPISNÍK (ČASOVÉ UPOZORNENIA) ---")

while True:
    print("\n--- HLAVNÉ MENU ---")
    print("1. Pridať novú poznámku")
    print("2. Zobraziť prehľad/sumár úloh")
    print("3. Vymazať poznámku (Zadať číslo riadku)")
    print("4. Ukončiť program")
    
    volba = input("Vyber si moznosť (1-4): ")

    if volba == "1":
        poznamka = input("\nNadiktuj/napíš svoju poznámku: ")
        priorita = input("Zadaj prioritu úlohy (1 - Vysoká, 2 - Stredná, 3 - Nízka): ")
        kategoria = input("Zadaj kategóriu (napr. Auto, Dom, Praca): ")
        datum = input("Zadaj termín splnenia (formát D.M.RRRR, napr. 8.6.2026): ")

        riadok_na_zapis = f"[{priorita}] | {kategoria} | {datum} | {poznamka}\n"
        with open("moje_poznamky.txt", "a", encoding="utf-8") as subbor:
            subbor.write(riadok_na_zapis)
        print("✅ Poznámka bola úspešne zapísaná!")

    elif volba == "2":
        with open("moje_poznamky.txt", "r", encoding="utf-8") as subbor:
            vsetky_riadky = subbor.readlines()

        print("\n  --- AKO CHCEŠ PREHĽAD ZOBRAZIŤ? ---")
        print("  A. Kompletný ranný sumár podľa priority s kontrolou termínov")
        print("  B. Filtrovať len jednu konkrétnu kategóriu")
        pod_volba = input("  Vyber si možnosť (A/B): ").upper()

        if pod_volba == "A":
            vysoka_priorita = []
            stredna_priorita = []
            nizka_priorita = []
            
            # Zistíme si, aký je presne dnešný deň v reálnom svete
            dnes = datetime.date.today()

            for riadok in vsetky_riadky:
                if not riadok.strip() or "|" not in riadok:
                    continue
                
                casti = riadok.split("|")
                priorita = casti[0].strip()
                kategoria = casti[1].strip()
                datum_text = casti[2].strip()
                text_ulohy = casti[3].strip()
                
                # CHYTRÁ KONTROLA DÁTUMU
                varovanie = ""
                try:
                    # Prevedieme text (napr. "8.6.2026") na skutočný dátum, ktorý Python vie porovnať
                    termin_ulohy = datetime.datetime.strptime(datum_text, "%d.%m.%Y").date()
                    
                    # Ak je termín starší alebo rovný dnešku, zapneme alarm
                    if termin_ulohy <= dnes:
                        varovanie = "⚠️ [PO TERMÍNE!] "
                except ValueError:
                    # Ak zadáš dátum slovom (napr. "streda"), Python ho neporovná, tak len neoznámi varovanie
                    pass

                pekny_vypis = f"{varovanie}{text_ulohy} (Termín: {datum_text}) [{kategoria}]"
                
                if "[1]" in priorita:
                    vysoka_priorita.append(pekny_vypis)
                elif "[2]" in priorita:
                    stredna_priorita.append(pekny_vypis)
                elif "[3]" in priorita:
                    nizka_priorita.append(pekny_vypis)

            print(f"\n--- TVOJ INTELIGENTNÝ RANNÝ SUMÁR (Dnes je: {dnes.strftime('%d.%m.%Y')}) ---")
            print("\n🔥 NAJDÔLEŽITEJŠIE ÚLOHY (Priorita 1):")
            for uloha in vysoka_priorita: print(f"  • {uloha}")
            print("\n⚡ STREDNÁ PRIORITA (Priorita 2):")
            for uloha in stredna_priorita: print(f"  • {uloha}")
            print("\n☕ AK ZVÝŠI ČAS (Priorita 3):")
            for uloha in nizka_priorita: print(f"  • {uloha}")
            print("\n-------------------------------------")

        elif pod_volba == "B":
            hladana_kategoria = input("\n  Zadaj názov kategórie: ").strip()
            print(f"\n--- 🔍 ÚLOHY Z KATEGÓRIE: {hladana_kategoria} ---")
            najdene = False
            for riadok in vsetky_riadky:
                if "|" in riadok:
                    casti = riadok.split("|")
                    if casti[1].strip().lower() == hladana_kategoria.lower():
                        print(f"  • {casti[3].strip()} (Termín: {casti[2].strip()}) [Priorita: {casti[0].strip()}]")
                        najdene = True
            if not najdene: print("  V tejto kategórii nemáš žiadne úlohy.")
            print("-----------------------------------------")

    elif volba == "4":
        print("\nZápisník sa zatvára. Pekný deň!")
        break