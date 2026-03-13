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

st.set_page_config(page_title="Tłumacz Języka Słowiańskiego", layout="wide")

# --- CSS: PRECYZYJNE POZYCJONOWANIE ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    
    /* Nagłówek przesunięty do góry */
    .title-text {
        color: #002b49; 
        font-weight: 800; 
        text-align: center;
        font-size: 2.2rem; 
        margin-top: -20px; /* Przesunięcie o 20px do góry */
        margin-bottom: 30px;
    }

    /* Pola wyboru i tekstu */
    .stTextArea textarea, div[data-baseweb="select"] { 
        border: 2px solid #2d3748 !important; 
        border-radius: 10px !important; 
        background-color: white !important;
    }

    /* Wycentrowanie przycisku zamiany do wysokości Selectboxów */
    .swap-container {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 42px; /* Standardowa wysokość Selectboxa w Streamlit */
    }
    
    .stButton button {
        background-color: #002b49; 
        color: white !important;
        border-radius: 8px; 
        border: none; 
        font-weight: bold;
    }

    /* Stylizacja przycisków kopiowania */
    .copy-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #4a5568;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SILNIK TŁUMACZENIA ---
@st.cache_data(ttl=60)
def load_all_data():
    osnova = []
    # Pobieranie danych (Twój istniejący kod pobierania)
    return osnova

all_data = load_all_data()

def translate_engine(text, src, tgt):
    if not text.strip(): return ""
    # Tutaj Twoja logika (Pivot przez PL + API MyMemory)
    return text # Placeholder

# --- SESSION STATE ---
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'src_lang' not in st.session_state: st.session_state.src_lang = "pl"
if 'tgt_lang' not in st.session_state: st.session_state.tgt_lang = "sl"

def swap_languages():
    st.session_state.src_lang, st.session_state.tgt_lang = st.session_state.tgt_lang, st.session_state.src_lang

# --- UI APLIKACJI ---

# 1. Nowy Tytuł
st.markdown('<h1 class="title-text">Tłumacz Języka Słowiańskiego (Prasłowiańskiego)</h1>', unsafe_allow_html=True)

# 2. Wybór Języków z wyrównanym przyciskiem
col_l, col_s, col_r = st.columns([10, 1.2, 10])

with col_l:
    st.selectbox("Źródło", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="src_lang", label_visibility="collapsed")

with col_s:
    st.markdown('<div class="swap-container">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.selectbox("Cel", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="tgt_lang", label_visibility="collapsed")

st.write("") # Odstęp

# 3. Przyciski Kopiowania
cp_l, cp_mid, cp_r = st.columns([10, 1.2, 10])
with cp_l:
    st.button("📋 Kopiuj", key="copy_in")
with cp_r:
    st.button("📋 Kopiuj wynik", key="copy_out")

# 4. Pola Tekstowe i Przycisk Tłumaczenia
t_l, t_mid, t_r = st.columns([10, 1.2, 10])

with t_l:
    input_txt = st.text_area("in", value=st.session_state.input_text, height=350, label_visibility="collapsed", placeholder="Wpisz tekst do przetłumaczenia...")
    st.session_state.input_text = input_txt
    if st.button("TŁUMACZ TERAZ", use_container_width=True):
        st.rerun()

with t_r:
    wynik = translate_engine(st.session_state.input_text, st.session_state.src_lang, st.session_state.tgt_lang)
    st.text_area("out", value=wynik, height=350, label_visibility="collapsed")

# Sekcja nauki została usunięta zgodnie z poleceniem.
st.markdown("---")
st.caption("Interfejs zoptymalizowany pod kątem estetyki DeepL.")
