import streamlit as st
import json
import re
from deep_translator import GoogleTranslator
from streamlit_javascript import st_javascript

# ================== 1. DYNAMICZNE POBIERANIE JĘZYKÓW ==================
@st.cache_resource
def get_all_languages():
    try:
        langs = GoogleTranslator().get_supported_languages(as_dict=True)
        return {name.capitalize(): code for name, code in langs.items()}
    except:
        # Fallback, gdyby API Google miało problem
        return {"Polish": "pl", "English": "en", "German": "de"}

GOOGLE_LANGS = get_all_languages()
ALL_OPTIONS = {"Auto": "auto", "Słowiański (Slo)": "slo", **GOOGLE_LANGS}

# ================== 2. DETEKCJA JĘZYKA UI (JavaScript) ==================
# Pobieramy język bezpośrednio z przeglądarki użytkownika
st_lang = st_javascript("window.navigator.language")

# Baza tłumaczeń interfejsu
UI_TRANSLATIONS = {
    "pl": {"title": "Tłumacz", "from": "Z języka:", "to": "Na język:", "input": "Wpisz tekst:", "btn": "🔄 Tłumacz", "res": "Wynik:", "warn": "⚠️ Wpisz tekst."},
    "en": {"title": "Translator", "from": "From:", "to": "To:", "input": "Enter text:", "btn": "🔄 Translate", "res": "Result:", "warn": "⚠️ Please enter text."},
    "de": {"title": "Übersetzer", "from": "Von:", "to": "Nach:", "input": "Text eingeben:", "btn": "🔄 Übersetzen", "res": "Ergebnis:", "warn": "⚠️ Text eingeben."},
    "fr": {"title": "Traducteur", "from": "De:", "to": "Vers:", "input": "Entrez le texte:", "btn": "🔄 Traduire", "res": "Résultat:", "warn": "⚠️ Entrez le texte."},
    "es": {"title": "Traductor", "from": "De:", "to": "A:", "input": "Ingrese texto:", "btn": "🔄 Traducir", "res": "Resultado:", "warn": "⚠️ Ingrese texto."}
}

# Logika wyboru języka UI
if st_lang:
    detected_code = st_lang[:2].lower()
    lang_code = detected_code if detected_code in UI_TRANSLATIONS else "en"
else:
    lang_code = "pl" # Domyślnie polski, dopóki JS nie odpowie

ui = UI_TRANSLATIONS[lang_code]

# ================== 3. KONFIGURACJA STRONY ==================
st.set_page_config(page_title=ui["title"], layout="wide")

st.markdown("""
    <style>
    .main { max-width: 900px; margin: 0 auto; }
    .stTextArea textarea { font-size: 1.1rem; }
    @media (max-width: 600px) {
        .stButton button { width: 100%; }
    }
    </style>
    """, unsafe_allow_html=True)

# ================== 4. LOGIKA SŁOWIAŃSKA & DICT ==================
@st.cache_data
def load_json_safe(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

osnova = load_json_safe("osnova.json")
vuzor = load_json_safe("vuzor.json")

@st.cache_data
def build_dict(osnova, vuzor):
    pl_to_slo = {}
    slo_to_pl = {}
    for entry in osnova + vuzor:
        pol = entry.get("polish", "").lower().strip()
        slo = entry.get("slovian", "").strip()
        if pol and slo:
            pl_to_slo[pol] = slo
            slo_to_pl[slo.lower()] = pol
    return pl_to_slo, slo_to_pl

pl_to_slo, slo_to_pl = build_dict(osnova, vuzor)

def translate_pl_to_slo(text):
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    result = []
    for t in tokens:
        low = t.lower()
        if low in pl_to_slo:
            res = pl_to_slo[low]
            if t.istitle(): res = res.capitalize()
            elif t.isupper(): res = res.upper()
            result.append(res)
        else:
            result.append(t)
    return "".join(result)

def google_translate(text, src, tgt):
    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except Exception as e:
        return f"(Error: {e})"

# ================== 5. INTERFEJS UŻYTKOWNIKA ==================
st.write(f"### 🌐 Slovo")
st.title(ui["title"])

col1, col2 = st.columns(2)
with col1:
    src_label = st.selectbox(ui["from"], list(ALL_OPTIONS.keys()), index=0)
with col2:
    # Próba inteligentnego ustawienia celu na Polski
    try:
        p_idx = list(ALL_OPTIONS.values()).index("pl")
    except:
        p_idx = 1
    tgt_label = st.selectbox(ui["to"], list(ALL_OPTIONS.keys()), index=p_idx)

user_input = st.text_area(ui["input"], height=150, placeholder="...")

if st.button(ui["btn"], type="primary"):
    if user_input.strip():
        src_code = ALL_OPTIONS[src_label]
        tgt_code = ALL_OPTIONS[tgt_label]
        
        with st.spinner('...'):
            if tgt_code == "slo":
                # Do Słowiańskiego zawsze przez Polski dla precyzji słownika
                pl_text = google_translate(user_input, src_code, "pl") if src_code != "pl" else user_input
                result = translate_pl_to_slo(pl_text)
            elif src_code == "slo":
                # Ze Słowiańskiego na dowolny przez Polski
                tokens = re.findall(r'\w+|[^\w\s]|\s+', user_input)
                pl_text = "".join([slo_to_pl.get(t.lower(), t) for t in tokens])
                result = google_translate(pl_text, "pl", tgt_code)
            else:
                # Normalne Google -> Google
                result = google_translate(user_input, src_code, tgt_code)
            
            st.divider()
            st.markdown(f"### {ui['res']}")
            st.success(result)
    else:
        st.warning(ui["warn"])
