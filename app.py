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
    "pl": "Polski",
    "sl": "Prasłowiański",
    "en": "Angielski",
    "de": "Niemiecki",
    "fr": "Francuski",
    "es": "Hiszpański",
    "ru": "Rosyjski"
}

st.set_page_config(page_title="Tłumacz Słowiańskiego Języka", layout="wide")

# --- ZAAWANSOWANY CSS (RESPONSYWNOŚĆ) ---
st.markdown("""
<style>
    /* Ogólne tło */
    .stApp { background-color: #f8f9fa; color: #1a1a1b; }
    
    /* Nagłówek */
    .main-title {
        color: #002b49;
        font-weight: 850;
        text-align: center;
        font-size: clamp(1.5rem, 5vw, 2.5rem);
        margin-bottom: 2rem;
    }

    /* Stylizacja pól i list */
    .stTextArea textarea, div[data-baseweb="select"] { 
        border: 2px solid #2d3748 !important; 
        border-radius: 8px !important; 
        background-color: white !important;
    }

    /* Kontener przycisku SWAP - responsywny */
    .swap-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        padding-top: 10px;
    }

    /* Przyciski Kopiuj - stylizacja */
    .btn-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        font-size: 0.9rem;
        font-weight: 600;
        color: #4a5568;
    }

    /* Przycisk Tłumacz na dole */
    .stButton > button {
        width: 100%;
        background-color: #002b49 !important;
        color: white !important;
        border-radius: 8px !important;
        height: 50px !important;
        font-size: 1.1rem !important;
        border: none !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover {
        background-color: #004a7c !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }

    /* Ukrycie brandingów Streamlit */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Responsywność dla urządzeń mobilnych */
    @media (max-width: 768px) {
        .swap-wrapper { transform: rotate(90deg); padding: 20px 0; }
        .stTextArea textarea { height: 200px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA TŁUMACZENIA (Pełna wersja) ---
@st.cache_data(ttl=60)
def load_all_data():
    data = []
    if os.path.exists("osnova.json"):
        try:
            with open("osnova.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except: pass
    return data

def translate_engine(text, src, tgt):
    if not text.strip(): return ""
    # MyMemory API dla języków nowożytnych
    if src != "sl" and tgt != "sl":
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair={src}|{tgt}"
        try:
            return requests.get(url, timeout=5).json()['responseData']['translatedText']
        except: return text
    
    # Placeholder dla Twojej logiki Prasłowiańskiej (Pivot PL)
    # Tutaj wstaw swoją funkcję 'local_slovian_logic' i 'master_translate'
    return f"[Wynik: {text}]" 

# --- SESSION STATE ---
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'src_lang' not in st.session_state: st.session_state.src_lang = "pl"
if 'tgt_lang' not in st.session_state: st.session_state.tgt_lang = "sl"

def swap_languages():
    old_src = st.session_state.src_lang
    st.session_state.src_lang = st.session_state.tgt_lang
    st.session_state.tgt_lang = old_src

# --- LAYOUT ---
st.markdown('<h1 class="main-title">Tłumacz Słowiańskiego Języka</h1>', unsafe_allow_html=True)

# 1. Wybór Języków
c_l, c_s, c_r = st.columns([10, 2, 10])
with c_l:
    st.selectbox("Z", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="src_lang", label_visibility="collapsed")
with c_s:
    st.markdown('<div class="swap-wrapper">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages)
    st.markdown('</div>', unsafe_allow_html=True)
with c_r:
    st.selectbox("Na", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="tgt_lang", label_visibility="collapsed")

st.write("") # Odstęp

# 2. Pola Tekstowe
t_l, t_s, t_r = st.columns([10, 1, 10])

with t_l:
    st.markdown('<div class="btn-header">TEKST ŹRÓDŁOWY <span style="cursor:pointer">📋</span></div>', unsafe_allow_html=True)
    st.session_state.input_text = st.text_area("in", value=st.session_state.input_text, height=300, label_visibility="collapsed", placeholder="Wpisz tekst...")
    if st.button("TŁUMACZ TERAZ"):
        st.rerun()

with t_r:
    st.markdown('<div class="btn-header">TŁUMACZENIE <span style="cursor:pointer">📋</span></div>', unsafe_allow_html=True)
    wynik = translate_engine(st.session_state.input_text, st.session_state.src_lang, st.session_state.tgt_lang)
    st.text_area("out", value=wynik, height=300, label_visibility="collapsed", disabled=False)

st.markdown("---")
st.caption("Aplikacja dostosowuje się do rozmiaru ekranu. Na urządzeniach mobilnych kolumny ułożą się pionowo.")
