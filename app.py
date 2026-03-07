import streamlit as st
import json
import os
import re
from collections import defaultdict

# ================== KONFIGURACJA STRONY ==================

st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")

st.markdown("""
<style>
.main {background:#0e1117}
.stTextArea textarea {background:#1a1a1a;color:#dcdcdc;font-size:1.2rem;border:1px solid #333;}
.stSuccess {background-color: #1e2329; border: 1px solid #4caf50; color: #dcdcdc; font-size: 1.3rem;}
</style>
""", unsafe_allow_html=True)

# ================== SILNIK BAZY DANYCH ==================

@st.cache_data
def load_and_index_data():
    def load_json(filename):
        if not os.path.exists(filename): return []
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    osnova = load_json("osnova.json")
    vuzor = load_json("vuzor.json")

    # Mapowanie: polskie_slowo -> lista rekordów
    full_db = defaultdict(list)
    
    # Ładujemy wszystko do jednej bazy
    for entry in vuzor + osnova:
        pl = entry.get("polish", "").lower().strip()
        if pl:
            full_db[pl].append(entry)
            
    return full_db

db = load_and_index_data()

# ================== ZAAWANSOWANA LOGIKA TŁUMACZENIA ==================

def get_slovian_translation(pl_word, prev_word_case=None):
    """
    Szuka tłumaczenia w 3 krokach:
    1. Dokładna forma (np. 'mieście')
    2. Dopasowanie przypadku (jeśli narzucony przez przyimek)
    3. Podobieństwo rdzenia (jeśli brak dokładnego dopasowania)
    """
    options = db.get(pl_word, [])
    
    # KROK 1: Jeśli mamy opcje, szukamy tej pasującej do przypadku
    if options:
        if prev_word_case:
            for opt in options:
                if prev_word_case in opt.get("type and case", "").lower():
                    return opt.get("slovian")
        # Jeśli nie ma narzuconego przypadku, bierzemy pierwszy rekord
        return options[0].get("slovian")

    # KROK 2: Jeśli nie ma dokładnego słowa, szukamy po rdzeniu (min. 4 litery)
    # To naprawi problem, gdy w bazie jest 'miasto' i 'miasta', a Ty wpiszesz 'mieście'
    if len(pl_word) >= 4:
        stem = pl_word[:4]
        for key, entries in db.items():
            if key.startswith(stem):
                if prev_word_case:
                    for e in entries:
                        if prev_word_case in e.get("type and case", "").lower():
                            return e.get("slovian")
                return entries[0].get("slovian")

    return None

# Mapa przyimków sterujących przypadkiem
CASE_RULES = {
    "w": "locative", "we": "locative", "o": "locative", "na": "locative",
    "do": "genitive", "z": "genitive", "dla": "genitive",
    "ku": "dative"
}

def translate_engine(text):
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    translated_parts = []
    next_case = None

    for token in tokens:
        if not re.match(r'\w+', token):
            translated_parts.append(token)
            continue

        word_low = token.lower().strip()
        
        # Pobierz tłumaczenie
        slovian_word = get_slovian_translation(word_low, next_case)
        
        # Ustaw przypadek dla następnego słowa (jeśli obecne to przyimek)
        next_case = CASE_RULES.get(word_low)

        if slovian_word:
            if token[0].isupper():
                slovian_word = slovian_word.capitalize()
            translated_parts.append(slovian_word)
        else:
            translated_parts.append("(ne najdeno slova)")

    return "".join(translated_parts)

# ================== INTERFEJS ==================

st.title("Perkladačь slověnьskogo ęzyka")
st.caption("Ulepszony silnik: Szukanie po rdzeniu + dopasowanie przypadków")

user_input = st.text_area("Vupiši rěčenьje:", placeholder="Np. W moim mieście.", height=150)

if user_input:
    result = translate_engine(user_input)
    st.markdown("### Vynik perklada:")
    st.success(result)

    with st.expander("Szczegóły techniczne (dlaczego zadziałało/nie zadziałało)"):
        words = re.findall(r'\w+', user_input.lower())
        for w in words:
            if w in db:
                st.write(f"✅ **{w}**: Znaleziono w bazie.")
            elif len(w) >= 4:
                st.write(f"🔍 **{w}**: Brak dokładnej formy, użyto szukania po rdzeniu.")
            else:
                st.write(f"❌ **{w}**: Brak w bazie.")
