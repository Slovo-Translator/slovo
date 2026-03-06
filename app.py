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
    .stSuccess { background-color: #050505; border: 1px solid #2e7d32; color: #dcdcdc; font-size: 1.2rem; }
    .stCaption { color: #888; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. KLUCZ API I KONFIGURACJA KLIENTA
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
        st.error(f"Blǫd osnovy: {e}")
        return {}

dictionary = load_dictionary()

# ============================================================
# 4. LOGIKA WYSZUKIWANIA I TŁUMACZENIA
# ============================================================
def get_relevant_context(text, dic):
    search_text = re.sub(r'[^\w\s]', '', text.lower())
    words = search_text.split()
    relevant_entries = []
    
    for word in words:
        if word in dic:
            relevant_entries.extend(dic[word])
        elif len(word) > 3:
            for key in dic.keys():
                if word.startswith(key[:4]) and len(key) > 3:
                    relevant_entries.extend(dic[key])
    
    seen = set()
    unique_entries = []
    for e in relevant_entries:
        identifier = (e['slovian'], e.get('type and case', ''))
        if identifier not in seen:
            seen.add(identifier)
            unique_entries.append(e)
            
    return unique_entries[:40]

# ============================================================
# 5. INTERFEJS UŻYTKOWNIKA
# ============================================================
st.title("Perkladačь slověnьskogo ęzyka")

user_input = st.text_input("Vupiši slovo alibo rěčenьje:", placeholder="")

if user_input:
    with st.spinner("Orzmyslь nad čęstьmi ęzyka i perklad..."):
        
        # --- KROK 1: DIRECT MATCH (Blokada błędów AI) ---
        input_clean = user_input.lower().strip()
        response_text = None
        matches = get_relevant_context(user_input, dictionary)

        # Jeśli to pojedyncze słowo i jest w bazie - bierzemy bezpośrednio
        if input_clean in dictionary:
            exact_val = dictionary[input_clean][0]['slovian']
            # Zachowanie wielkości liter
            if user_input.istitle(): response_text = exact_val.capitalize()
            elif user_input.isupper(): response_text = exact_val.upper()
            else: response_text = exact_val
        
        # --- KROK 2: WYWOŁANIE AI (Dla zdań lub braku słowa) ---
        if not response_text:
            context_str = "\n".join([
                f"- POLSKIE: {m['polish']} | UŻYJ FORMY: {m['slovian']} | GRAMATYKA: {m.get('type and case','')}"
                for m in matches
            ])

            system_prompt = """Jesteś rygorystycznym tłumaczem polsko-prasłowiańskim.
            TWOJE JEDYNE ZADANIE: Przetłumacz tekst używając WYŁĄCZNIE form z sekcji BAZA.
            
            ZASADY KRYTYCZNE:
            1. Jeśli w BAZIE podano formę (np. 'esmy'), MUSISZ jej użyć. Nie poprawiaj jej na 'esmь'.
            2. Ignoruj własną wiedzę historyczną, jeśli jest sprzeczna z BAZĄ.
            3. Zakaz używania cyrylicy (wyjątek: znak ь).
            4. Przymiotnik zawsze przed rzeczownikiem.
            5. Zwróć tylko czysty tekst tłumaczenia."""

            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"BAZA DANYCH (użyj tych form!):\n{context_str}\n\nTEKST DO TŁUMACZENIA: {user_input}"}
                    ],
                    model="openai/gpt-oss-120b",
                    temperature=0.0
                )
                response_text = chat_completion.choices[0].message.content.strip()
            except Exception as e:
                st.error(f"Blǫd umětьnogo uma: {e}")
                response_text = "(error)"

        # --- KROK 3: WYŚWIETLANIE ---
        st.markdown("### Vynik perklada:")
        st.success(response_text)

        if matches:
            with st.expander("Užito žerdlo jiz osnovy"):
                for m in matches:
                    st.write(f"**{m['polish']}** → `{m['slovian']}` ({m.get('type and case','')})")

