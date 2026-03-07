import streamlit as st
import json
import os
import re
from collections import defaultdict
from groq import Groq

# ================== KONFIGURACJA ==================
st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")

st.markdown("""
<style>
.main {background:#0e1117}
.stTextArea textarea {background:#1a1a1a;color:#dcdcdc;font-size:1.1rem;}
</style>
""", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ================== ŁADOWANIE I FILTROWANIE DANYCH ==================
@st.cache_data
def load_data():
    def load_json(name):
        if not os.path.exists(name): return []
        with open(name, "r", encoding="utf-8") as f: return json.load(f)
    return load_json("vuzor.json") + load_json("osnova.json")

DATA = load_data()

def get_filtered_context(text):
    tokens = re.findall(r'\w+', text.lower())
    context_chunks = []
    
    # Mapowanie przyimków na oczekiwany tag gramatyczny
    prep_map = {"w": "locative", "we": "locative", "na": "locative", "do": "genitive"}
    
    for i, word in enumerate(tokens):
        # Określamy wymagany przypadek na podstawie poprzedniego słowa
        required_case = prep_map.get(tokens[i-1]) if i > 0 else None
        
        relevant = []
        stem = word[:4] if len(word) >= 4 else word
        
        for entry in DATA:
            pl = entry.get("polish", "").lower()
            if word == pl or (len(word) >= 4 and pl.startswith(stem)):
                # Jeśli mamy przyimek, dajemy priorytet rzeczownikom w danym przypadku
                entry_info = entry.get("type and case", "").lower()
                if required_case and required_case in entry_info and "noun" in entry_info:
                    relevant.insert(0, entry) # Priorytet na górę listy
                else:
                    relevant.append(entry)
        
        context_chunks.extend(relevant[:10]) # Ograniczamy szum
    return context_chunks

# ================== INTERFEJS ==================
st.title("Perkladačь slověnьskogo ęzyka")
user_input = st.text_area("Vupiši rěčenьje:", placeholder="W moim ogrodzie.", height=150)

if user_input:
    with st.spinner("Generowanie precyzyjnego tłumaczenia..."):
        matches = get_filtered_context(user_input)
        
        # Formatowanie danych z wyraźnym zaznaczeniem części mowy
        mapping = "\n".join([
            f"ID:{idx} | PL: {m['polish']} | SL: {m['slovian']} | TAG: {m.get('type and case', '')}"
            for idx, m in enumerate(matches)
        ])

        system_prompt = f"""Jesteś rygorystycznym tłumaczem.
ZASADY BEZWZGLĘDNE:
1. Używaj TYLKO słów z sekcji SL w dostarczonych danych.
2. Po słowie 'Vu' (w) MUSISZ użyć formy oznaczonej jako 'noun' i 'locative' (np. obgordě).
3. ZAKAZ: Nigdy nie używaj słów kończących się na '-ti' (np. obgordjati) jako miejsca/rzeczownika. To są czasowniki.
4. Słowo 'są' to 'sǫtь'.
5. Jeśli brakuje dokładnej formy, użyj najbardziej zbliżonej znaczeniowo formy rzeczownikowej, nie czasownikowej.

DANE DOSTĘPNE:
{mapping}

Przetłumacz zdanie użytkownika, dbając o poprawność gramatyczną zgodnie z TAG-ami."""

        try:
            chat = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0
            )
            st.markdown("### Vynik perklada:")
            st.success(chat.choices[0].message.content.strip())
        except Exception as e:
            st.error(f"Błąd: {e}")

    with st.expander("Weryfikacja filtrów gramatycznych"):
        st.write("Dostarczone do AI przefiltrowane rekordy (z priorytetem dla noun/locative):")
        st.json(matches)
