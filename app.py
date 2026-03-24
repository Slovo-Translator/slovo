import streamlit as st
import json
import re
from deep_translator import GoogleTranslator

# Auto-detect browser language
try:
    import streamlit_browser_language as sbl
    browser_lang = sbl.get_browser_language()[:2] or "pl"
except ImportError:
    browser_lang = "pl"

st.set_page_config(page_title="Tłumacz", layout="centered")

# ================== TRANSLATIONS ==================
translations = {
    "pl": {
        "title": "Tłumacz",
        "from_lang": "Z języka:",
        "to_lang": "Na język:",
        "input": "Wpisz tekst do tłumaczenia:",
        "button": "🔄 Tłumacz",
        "result": "### Wynik tłumaczenia:"
    },
    "en": {
        "title": "Translator",
        "from_lang": "From language:",
        "to_lang": "To language:",
        "input": "Write word or text for translation:",
        "button": "🔄 Translate",
        "result": "### Translation result:"
    },
    "de": {
        "title": "Übersetzer",
        "from_lang": "Von Sprache:",
        "to_lang": "In Sprache:",
        "input": "Text zum Übersetzen eingeben:",
        "button": "🔄 Übersetzen",
        "result": "### Übersetzungsergebnis:"
    },
    "fr": {
        "title": "Traducteur",
        "from_lang": "De la langue :",
        "to_lang": "Vers la langue :",
        "input": "Saisissez le texte à traduire :",
        "button": "🔄 Traduire",
        "result": "### Résultat de la traduction :"
    },
    "es": {
        "title": "Traductor",
        "from_lang": "Del idioma:",
        "to_lang": "Al idioma:",
        "input": "Escribe el texto para traducir:",
        "button": "🔄 Traducir",
        "result": "### Resultado de la traducción:"
    },
    "ru": {
        "title": "Переводчик",
        "from_lang": "С языка:",
        "to_lang": "На язык:",
        "input": "Введите текст для перевода:",
        "button": "🔄 Перевести",
        "result": "### Результат перевода:"
    }
}

ui_lang = browser_lang if browser_lang in translations else "pl"
t = translations[ui_lang]

# Google languages
google_langs = {
    "Auto": "auto",
    "Polski": "pl",
    "Angielski": "en",
    "Niemiecki": "de",
    "Francuski": "fr",
    "Hiszpański": "es",
    "Rosyjski": "ru",
    "Słowiański": "slo"
}

# ================== LOAD & DICT ==================
@st.cache_data
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Błąd {filename}: {e}")
        return []

osnova = load_json("osnova.json")
vuzor = load_json("vuzor.json")

@st.cache_data
def build_dict(osnova, vuzor):
    pl_to_slo = {}
    slo_to_pl = {}
    def process(data):
        for entry in data:
            pol = entry.get("polish", "").lower().strip()
            slo = entry.get("slovian", "").strip()
            if pol and slo:
                pl_to_slo[pol] = slo
                slo_to_pl[slo.lower()] = pol
    process(osnova)
    process(vuzor)
    return pl_to_slo, slo_to_pl

pl_to_slo, slo_to_pl = build_dict(osnova, vuzor)

# ================== TRANSLATE FUNCTIONS ==================
def translate_pl_to_slo(text):
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    result = []
    for token in tokens:
        if re.match(r'\w+', token):
            lower = token.lower()
            if lower in pl_to_slo:
                translated = pl_to_slo[lower]
            else:
                translated = None
                for k, v in pl_to_slo.items():
                    if lower.startswith(k[:4]):
                        translated = v
                        break
                if not translated:
                    translated = f"[{token}]"
            if token.istitle(): translated = translated.capitalize()
            elif token.isupper(): translated = translated.upper()
            result.append(translated)
        else:
            result.append(token)
    return "".join(result)

def translate_slo_to_pl(text):
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    result = []
    for token in tokens:
        if re.match(r'\w+', token):
            lower = token.lower()
            translated = slo_to_pl.get(lower, token)
            if token.istitle(): translated = translated.capitalize()
            elif token.isupper(): translated = translated.upper()
            result.append(translated)
        else:
            result.append(token)
    return "".join(result)

def google_translate(text, source, target):
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except Exception as e:
        return f"(błąd: {e})"

# ================== UI ==================
st.markdown("### Slovo")  # Logo w lewym górnym rogu

st.title(t["title"])

col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox(t["from_lang"], list(google_langs.keys()), index=0)
with col2:
    target_lang = st.selectbox(t["to_lang"], list(google_langs.keys()), index=6)

user_input = st.text_area(t["input"], height=150)

if st.button(t["button"]) and user_input:
    src = google_langs[source_lang]
    tgt = google_langs[target_lang]
    if tgt == "slo":
        pl = google_translate(user_input, src, "pl")
        result = translate_pl_to_slo(pl)
    elif src == "slo":
        pl = translate_slo_to_pl(user_input)
        result = google_translate(pl, "pl", tgt)
    else:
        result = google_translate(user_input, src, tgt)
    st.markdown(t["result"])
    st.success(result)
