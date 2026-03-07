import streamlit as st
import json
import os
import re
from collections import defaultdict
from groq import Groq

# ================== KONFIGURACJA STRONY ==================
st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .stTextArea textarea {background-color: #1a1a1a; color: #dcdcdc; font-size: 1.1rem;}
    .stSuccess {background-color: #1e2a1e; color: #90ee90; border: 1px solid #4CAF50;}
</style>
""", unsafe_allow_html=True)

# ================== POŁĄCZENIE Z API ==================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Błąd klucza API. Upewnij się, że GROQ_API_KEY jest w secrets.")
    st.stop()

# ================== ŁADOWANIE I INDEKSOWANIE DANYCH ==================

@st.cache_data
def load_data():
    def read_json(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    osnova_raw = read_json("osnova.json")
    vuzor_raw = read_json("vuzor.json")
    
    # Indeksujemy słownik po polskim słowie
    dictionary = defaultdict(list)
    for entry in osnova_raw:
        pol = entry.get("polish", "").lower().strip()
        if pol:
            dictionary[pol].append(entry)
            
    return dictionary, vuzor_raw, osnova_raw

# NAPRAWA BŁĘDU: Przypisujemy wyniki do zmiennych globalnych
dictionary, vuzor_list, osnova_raw = load_data()

# ================== LOGIKA ESTRAKCJI KONTEKSTU ==================

def get_grammatical_context(text, dic, vuzory):
    words = re.findall(r'\b\w+\b', text.lower())
    found_mappings = []
    relevant_forms = []
    seen_slovian_bases = set()

    for w in words:
        entries = []
        if w in dic:
            entries = dic[w]
        elif len(w) >= 4:
            pref = w[:4]
            for pol_key in dic:
                if pol_key.startswith(pref):
                    entries.extend(dic[pol_key])

        for e in entries:
            found_mappings.append(e)
            s_base = e.get("slovian")
            
            # Szukamy form w vuzorze na podstawie słowa bazowego
            if s_base and s_base not in seen_slovian_bases:
                for v in vuzory:
                    v_case = v.get("type and case", "")
                    v_slov = v.get("slovian", "")
                    
                    # Sprawdzenie czy wiersz dotyczy danego słowa
                    if s_base == v_slov or f"'{s_base}'" in v_case:
                        relevant_forms.append({
                            "forma": v_slov,
                            "gramatyka": v_case
                        })
                seen_slovian_bases.add(s_base)

    return found_mappings, relevant_forms

# ================== INTERFEJS UŻYTKOWNIKA ==================

st.title("🏛️ Perkladačь slověnьskogo ęzyka")
st.subheader("Precyzyjne tłumaczenie z wykorzystaniem tabel odmian")

user_input = st.text_area(
    "Vupiši slovo alibo rěčenьje (PL):",
    placeholder="Np. W Słowianach siła. Miasto jest wielkie.",
    height=150
)

if user_input:
    with st.spinner("Analiza gramatyczna i tłumaczenie..."):
        
        mappings, grammar_pool = get_grammatical_context(user_input, dictionary, vuzor_list)

        # Przygotowanie kontekstu dla AI (szczegóły: część mowy, rodzaj, przypadek)
        mappings_str = "\n".join([f"- PL: {m.get('polish')} -> SL_BASE: {m.get('slovian')}" for m in mappings])
        
        grammar_str = ""
        for item in grammar_pool:
            grammar_str += f"Forma: {item['forma']} | Info: {item['gramatyka']}\n"

        system_prompt = f"""Jesteś ekspertem lingwistyki słowiańskiej. 
Twoim zadaniem jest przetłumaczyć polski tekst na język słowiański, używając DOKŁADNYCH FORM z dostarczonych tabel odmian.

SŁOWNIK (FORMY BAZOWE):
{mappings_str}

DOSTĘPNE FORMY GRAMATYCZNE (RODZAJ, LICZBA, PRZYPADEK, ŻYWOTNOŚĆ):
{grammar_str}

ZASADY:
1. Rozpoznaj formę w polskim zdaniu (np. "miastach" to miejscownik, liczba mnoga).
2. Znajdź w tabeli powyżej formę słowiańską, która ma w Info: 'locative' oraz 'plural'.
3. Jeśli słowo to 'gord', a szukasz locative plural, z tabeli wybierz 'gorděh'.
4. Zachowaj szyk: Przymiotnik przed rzeczownikiem.
5. Nie dodawaj komentarzy, tylko czyste tłumaczenie.

TEKST: "{user_input}" """

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0,
                max_tokens=1000
            )

            translation = response.choices[0].message.content.strip()

            st.markdown("### Vynik perklada:")
            st.success(translation)
            
            with st.expander("Szczegóły analizy tabel"):
                st.text(grammar_str if grammar_str else "Brak pasujących wzorów w vuzor.json")

        except Exception as e:
            st.error(f"Błąd API: {e}")

# ================== STOPKA (NAPRAWIONA) ==================
st.divider()
st.caption(f"Baza danych: {len(osnova_raw)} słów podstawowych | {len(vuzor_list)} form gramatycznych.")
