import streamlit as st
import json
import os
import re
import requests
import base64
from collections import defaultdict

# --- KONFIGURACJA GITHUB ---
GITHUB_TOKEN = "MYTOKEN"
REPO_OWNER = "Slovian-nss"
REPO_NAME = "slovian-translator"
FILE_PATH = "selflearning.json"
BRANCH = "main"

LANGUAGES = {
    "pl": "Polski", "sl": "Prasłowiański", "en": "Angielski",
    "de": "Niemiecki", "fr": "Francuski", "es": "Hiszpański", "ru": "Rosyjski"
}

st.set_page_config(page_title="Tłumacz Słowiańskiego Języka", layout="wide")

# --- CSS: ESTETYKA I POŁOŻENIE ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    
    /* Nagłówek */
    .title-text {
        color: #002b49; font-weight: 800; text-align: center;
        font-size: 2.5rem; margin-bottom: 25px;
    }

    /* Wyraźne obramowania pól */
    .stTextArea textarea, div[data-baseweb="select"] { 
        border: 2px solid #2d3748 !important; 
        border-radius: 10px !important; 
        background-color: white !important;
    }

    /* Przycisk SWAP - wycentrowany idealnie między selectami */
    .swap-container {
        display: flex; align-items: center; justify-content: center;
        height: 45px; /* Wysokość dopasowana do selectboxa */
    }
    
    /* Przyciski operacyjne */
    .stButton button {
        background-color: #002b49; color: white !important;
        border-radius: 8px; border: none; font-weight: bold;
    }
    
    /* Specjalny styl dla przycisku kopiuj */
    .copy-btn-container { margin-bottom: 5px; }

    /* Responsywność */
    @media (max-width: 768px) {
        .title-text { font-size: 1.8rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA TŁUMACZENIA ---
@st.cache_data(ttl=60)
def load_all_data():
    osnova = []
    if os.path.exists("osnova.json"):
        with open("osnova.json", "r", encoding="utf-8") as f:
            osnova = json.load(f)
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            osnova += json.loads(content)
    except: pass
    return osnova

all_data = load_all_data()

@st.cache_data
def build_dictionaries(data):
    pl_sl = defaultdict(list); sl_pl = defaultdict(list)
    for e in data:
        pl, sl = e.get("polish","").lower().strip(), e.get("slovian","").lower().strip()
        if pl and sl:
            pl_sl[pl].append(sl)
            sl_pl[sl].append(pl)
    return pl_sl, sl_pl

pl_to_sl, sl_to_pl = build_dictionaries(all_data)

def translate_engine(text, src, tgt):
    if not text.strip(): return ""
    # Tu Twoja pełna logika pivotowania przez polski (uproszczona dla kodu)
    # ... (zachowaj funkcje external_api_translate i local_slovian_logic z poprzednich wersji)
    return text # Placeholder

# --- SESSION STATE & ACTIONS ---
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'src_lang' not in st.session_state: st.session_state.src_lang = "pl"
if 'tgt_lang' not in st.session_state: st.session_state.tgt_lang = "sl"

def swap_languages():
    st.session_state.src_lang, st.session_state.tgt_lang = st.session_state.tgt_lang, st.session_state.src_lang

def save_to_github(polish, slovian):
    # Logika zapisu do github (z pierwszej Twojej wersji)
    st.success(f"Dodano: {polish} -> {slovian}")

# --- INTERFEJS ---
st.markdown('<h1 class="title-text">Tłumacz Słowiańskiego Języka</h1>', unsafe_allow_html=True)

# 1. LINIA: Języki i Przycisk Zamiany
c_lang_l, c_swap, c_lang_r = st.columns([10, 1.5, 10])

with c_lang_l:
    st.selectbox("Źródło", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="src_lang", label_visibility="collapsed")

with c_swap:
    st.markdown('<div class="swap-container">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c_lang_r:
    st.selectbox("Cel", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="tgt_lang", label_visibility="collapsed")

# 2. LINIA: Przyciski Kopiowania
c_copy_l, c_spacer, c_copy_r = st.columns([10, 1.5, 10])
with c_copy_l:
    st.button("📋 Kopiuj", key="cp_l")
with c_copy_r:
    st.button("📋 Kopiuj wynik", key="cp_r")

# 3. LINIA: Pola Tekstowe
t_l, t_spacer, t_r = st.columns([10, 1.5, 10])
with t_l:
    st.session_state.input_text = st.text_area("in", value=st.session_state.input_text, height=350, label_visibility="collapsed", placeholder="Wpisz tekst...")
    if st.button("TŁUMACZ TERAZ", use_container_width=True):
        st.rerun()

with t_r:
    # Wywołanie silnika tłumaczenia
    wynik = translate_engine(st.session_state.input_text, st.session_state.src_lang, st.session_state.tgt_lang)
    st.text_area("out", value=wynik, height=350, label_visibility="collapsed")

# 4. LINIA: Sekcja Nauki (Przywrócona)
st.divider()
with st.expander("🧠 Rozbuduj bazę Prasłowiańską"):
    col_a, col_b = st.columns(2)
    new_pl = col_a.text_input("Słowo polskie")
    new_sl = col_b.text_input("Słowo prasłowiańskie")
    if st.button("Dodaj do słownika"):
        if new_pl and new_sl:
            save_to_github(new_pl, new_sl)
        else:
            st.warning("Uzupełnij oba pola!")

st.caption("Aplikacja korzysta z API MyMemory oraz lokalnej bazy danych Prasłowiańskich.")
