import streamlit as st
import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
from dotenv import load_dotenv

# ----------------------------
# KONFIGURÁCIA
# ----------------------------
st.set_page_config(page_title="Biznis Zápisník", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stApp { background-image: url("https://www.transparenttextures.com/patterns/cream-paper.png"); background-color: #f4f1ea; }
    </style>
""", unsafe_allow_html=True)

st.title("📝 Môj Inteligentný Biznis Zápisník")
st.markdown("---")

# ----------------------------
# OPENAI KĽÚČ
# ----------------------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None

# ----------------------------
# GOOGLE SHEETS
# ----------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
SHEET_NAME = "Hárok1"

def get_gsheet_client():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

gs_client = get_gsheet_client()
spreadsheet = gs_client.open_by_key(SPREADSHEET_ID)
worksheet = spreadsheet.worksheet(SHEET_NAME)

HEADERS = ["text", "priorita", "termín", "kategória", "stav", "archív"]

def ensure_headers():
    values = worksheet.get_all_values()
    if not values:
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
    elif values[0] != HEADERS:
        # ak je sheet prázdny alebo iný formát, ponecháme existujúce dáta bez prepisu
        pass

ensure_headers()

def nacitat_poznamky():
    try:
        values = worksheet.get_all_values()
        if not values:
            return []
        if values[0] == HEADERS:
            values = values[1:]
        rows = []
        for r in values:
            if len(r) < 6:
                r = r + [""] * (6 - len(r))
            rows.append(r[:6])
        return rows
    except Exception as e:
        st.error(f"Chyba pri načítaní z Google Sheets: {e}")
        return []

def zapisat_riadok(row):
    try:
        if len(row) < 6:
            row = row + [""] * (6 - len(row))
        worksheet.append_row(row[:6], value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Chyba pri zápise do Google Sheets: {e}")
        return False

def prepisat_vsetko(rows):
    try:
        worksheet.clear()
        worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
        for r in rows:
            if len(r) < 6:
                r = r + [""] * (6 - len(r))
            worksheet.append_row(r[:6], value_input_option="USER_ENTERED")
    except Exception as e:
        st.error(f"Chyba pri prepisovaní Google Sheets: {e}")

# ----------------------------
# NAČÍTANIE DÁT
# ----------------------------
vsetky_riadky = nacitat_poznamky()

# ----------------------------
# BOČNÝ PANEL
# ----------------------------
st.sidebar.header("🔍 Filtrovanie úloh")

def get_priorita_display(value):
    if value == "1":
        return "🔴 Priorita 1"
    if value == "2":
        return "🟡 Priorita 2"
    if value == "3":
        return "🟢 Priorita 3"
    return value

kategorie_set = sorted(list(set([r[3] for r in vsetky_riadky if len(r) > 3 and r[3]])))
kategorie = ["Všetky"] + kategorie_set

filter_priorita = st.sidebar.selectbox("Vyber prioritu:", ["Všetky", "🔴 Priorita 1", "🟡 Priorita 2", "🟢 Priorita 3"])
filter_kategoria = st.sidebar.selectbox("Vyber kategóriu:", kategorie)

# ----------------------------
# HLASOVÝ ASISTENT
# ----------------------------
st.subheader("🎙️ Hlasový asistent AI")

if client:
    nahravka = mic_recorder(start_prompt="🎤 Začať", stop_prompt="🛑 Spracovať", key="voice", just_once=True)
    if nahravka:
        temp_file = "temp.wav"
        with open(temp_file, "wb") as f:
            f.write(nahravka["bytes"])

        with open(temp_file, "rb") as f:
            text = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="sk"
            ).text

        dnes = datetime.date.today().strftime("%d.%m.%Y")
        prompt = (
            f"Z tejto poznámky vytvor jednu úlohu v presnom formáte: "
            f"text|priorita|termín|kategória. "
            f"Text: {text}. Dnešný dátum: {dnes}. "
            f"Ak chýba priorita, použi 2. Ak chýba termín, použi dnešný dátum. "
            f"Ak chýba kategória, použi Všeobecné."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        obsah = resp.choices[0].message.content.strip()
        casti = [x.strip() for x in obsah.split("|")]

        if len(casti) < 4:
            text_ulohy = obsah
            priorita = "2"
            termin = dnes
            kategoria = "Všeobecné"
        else:
            text_ulohy = casti[0]
            priorita = casti[1].replace("Priorita", "").strip()
            termin = casti[2]
            kategoria = casti[3]

        zapisat_riadok([text_ulohy, priorita, termin, kategoria, "[ ]", "0"])
        st.rerun()

# ----------------------------
# MANUÁLNE ZADÁVANIE
# ----------------------------
with st.form("nova_uloha", clear_on_submit=True):
    t = st.text_input("Čo urobiť?")
    c1, c2 = st.columns(2)
    p = c1.selectbox("Priorita", ["1", "2", "3"])
    d = c2.date_input("Termín")
    kat = st.text_input("Kategória")

    if st.form_submit_button("Uložiť"):
        zapisat_riadok([t, p, d.strftime("%d.%m.%Y"), kat or "Všeobecné", "[ ]", "0"])
        st.rerun()

# ----------------------------
# DASHBOARD
# ----------------------------
st.subheader("🔥 Tvoj aktuálny prehľad úloh")

f_cas = st.segmented_control(
    "Časové obdobie a formát:",
    ["Všetko", "Len na dnes", "Tento týždeň", "Tento mesiac po týždňoch", "Tento rok po mesiacoch"],
    default="Všetko"
)

dnes = datetime.date.today()

mesiace_sk = {
    1: "Január", 2: "Február", 3: "Marec", 4: "Apríl", 5: "Máj", 6: "Jún",
    7: "Júl", 8: "August", 9: "September", 10: "Október", 11: "November", 12: "December"
}

aktivne_ulohy = []
archivovane_ulohy = []

for index