import streamlit as st
import datetime
import os
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
from dotenv import load_dotenv

# Načítanie API kľúča
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None

st.set_page_config(page_title="Biznis Zápisník", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stApp { background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png"); background-color: #f4f1ea; }
    </style>
""", unsafe_allow_html=True)

st.title("📝 Môj Inteligentný Biznis Zápisník")
st.markdown("---")

def nacitat_poznamky():
    try:
        with open("moje_poznamky.txt", "r", encoding="utf-8") as f: return f.readlines()
    except FileNotFoundError: return []

def zapisat_vsetky_riadky(riadky):
    with open("moje_poznamky.txt", "w", encoding="utf-8") as f: f.writelines(riadky)

vsetky_riadky = nacitat_poznamky()

# Bočný panel - len priority a kategórie
st.sidebar.header("🔍 Filtrovanie úloh")
filter_priorita = st.sidebar.selectbox("Vyber prioritu:", ["Všetky", "🔴 Priorita 1", "🟡 Priorita 2", "🟢 Priorita 3"])
kategorie = ["Všetky"] + sorted(list(set([r.split("|")[1].strip() for r in vsetky_riadky if "|" in r])))
filter_kategoria = st.sidebar.selectbox("Vyber kategóriu:", kategorie)

# Hlasový asistent
st.subheader("🎙️ Hlasový asistent AI")
if client:
    nahravka = mic_recorder(start_prompt="🎤 Začať", stop_prompt="🛑 Spracovať", key="voice", just_once=True)
    if nahravka:
        with open("temp.wav", "wb") as f: f.write(nahravka['bytes'])
        with open("temp.wav", "rb") as f:
            text = client.audio.transcriptions.create(model="whisper-1", file=f, language="sk").text
        dnes = datetime.date.today().strftime("%d.%m.%Y")
        prompt = f"Z textu '{text}' urob formát: Priorita(1-3)|Kategória|Termín(DD.MM.RRRR)|Úloha. Dnes: {dnes}."
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        with open("moje_poznamky.txt", "a", encoding="utf-8") as f: f.write(resp.choices[0].message.content.strip() + " | [ ] | 0\n")
        st.rerun()

# Manuálne zadávanie úloh
with st.form("nova_uloha", clear_on_submit=True):
    t = st.text_input("Čo urobiť?")
    c1, c2 = st.columns(2)
    p = c1.selectbox("Priorita", ["1", "2", "3"])
    d = c2.date_input("Termín")
    kat = st.text_input("Kategória")
    if st.form_submit_button("Uložiť"):
        with open("moje_poznamky.txt", "a", encoding="utf-8") as f: 
            f.write(f"[{p}] | {kat or 'Všeobecné'} | {d.strftime('%d.%m.%Y')} | {t} | [ ] | 0\n")
        st.rerun()

# Dashboard - Rozšírené filtre časového obdobia presne podľa teba
st.subheader("🔥 Tvoj aktuálny prehľad úloh")
f_cas = st.segmented_control(
    "Časové obdobie a formát:", 
    ["Všetko", "Len na dnes", "Tento týždeň", "Tento mesiac po týždňoch", "Tento rok po mesiacoch"], 
    default="Všetko"
)

zmena_vykonana = False
dnes = datetime.date.today()

# Názvy mesiacov pre pekné slovenské zobrazenie
mesiace_sk = {
    1: "Január", 2: "Február", 3: "Marec", 4: "Apríl", 5: "Máj", 6: "Jún",
    7: "Júl", 8: "August", 9: "September", 10: "Október", 11: "November", 12: "December"
}

# Zoznamy pre rozdelenie aktívnych a archivovaných úloh
aktivne_ulohy = []
archivovane_ulohy = []

for index, r in enumerate(vsetky_riadky):
    if "|" not in r: continue
    c = [x.strip() for x in r.split("|")]
    
    stav = c[4] if len(c) >= 5 else "[ ]"
    archivovany = c[5] if len(c) >= 6 else "0"
    
    if archivovany == "1":
        archivovane_ulohy.append((index, c, stav))
    else:
        aktivne_ulohy.append((index, c, stav))

# --- POMOCNÁ FUNKCIA NA VYKRESLENIE RIADKU ÚLOHY ---
def vykresli_riadok_ulohy(index, c, stav, zmena_vykonana_akcia):
    je_splnena = (stav == "[X]")
    priorita_ikona = "🔴" if "1" in c[0] else "🟡" if "2" in c[0] else "🟢"
    
    if je_splnena:
        label_text = f"~~{priorita_ikona} {c[3]} ({c[2]}) - {c[1]}~~"
    else:
        try:
            task_date = datetime.datetime.strptime(c[2], "%d.%m.%Y").date()
            varovanie = "⚠️ [PO TERMÍNE!] " if task_date < dnes else ""
        except:
            varovanie = ""
        label_text = f"{priorita_ikona} {varovanie}**{c[3]}** ({c[2]}) - *{c[1]}*"

    col_check, col_edit, col_arch = st.columns([0.75, 0.12, 0.12])
    
    with col_check:
        novy_st = st.checkbox(label_text, value=je_splnena, key=f"check_{index}")
        if novy_st != je_splnena:
            c5_val = '1' if len(c) >= 6 else '0'
            vsetky_riadky[index] = f"{c[0]} | {c[1]} | {c[2]} | {c[3]} | {'[X]' if novy_st else '[ ]'} | {c5_val}\n"
            zmena_vykonana_akcia = True

    with col_edit:
        if st.button("✏️", key=f"edit_btn_{index}"):
            st.session_state[f"editing_{index}"] = not st.session_state.get(f"editing_{index}", False)
            st.rerun()

    with col_arch:
        if st.button("📦", key=f"arch_btn_{index}"):
            vsetky_riadky[index] = f"{c[0]} | {c[1]} | {c[2]} | {c[3]} | {stav} | 1\n"
            zmena_vykonana_akcia = True

    if st.session_state.get(f"editing_{index}", False):
        novy_text = st.text_input("Uprav text a stlač Enter:", value=c[3], key=f"input_{index}")
        if novy_text != c[3]:
            c5_val = c[5] if len(c) >= 6 else '0'
            vsetky_riadky[index] = f"{c[0]} | {c[1]} | {c[2]} | {novy_text} | {stav} | {c5_val}\n"
            zapisat_vsetky_riadky(vsetky_riadky)
            st.session_state[f"editing_{index}"] = False
            st.rerun()
            
    return zmena_vykonana_akcia


# --- FILTROVANIE A TRIEDENIE AKTÍVNYCH ÚLOH ---
filtrovane_ulohy = []

for index, c, stav in aktivne_ulohy:
    try:
        datum = datetime.datetime.strptime(c[2], "%d.%m.%Y").date()
    except ValueError:
        continue
    
    # Aplikácia základných filtrov z bočného panela
    if filter_priorita != "Všetky":
        vybrate_cislo = filter_priorita.split()[-1]
        if vybrate_cislo not in c[0]: continue
    if filter_kategoria != "Všetky" and c[1] != filter_kategoria: continue
    
    # Aplikácia časových filtrov z dashboardu
    if f_cas == "Len na dnes" and datum != dnes: continue
    if f_cas == "Tento týždeň" and not (dnes <= datum <= dnes + datetime.timedelta(days=7)): continue
    if f_cas == "Tento mesiac po týždňoch" and not (datum.year == dnes.year and datum.month == dnes.month): continue
    if f_cas == "Tento rok po mesiacoch" and datum.year != dnes.year: continue
    
    filtrovane_ulohy.append((index, c, stav, datum))


# --- SAMOTNÉ ZOBRAZENIE PODĽA VYBRATÉHO FORMÁTU ---

if f_cas in ["Všetko", "Len na dnes", "Tento týždeň"]:
    # Klasické zobrazenie pod sebou bez špeciálneho delenia
    for index, c, stav, datum in filtrovane_ulohy:
        zmena_vykonana = vykresli_riadok_ulohy(index, c, stav, zmena_vykonana)

elif f_cas == "Tento mesiac po týždňoch":
    # Zoskupíme úlohy podľa kalendárneho týždňa
    tyzdne = {}
    for polozka in filtrovane_ulohy:
        # .isocalendar()[1] vráti číslo týždňa v roku
        cislo_tyzdna = polozka[3].isocalendar()[1]
        tyzdne.setdefault(cislo_tyzdna, []).append(polozka)
        
    for t_cislo in sorted(tyzdne.keys()):
        st.markdown(f"### 📅 {t_cislo}. Týždeň v roku")
        for index, c, stav, datum in tyzdne[t_cislo]:
            zmena_vykonana = vykresli_riadok_ulohy(index, c, stav, zmena_vykonana)

elif f_cas == "Tento rok po mesiacoch":
    # Zoskupíme úlohy podľa mesiacov
    mesiace = {}
    for polozka in filtrovane_ulohy:
        cislo_mesiaca = polozka[3].month
        mesiace.setdefault(cislo_mesiaca, []).append(polozka)
        
    for m_cislo in sorted(mesiace.keys()):
        nazov_mesiaca = mesiace_sk.get(m_cislo, f"{m_cislo}. Mesiac")
        st.markdown(f"### 🗓️ {nazov_mesiaca}")
        for index, c, stav, datum in mesiace[m_cislo]:
            zmena_vykonana = vykresli_riadok_ulohy(index, c, stav, zmena_vykonana)


# --- SEKCIA PRE ARCHÍV NA SPODKU STRÁNKY ---
st.markdown("---")
with st.expander("📦 Archivované úlohy (História)"):
    if not archivovane_ulohy:
        st.write("Archív je prázdny.")
    for index, c, stav in archivovane_ulohy:
        st.write(f"📁 ~~[{c[0]}] {c[3]} ({c[2]}) - {c[1]}~~")
        if st.button("⏪ Obnoviť z archívu", key=f"restore_{index}"):
            vsetky_riadky[index] = f"{c[0]} | {c[1]} | {c[2]} | {c[3]} | {stav} | 0\n"
            zmena_vykonana = True
            st.rerun()

if zmena_vykonana:
    zapisat_vsetky_riadky(vsetky_riadky)
    st.rerun()