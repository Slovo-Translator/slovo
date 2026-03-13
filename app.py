import streamlit as st

# --- KONFIGURACJA ---
LANGUAGES = {
    "pl": "Polski", "sl": "Prasłowiański", "en": "Angielski",
    "de": "Niemiecki", "fr": "Francuski", "es": "Hiszpański", "ru": "Rosyjski"
}

st.set_page_config(page_title="Tłumacz", layout="wide")

# --- CSS: ABSOLUTNE WYRÓWNANIE ---
st.markdown("""
<style>
    /* 1. Przesunięcie nagłówka mocno do góry */
    .title-text {
        color:#002b49;
        font-weight:800;
        text-align:center;
        font-size:2.2rem;
        margin-top: -60px !important; 
        margin-bottom: 30px !important;
    }

    /* 2. Usuwamy marginesy pod selectboxami i przyciskami, żeby rzędy były blisko siebie */
    .stSelectbox, .stButton, .stTextArea {
        margin-bottom: -15px !important;
    }

    /* 3. Wymuszamy, aby kolumny w rzędzie wyboru języka miały tę samą wysokość i wycentrowanie */
    [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    /* 4. Styl przycisków Kopiuj/Wklej - mniejsze i dopasowane */
    .stButton button {
        background:#002b49;
        color:white !important;
        border-radius:6px;
        height: 38px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        width: auto !important;
        min-width: 120px;
    }

    /* 5. Przycisk zamiany języków (strzałki) - wycentrowany */
    .swap-btn-style button {
        background: #002b49 !important;
        height: 40px !important;
        width: 45px !important;
        min-width: 45px !important;
        margin-top: 0px !important;
    }

    /* 6. Pola tekstowe */
    .stTextArea textarea {
        border:2px solid #2d3748 !important;
        border-radius:10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA ---
if "input_text" not in st.session_state: st.session_state.input_text = ""
if "src_lang" not in st.session_state: st.session_state.src_lang = "pl"
if "tgt_lang" not in st.session_state: st.session_state.tgt_lang = "sl"

def swap_languages():
    st.session_state.src_lang, st.session_state.tgt_lang = \
        st.session_state.tgt_lang, st.session_state.src_lang

# --- UI ---
st.markdown('<h1 class="title-text">Tłumacz Języka Słowiańskiego (Prasłowiańskiego)</h1>', unsafe_allow_html=True)

# RZĄD 1: Wybór języka i zamiana
col_l, col_s, col_r = st.columns([10, 1.5, 10])
with col_l:
    st.selectbox("src", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="src_lang", label_visibility="collapsed")
with col_s:
    st.markdown('<div class="swap-btn-style">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages)
    st.markdown('</div>', unsafe_allow_html=True)
with col_r:
    st.selectbox("tgt", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="tgt_lang", label_visibility="collapsed")

st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True) # Precyzyjny odstęp między rzędami

# RZĄD 2: Kopiuj / Wklej
btn_l, _, btn_r = st.columns([10, 1.5, 10])
with btn_l:
    st.button("📋 Wklej tekst")
with btn_r:
    st.button("📋 Kopiuj wynik")

# RZĄD 3: Pola tekstowe
t_l, _, t_r = st.columns([10, 1.5, 10])
with t_l:
    st.session_state.input_text = st.text_area("in", value=st.session_state.input_text, height=300, label_visibility="collapsed", placeholder="Wpisz tekst...")
with t_r:
    # Tu podepnij swoje tłumaczenie
    wynik = f"Przetłumaczono na {st.session_state.tgt_lang}: {st.session_state.input_text}" if st.session_state.input_text else ""
    st.text_area("out", value=wynik, height=300, label_visibility="collapsed")
