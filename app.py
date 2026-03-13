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

st.set_page_config(page_title="Tłumacz Języka Słowiańskiego", layout="wide")

# --- CSS ---
st.markdown("""
<style>

.stApp{
background:#f0f2f5;
}

/* NAGŁÓWEK */
.title-text{
color:#002b49;
font-weight:800;
text-align:center;
font-size:2.2rem;
margin-top:-20px;
margin-bottom:25px;
}

/* SELECT */
div[data-baseweb="select"]{
border:2px solid #2d3748 !important;
border-radius:10px !important;
background:white !important;
}

/* TEXTAREA */
.stTextArea textarea{
border:2px solid #2d3748 !important;
border-radius:10px !important;
background:white !important;
}

/* PRZYCISK ZAMIANY */
.swap-btn{
margin-top:28px;
}

.swap-btn button{
height:42px !important;
width:100%;
font-size:18px;
}

/* PRZYCISKI */
.stButton button{
background:#002b49;
color:white !important;
border-radius:8px;
border:none;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)


# --- SILNIK TŁUMACZENIA ---
@st.cache_data(ttl=60)
def load_all_data():
    osnova = []
    return osnova

all_data = load_all_data()

def translate_engine(text, src, tgt):
    if not text.strip():
        return ""
    return text


# --- SESSION STATE ---
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

if "src_lang" not in st.session_state:
    st.session_state.src_lang = "pl"

if "tgt_lang" not in st.session_state:
    st.session_state.tgt_lang = "sl"


def swap_languages():
    st.session_state.src_lang, st.session_state.tgt_lang = \
        st.session_state.tgt_lang, st.session_state.src_lang


# --- TYTUŁ ---
st.markdown(
'<h1 class="title-text">Tłumacz Języka Słowiańskiego (Prasłowiańskiego)</h1>',
unsafe_allow_html=True
)


# --- WYBÓR JĘZYKA ---
col_l, col_s, col_r = st.columns([10,1.2,10])

with col_l:
    st.selectbox(
        "Źródło",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="src_lang"
    )

with col_s:
    st.markdown('<div class="swap-btn">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.selectbox(
        "Cel",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="tgt_lang"
    )


st.write("")


# --- PRZYCISKI KOPIOWANIA ---
cp_l, cp_mid, cp_r = st.columns([10,1.2,10])

with cp_l:
    st.button("📋 Kopiuj", key="copy_in")

with cp_r:
    st.button("📋 Kopiuj wynik", key="copy_out")


# --- POLA TEKSTOWE ---
t_l, t_mid, t_r = st.columns([10,1.2,10])

with t_l:
    input_txt = st.text_area(
        "in",
        value=st.session_state.input_text,
        height=350,
        placeholder="Wpisz tekst do przetłumaczenia..."
    )

    st.session_state.input_text = input_txt

    if st.button("TŁUMACZ TERAZ", use_container_width=True):
        st.rerun()

with t_r:
    wynik = translate_engine(
        st.session_state.input_text,
        st.session_state.src_lang,
        st.session_state.tgt_lang
    )

    st.text_area(
        "out",
        value=wynik,
        height=350
    )


st.markdown("---")
st.caption("Interfejs zoptymalizowany pod kątem estetyki DeepL.")
