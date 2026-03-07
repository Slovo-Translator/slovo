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

    # Tworzymy mapę: polskie_slowo -> lista dostępnych form (z gramatyką)
    full_db = defaultdict(list)
    
    # Najpierw Vuzor (formy odmienione mają priorytet)
    for entry in vuzor:
        pl = entry.get("polish", "").lower().strip()
        if pl: full_db[pl].append(entry)
            
    # Potem Osnova (jako uzupełnienie)
    for entry in osnova:
        pl = entry.get("polish", "").lower().strip()
        if pl: full_db[pl].append(entry)
            
    return full_db

db = load_and_index_data()

# ================== LOGIKA GRAMATYCZNA ==================

# Mapa przyimków sterujących przypadkiem następnego słowa
RULES = {
    "w": "locative",
    "we": "locative",
    "o": "locative",
    "na": "locative",
    "do": "genitive",
    "z": "genitive",
    "ku": "dative",
    "dla": "genitive"
}

def get_best_form(pl_word, required_case=None):
    options = db.get(pl_word, [])
    if not options:
        return None

    # Jeśli mamy narzucony przypadek (np. przez przyimek), szukamy go w 'type and case'
    if required_case:
        for opt in options:
            case_info = opt.get("type and case", "").lower()
            if required_case in case_info:
                return opt.get("slovian")

    # Jeśli nie znaleźliśmy konkretnego przypadku, bierzemy najczęstszą formę (zazwyczaj mianownik)
    return options[0].get("slovian")

def translate_engine(text):
    # Rozbijamy na słowa, znaki i spacje, by zachować formatowanie
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    translated_parts = []
    
    current_case_context = None

    for token in tokens:
        # Jeśli to spacja lub interpunkcja - przepisz bez zmian
        if not re.match(r'\w+', token):
            translated_parts.append(token)
            continue

        word_low = token.lower().strip()
        
        # Sprawdź, czy to słowo to przyimek, który narzuci przypadek NASTĘPNEMU słowu
        this_word_case = current_case_context
        current_case_context = RULES.get(word_low)

        # Pobierz tłumaczenie uwzględniając kontekst gramatyczny
        slovian_word = get_best_form(word_low, this_word_case)

        if slovian_word:
            # Zachowanie wielkości liter
            if token[0].isupper():
                slovian_word = slovian_word.capitalize()
            translated_parts.append(slovian_word)
        else:
            # Twoja zasada bezwzględna nr 1
            translated_parts.append("(ne najdeno slova)")

    return "".join(translated_parts)

# ================== INTERFEJS UŻYTKOWNIKA ==================

st.title("Perkladačь slověnьskogo ęzyka")
st.caption("Tryb offline: Lokalny silnik gramatyczny (Osnova + Vuzor)")

user_input = st.text_area(
    "Vupiši slovo alibo rěčenьje:",
    placeholder="Np. W moim grodzie.",
    height=150
)

if user_input:
    # Proces tłumaczenia
    result = translate_engine(user_input)
    
    st.markdown("### Vynik perklada:")
    st.success(result)

    # Diagnostyka dla Ciebie
    with st.expander("Szczegóły dopasowania (debug)"):
        words = re.findall(r'\w+', user_input.lower())
        for w in words:
            found = db.get(w)
            if found:
                st.write(f"✅ **{w}**: znaleziono {len(found)} form(y).")
            else:
                st.write(f"❌ **{w}**: brak w bazie danych.")

st.divider()
st.info("Aplikacja automatycznie dopasowuje przypadki (np. miejscownik po 'w') korzystając z bazy Vuzor.")
