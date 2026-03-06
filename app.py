import streamlit as st
import json
import os
import re
from groq import Groq

# ============================================================
# 1. KONFIGURACJA I STYLIZACJA
# ============================================================
st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextInput > div > div > input { background-color: #1a1a1a; color: #dcdcdc; border: 1px solid #333; }
    .stTextArea > div > div > textarea { background-color: #1a1a1a; color: #dcdcdc; border: 1px solid #333; }
    .stSuccess { background-color: #050505; border: 1px solid #2e7d32; color: #dcdcdc; font-size: 1.2rem; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. KONFIGURACJA KLIENTA GROQ
# ============================================================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# 3. ŁADOWANIE BAZY DANYCH
# ============================================================
@st.cache_data
def load_dictionary():
    if not os.path.exists("osnova.json"):
        return {}
    try:
        with open("osnova.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        index = {}
        for entry in data:
            pl = entry.get("polish", "").lower().strip()
            if pl:
                if pl not in index: index[pl] = []
                index[pl].append(entry)
        return index
    except Exception as e:
        st.error(f"Błąd bazy: {e}")
        return {}

dictionary = load_dictionary()

# ============================================================
# 4. PRECYZYJNA LOGIKA POBIERANIA KONTEKSTU (Słowa + Frazy)
# ============================================================
def get_strict_context(text, dic):
    # Wyciągamy słowa, ignorując interpunkcję dla wyszukiwania
    search_text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = search_text.split()
    relevant_entries = []
    
    for word in words:
        if word in dic:
            relevant_entries.extend(dic[word])
    
    seen = set()
    unique_entries = []
    for e in relevant_entries:
        identifier = (e['polish'].lower(), e['slovian'].lower())
        if identifier not in seen:
            seen.add(identifier)
            unique_entries.append(e)
            
    return unique_entries

# ============================================================
# 5. INTERFEJS UŻYTKOWNIKA
# ============================================================
st.title("Perkladačь slověnьskogo ęzyka")

# Używamy text_area zamiast text_input dla obsługi wielu linii
user_input = st.text_area("Vupiši slovo alibo rěčenьje:", placeholder="", height=200)

if user_input:
    with st.spinner("Przetwarzanie tekstu..."):
        matches = get_strict_context(user_input, dictionary)
        
        # Przygotowanie bardzo technicznej instrukcji mapowania
        mapping_rules = "\n".join([
            f"MAPUJ: '{m['polish']}' NA '{m['slovian']}'"
            for m in matches
        ])

        system_prompt = """Jesteś tłumaczem słowiańskiego (prasłowiańskiego) języka i działającym w trybie 'Search and Replace', a twoje jedyne źródła wiedzy o tym języku to pliki 'osnova.json' i 'vuzor.json'. 

ZADANIE:
Zastąp polskie słowa ich odpowiednikami z listy MAPOWANIA, zachowując nienaruszony format źródłowy.

RYGORYSTYCZNE ZASADY:
1. FORMAT: Zachowaj identyczne odstępy, spacje, znaki interpunkcyjne (. , ! ?), linki (http/www), symbole matematyczne (+ = / * %) i nowej linii (entery).
2. WIELKOŚĆ LITER: Odwzoruj wielkość liter słowa wejściowego:
   - Jeśli 'Słowo' -> 'Slovian'
   - Jeśli 'słowo' -> 'slovian'
   - Jeśli 'SŁOWO' -> 'SLOVIAN'
3. NIEZMIENNE: Jeśli słowa nie ma w MAPOWANIU, zostaw je w oryginale. Nie tłumacz niczego 'z głowy'.
4. BRAK DOPISKÓW: Zwróć wyłącznie przetworzony tekst. Nie dodawaj cudzysłowów ani wyjaśnień.
5. KOLEJNOŚĆ SŁÓW: Przymiotniki (oznaczone jako adjective - pridavьnik) i przysłówki (oznaczone jako adverb - prislovok) są zawsze przed rzeczownikami (oznaczone jako noun - jimenьnik), dokładnie tak samo, jak w języku rosyjskim dla przykładu 'Wojsko Słowiańskie' albo 'Słowiańskie Wojsko' to 'Slověnьsko Vojisko'.
6. Musisz rozpoznawać dobrze części mowy/języka polskiego i potem je dobrze odwzorowywać w przekładzie/tłumaczeniu na język słowiański (prasłowiański) w pliku 'vuzor.json' masz przykłady tworzenia gramatycznych odmian."""

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"LISTA MAPOWANIA:\n{mapping_rules}\n\nTEKST ŹRÓDŁOWY:\n{user_input}"}
                ],
                model="openai/gpt-oss-120b",
                temperature=0.0
            )
            response_text = chat_completion.choices[0].message.content.strip()

            # Wyświetlanie wyniku
            st.markdown("### Vynik perklada:")
            st.success(response_text)

        except Exception as e:
            st.error(f"Błąd modelu: {e}")

        if matches:
            with st.expander("Użyte mapowanie z bazy"):
                for m in matches:
                    st.write(f"'{m['polish']}' → `{m['slovian']}`")





