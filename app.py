import streamlit as st

# --- KONFIGURACJA ---
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

# --- CSS DLA IDEALNEGO WYRÓWNANIA ---
st.markdown("""
<style>
    .stApp { background:#f0f2f5; }
    
    /* Przesunięcie nagłówka o 20px wyżej niż wcześniej */
    .title-text {
        color:#002b49;
        font-weight:800;
        text-align:center;
        font-size:2.2rem;
        margin-top:-40px; 
        margin-bottom:25px;
    }

    /* Wyrównanie pionowe rzędu wyboru języka */
    [data-testid="column"] {
        display: flex;
        align-items: flex-end;
    }

    /* Stylizacja pól i przycisków */
    div[data-baseweb="select"], .stTextArea textarea {
        border:2px solid #2d3748 !important;
        border-radius:10px !important;
        background:white !important;
    }

    .stButton button {
        background:#002b49;
        color:white !important;
        border-radius:8px;
        font-weight:bold;
        height: 45px; /* Stała wysokość dla wyrównania */
        width: 100%;
    }
    
    /* Specyficzny styl dla przycisku zamiany języków */
    .swap-container button {
        font-size: 20px !important;
        border: 2px solid #002b49 !important;
    }

</style>
""", unsafe_allow_html=True)

# --- FUNKCJE ---
def translate_engine(text, src, tgt):
    if not text.strip(): return ""
    return f"Tłumaczenie: {text}" # Tu wstaw logikę API

if "input_text" not in st.session_state: st.session_state.input_text = ""
if "src_lang" not in st.session_state: st.session_state.src_lang = "pl"
if "tgt_lang" not in st.session_state: st.session_state.tgt_lang = "sl"

def swap_languages():
    st.session_state.src_lang, st.session_state.tgt_lang = \
        st.session_state.tgt_lang, st.session_state.src_lang

# --- UI ---
st.markdown('<h1 class="title-text">Tłumacz Języka Słowiańskiego (Prasłowiańskiego)</h1>', unsafe_allow_html=True)

# RZĄD 1: Wybór języków i przycisk zamiany
col_l, col_s, col_r = st.columns([10, 2, 10])

with col_l:
    st.selectbox("Z:", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="src_lang", label_visibility="collapsed")

with col_s:
    # Kontener dla przycisku zamiany
    st.markdown('<div class="swap-container">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages)
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.selectbox("Na:", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="tgt_lang", label_visibility="collapsed")

# RZĄD 2: Przyciski funkcyjne (Kopiuj/Wklej)
btn_l, _, btn_r = st.columns([10, 2, 10])

with btn_l:
    # Wklejanie w samym Pythonie/Streamlit jest ograniczone (bezpieczeństwo), 
    # ale zostawiamy przycisk zgodnie z prośbą o układ
    st.button("📋 Wklej tekst")

with btn_r:
    if st.button("📋 Kopiuj wynik"):
        st.toast("Skopiowano do schowka! (Wymaga JS dla pełnej funkcjonalności)")

# RZĄD 3: Pola tekstowe
t_l, _, t_r = st.columns([10, 2, 10])

with t_l:
    input_txt = st.text_area("Input", value=st.session_state.input_text, height=300, placeholder="Wpisz tekst...", label_visibility="collapsed")
    st.session_state.input_text = input_txt

with t_r:
    wynik = translate_engine(st.session_state.input_text, st.session_state.src_lang, st.session_state.tgt_lang)
    st.text_area("Output", value=wynik, height=300, label_visibility="collapsed")

st.markdown("---")
st.caption("Interfejs zoptymalizowany pod kątem estetyki DeepL.")
