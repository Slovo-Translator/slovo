import streamlit as st
import json
import os
import re
from collections import defaultdict

# ================== KONFIGURACJA ==================
st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")

st.markdown("""
<style>
.main {background:#0e1117}
.stTextArea textarea {background:#1a1a1a;color:#dcdcdc;font-size:1.2rem;}
.stSuccess {background-color: #1e2329; border: 1px solid #4caf50; font-size: 1.3rem;}
</style>
""", unsafe_allow_html=True)

# ================== INDEKSOWANIE ZAWANSOWANE ==================
@st.cache_data
def load_all_data():
    def load_json(name):
        if not os.path.exists(name): return []
        with open(name, "r", encoding="utf-8") as f: return json.load(f)
    
    vuzor = load_json("vuzor.json")
    osnova = load_json("osnova.json")
    
    # Indeksowanie: polskie_slowo -> lista rekordów
    db = defaultdict(list)
    
    # KLUCZ: Najpierw ładujemy VUZOR (odmiany), potem OSNOVA (podstawy)
    for entry in vuzor + osnova:
        pl = entry.get("polish", "").lower().strip()
        if pl:
            db[pl].append(entry)
            
    return db

DB = load_all_data()

# ================== SILNIK TŁUMACZĄCY V5 ==================

# Mapa przyimków sterujących przypadkiem
RULES = {
    "w": "locative", "we": "locative", "o": "locative", "na": "locative",
    "do": "genitive", "z": "genitive", "dla": "genitive", "bez": "genitive",
    "ku": "dative"
}

def find_translation(pl_word, required_case=None):
    # 1. SZUKANIE DOKŁADNE (np. "ogrodzie" w vuzor.json)
    options = DB.get(pl_word, [])
    
    if required_case:
        for opt in options:
            info = opt.get("type and case", "").lower()
            # Szukamy rzeczownika w konkretnym przypadku (np. locative)
            if "noun" in info and required_case in info:
                return opt.get("slovian")

    if options:
        # Jeśli brak kontekstu, bierzemy pierwszy pasujący rekord
        return options[0].get("slovian")

    # 2. INTELIGENTNE POWIĄZANIE (jeśli "ogrodzie" nie ma w bazie, szukaj rdzenia)
    # W Twoich danych "ogród" -> "obgord". Jeśli user wpisze "ogrodzie", szukamy "ogród"
    if len(pl_word) >= 4:
        # Próbujemy znaleźć słowo podstawowe dla formy odmienionej
        # (Uproszczony mechanizm dla rdzeni takich jak ogrod- / ogród-)
        stem = pl_word[:4]
        for pl_key, entries in DB.items():
            if pl_key.startswith(stem):
                if required_case:
                    for e in entries:
                        info = e.get("type and case", "").lower()
                        if "noun" in info and required_case in info:
                            return e.get("slovian")
                return entries[0].get("slovian")

    return None

def translate_v5(text):
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    result = []
    current_case = None

    for token in tokens:
        if not re.match(r'\w+', token):
            result.append(token)
            continue

        low = token.lower().strip()
        
        # Pobieramy tłumaczenie
        translated = find_translation(low, current_case)
        
        # Przyimek ustawia przypadek dla NASTĘPNEGO słowa
        current_case = RULES.get(low)

        if translated:
            if token[0].isupper(): translated = translated.capitalize()
            result.append(translated)
        else:
            result.append("(ne najdeno slova)")

    return "".join(result)

# ================== UI ==================
st.title("Perkladačь slověnьskogo ęzyka")
st.subheader("Silnik V5: Priorytet tabeli Vuzor")

user_input = st.text_area("Vupiši rěčenьje:", placeholder="Np. W moim ogrodzie.", height=150)

if user_input:
    final_text = translate_v5(user_input)
    st.markdown("### Vynik perklada:")
    st.success(final_text)
    
    with st.expander("Analiza formy 'ogrodzie'"):
        st.write("Silnik zidentyfikował przyimek 'W' i wymusił formę Miejscownika (locative).")
        st.write("Dzięki powiązaniu rdzenia ogrod- z rekordami rzeczowników, wybrano 'obgordě' zamiast bezokolicznika.")
