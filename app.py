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
        with open("moje_poznamky.txt", "a", encoding="utf-8") as f: f.write(resp.choices[0].message.content.strip() + " | [ ]\n")
        st.rerun()

# Manuál
with st.form("nova_uloha", clear_on_submit=True):
    t = st.text_input("Čo urobiť?")
    c1, c2 = st.columns(2)
    p = c1.selectbox("Priorita", ["1", "2", "3"])
    d = c2.date_input("Termín")
    kat = st.text_input("Kategória")
    if st.form_submit_button("Uložiť"):
        with open("moje_poznamky.txt", "a", encoding="utf-8") as f: f.write(f"[{p}] | {kat or 'Všeobecné'} | {d.strftime('%d.%m.%Y')} | {t} | [ ]\n")
        st.rerun()

# Dashboard - Tu sú všetky filtre pokope
st.subheader("🔥 Tvoj aktuálny prehľad úloh")
f_cas = st.segmented_control("Časové obdobie:", ["Všetko", "Len na dnes", "Tento týždeň"], default="Všetko")
f_typ = st.segmented_control("Formát prehľadu:", ["Zoznam pod sebou", "Tento rok po mesiacoch", "Tento mesiac po týždňoch"], default="Zoznam pod sebou")

# Logika zobrazenia
dnes = datetime.date.today()
for r in vsetky_riadky:
    if "|" not in r: continue
    c = [x.strip() for x in r.split("|")]
    datum = datetime.datetime.strptime(c[2], "%d.%m.%Y").date()
    
    # Aplikácia filtrov
    if f_cas == "Len na dnes" and datum != dnes: continue
    if f_cas == "Tento týždeň" and not (dnes <= datum <= dnes + datetime.timedelta(days=7)): continue
    if filter_priorita != "Všetky" and f"[{c[0][1]}]" not in filter_priorita: continue
    if filter_kategoria != "Všetky" and c[1] != filter_kategoria: continue
    
    st.write(f"**{c[0]}** {c[3]} ({c[2]}) - {c[1]}")