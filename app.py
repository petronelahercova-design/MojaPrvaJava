import streamlit as st
import datetime
import os
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
from dotenv import load_dotenv

# Načítanie API kľúča zo súboru .env
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializácia OpenAI klienta
client = OpenAI(api_key=API_KEY) if API_KEY else None

st.set_page_config(page_title="Biznis Zápisník", page_icon="📝", layout="centered")

st.title("📝 Môj Inteligentný Biznis Zápisník")
st.markdown("---")

def nacitat_poznamky():
    try:
        with open("moje_poznamky.txt", "r", encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        return []

def zapisat_vsetky_riadky(riadky):
    with open("moje_poznamky.txt", "w", encoding="utf-8") as f:
        f.writelines(riadky)

vsetky_riadky = nacitat_poznamky()

# ==========================================
# --- BOČNÝ PANEL S FILTRAMI ---
# ==========================================
st.sidebar.header("🔍 Filtrovanie úloh")
filter_priorita = st.sidebar.selectbox("Vyber prioritu:", ["Všetky", "🔴 Priorita 1", "🟡 Priorita 2", "🟢 Priorita 3"])

vsetky_kategorie = ["Všetky"]
kategorie_zo_suboru = []
for riadok in vsetky_riadky:
    if not riadok.strip() or "|" not in riadok: continue
    casti = riadok.split("|")
    if len(casti) > 1:
        kat = casti[1].strip()
        if kat and kat not in kategorie_zo_suboru: kategorie_zo_suboru.append(kat)

vsetky_kategorie += sorted(kategorie_zo_suboru)
filter_kategoria = st.sidebar.selectbox("Vyber kategóriu:", vsetky_kategorie)
filter_cas = st.sidebar.radio("Časový prehľad:", ["Všetko", "Len na dnes", "Tento týždeň"])

# ==========================================
# --- 🎙️ SEKČIA PRE HLASOVÉ OVLÁDANIE ---
# ==========================================
st.subheader("🎙️ Hlasový asistent AI")

if not client:
    st.warning("⚠️ V súbore `.env` chýba alebo je nesprávny OpenAI kľúč. Hlasové funkcie sú vypnuté.")
else:
    st.markdown("<small>Stlač tlačidlo, nadiktuj úlohu (napr. *'Priorita 1, kategória Dom, Opraviť dvere v drevenici do nedele'*) a zastav nahrávanie.</small>", unsafe_allow_html=True)
    
    # Skutočný mikrofónový rekordér
    nahravka = mic_recorder(
        start_prompt="🎤 Začať nahrávať hlas",
        stop_prompt="🛑 Zastaviť nahrávanie a spracovať cez AI",
        key="hlasovy_asistent",
        just_once=True
    )

    if nahravka:
        audio_bytes = nahravka['bytes']
        
        with st.spinner("🧠 AI premýšľa a prepisuje tvoj hlas..."):
            try:
                # 1. Uložíme dočasný súbor pre Whisper
                with open("docasna_nahravka.wav", "wb") as f:
                    f.write(audio_bytes)
                
                # 2. Whisper AI prepíše reč na text
                with open("docasna_nahravka.wav", "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file,
                        language="sk"
                    )
                
                hovoreny_text = transcription.text
                st.info(f"🗣️ **Nadiktované:** \"{hovoreny_text}\"")
                
                # 3. GPT-4o-mini spracuje text a zaradí ho do zápisníka
                dnesny_datum = datetime.date.today().strftime("%d.%m.%Y")
                
                prompt = f"""
                Z tohto textu: "{hovoreny_text}" vytiahni informácie pre úlohu v zápisníku.
                Dnešný dátum je {dnesny_datum}.
                Vráť výsledok striktne v tomto formáte (iba jeden riadok, nič iné nepíš):
                Priorita (iba číslo 1 alebo 2 alebo 3, ak sa nespomína, daj 3) | Kategória (jedno slovo, ak sa nespomína, daj Všeobecné) | Termín (vo formáte DD.MM.RRRR, ak sa nespomína, použi {dnesny_datum}) | Samotný text úlohy
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                ai_vysledok = response.choices[0].message.content.strip()
                
                # Bezpečné rozdelenie výsledku z AI
                if "|" in ai_vysledok:
                    casti_ai = ai_vysledok.split("|")
                    if len(casti_ai) >= 4:
                        prio_ai = casti_ai[0].strip()
                        kat_ai = casti_ai[1].strip()
                        dat_ai = casti_ai[2].strip()
                        text_ai = casti_ai[3].strip()
                        
                        novy_riadok_ai = f"[{prio_ai}] | {kat_ai} | {dat_ai} | {text_ai} | [ ]\n"
                        with open("moje_poznamky.txt", "a", encoding="utf-8") as f:
                            f.write(novy_riadok_ai)
                            
                        st.success(f"🎉 Úloha úspešne pridaná! **P{prio_ai}** | {kat_ai} | {dat_ai} | {text_ai}")
                        
                        if os.path.exists("docasna_nahravka.wav"):
                            os.remove("docasna_nahravka.wav")
                            
                        st.rerun()
                st.error("AI vrátila nekompatibilný formát, skús to znova prosím.")
                    
            except Exception as e:
                st.error(f"Chyba pri spracovaní cez AI: {e}")

st.markdown("---")

# ==========================================
# --- FORMULÁR PRE MANUÁLNU POZNÁMKU ---
# ==========================================
st.subheader("➕ Pridať novú úlohu ručne")

with st.form("nova_uloha_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        text_ulohy = st.text_input("Čo potrebuješ urobiť?", placeholder="Napr. Skontrolovať olej...")
    with col2:
        priorita = st.selectbox("Priorita", ["1", "2", "3"])
        
    col3, col4 = st.columns(2)
    with col3:
        kategoria = st.text_input("Kategória", placeholder="Projekt, Zdravie, Poplatky...")
    with col4:
        termin = st.date_input("Termín splnenia", datetime.date.today())
        
    tlacidlo = st.form_submit_button("Uložiť do systému")

    if tlacidlo and text_ulohy:
        novy_riadok = f"[{priorita}] | {kategoria if kategoria else 'Všeobecné'} | {termin.strftime('%d.%m.%Y')} | {text_ulohy} | [ ]\n"
        with open("moje_poznamky.txt", "a", encoding="utf-8") as f:
            f.write(novy_riadok)
        st.success("🎉 Úloha bola bezpečne zapísaná!")
        st.rerun()

st.markdown("---")

# ==========================================
# --- DYNAMICKÝ VIZUÁLNY SUMÁR ---
# ==========================================
st.subheader("🔥 Tvoj aktuálny prehľad úloh")
dnes = datetime.date.today()

if not vsetky_riadky:
    st.info("Zápisník je prázdny. Napíš niečo vyššie!")
else:
    aktivne_ulohy_objekty = []
    archiv_ulohy_objekty = []

    for index, riadok in enumerate(vsetky_riadky):
        if not riadok.strip() or "|" not in riadok: continue
        casti = riadok.split("|")
        
        # Bezpečnostná poistka pre staré/nekompatibilné riadky
        if len(casti) < 4: continue
            
        prio = casti[0].strip()
        kat = casti[1].strip()
        dat_txt = casti[2].strip()
        obsah = casti[3].strip()
        status = casti[4].strip() if len(casti) > 4 else "[ ]"
        
        try:
            term_date = datetime.datetime.strptime(dat_txt, "%d.%m.%Y").date()
        except: 
            continue

        Uloha_data = {
            "index": index, "prio": prio, "kat": kat, "dat_txt": dat_txt,
            "date": term_date, "obsah": obsah, "status": status, "povodny_riadok": riadok
        }

        if status == "[X]":
            archiv_ulohy_objekty.append(Uloha_data)
        else:
            if filter_priorita != "Všetky":
                if "Priorita 1" in filter_priorita and "[1]" not in prio: continue
                elif "Priorita 2" in filter_priorita and "[2]" not in prio: continue
                elif "Priorita 3" in filter_priorita and "[3]" not in prio: continue
                    
            if filter_kategoria != "Všetky" and kat != filter_kategoria: continue
                
            if filter_cas == "Len na dnes" and term_date != dnes: continue
            elif filter_cas == "Tento týždeň":
                if not (dnes <= term_date <= dnes + datetime.timedelta(days=7)): continue

            aktivne_ulohy_objekty.append(Uloha_data)

    typ_zobrazenia = st.segmented_control(
        "Zvoliť formát prehľadu:",
        options=["Zoznam pod sebou", "Tento rok po mesiacoch", "Tento mesiac po týždňoch"],
        default="Zoznam pod sebou"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    def vykresli_riadok_ulohy(uloha):
        varovanie = ""
        if uloha["date"] < dnes: varovanie = "⚠️ [PO TERMÍNE] "
        elif uloha["date"] == dnes: varovanie = "📅 [DNES] "
            
        col_text, col_btn = st.columns([5, 1])
        with col_text:
            if "[1]" in uloha["prio"]: st.error(f"🔴 **P1:** {varovanie}{uloha['obsah']} *(Do: {uloha['dat_txt']})* [{uloha['kat']}]")
            elif "[2]" in uloha["prio"]: st.warning(f"🟡 **P2:** {varovanie}{uloha['obsah']} *(Do: {uloha['dat_txt']})* [{uloha['kat']}]")
            else: st.success(f"🟢 **P3:** {varovanie}{uloha['obsah']} *(Do: {uloha['dat_txt']})* [{uloha['kat']}]")
                
        with col_btn:
            if st.button("✓ Splniť", key=f"btn_{uloha['index']}"):
                casti_riadku = uloha["povodny_riadok"].strip().split("|")
                if len(casti_riadku) == 4:
                    novy_riadok = f"{casti_riadku[0].strip()} | {casti_riadku[1].strip()} | {casti_riadku[2].strip()} | {casti_riadku[3].strip()} | [X]\n"
                else:
                    casti_riadku[4] = " [X]"
                    novy_riadok = " | ".join(casti_riadku) + "\n"
                
                vsetky_riadky[uloha["index"]] = novy_riadok
                zapisat_vsetky_riadky(vsetky_riadky)
                st.toast("Úloha presunutá do archívu! 🎉")
                st.rerun()

    if not aktivne_ulohy_objekty:
        st.info("Žiadne aktívne úlohy pre zvolené filtre. 👌")
    elif typ_zobrazenia == "Zoznam pod sebou":
        for u in aktivne_ulohy_objekty: vykresli_riadok_ulohy(u)
    elif typ_zobrazenia == "Tento rok po mesiacoch":
        mesiace_sk = {1: "Január", 2: "Február", 3: "Marec", 4: "Apríl", 5: "Máj", 6: "Jún", 
                      7: "Júl", 8: "August", 9: "September", 10: "Október", 11: "November", 12: "December"}
        for m_id in range(1, 13):
            ulohy_v_mesiaci = [u for u in aktivne_ulohy_objekty if u["date"].month == m_id and u["date"].year == dnes.year]
            if ulohy_v_mesiaci:
                with st.expander(f"📅 {mesiace_sk[m_id]} ({len(ulohy_v_mesiaci)} úloh)"):
                    for u in ulohy_v_mesiaci: vykresli_riadok_ulohy(u)
    elif typ_zobrazenia == "Tento mesiac po týždňoch":
        ulohy_tento_mesiac = [u for u in aktivne_ulohy_objekty if u["date"].month == dnes.month and u["date"].year == dnes.year]
        if not ulohy_tento_mesiac: st.info("Tento mesiac ťa nečakajú žiadne úlohy.")
        else:
            cisla_tyzdnov = sorted(list(set([u["date"].isocalendar()[1] for u in ulohy_tento_mesiac])))
            for t_id in cisla_tyzdnov:
                ulohy_v_tyzdni = [u for u in ulohy_tento_mesiac if u["date"].isocalendar()[1] == t_id]
                with st.expander(f"🗓️ {t_id}. týždeň v roku ({len(ulohy_v_tyzdni)} úloh)"):
                    for u in ulohy_v_tyzdni: vykresli_riadok_ulohy(u)

    st.markdown("---")
    with st.expander("📜 Archív splnených úloh (História)"):
        if not archiv_ulohy_objekty: st.caption("Zatiaľ tu nie sú žiadne splnené úlohy.")
        else:
            for u in reversed(archiv_ulohy_objekty): 
                obsah_archivu = u['obsah'] if 'obsah' in u else u['povodny_riadok'].strip()
                st.markdown(f"~~✅ **[{u.get('kat', 'Archív')}]** {obsah_archivu}~~ *(Termín: {u.get('dat_txt', 'Nevedno')})*")