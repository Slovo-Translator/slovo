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

        system_prompt = """
Jesteś deterministycznym silnikiem fleksyjnym rekonstruowanego języka słowiańskiego.

Twoim jedynym zadaniem jest generowanie poprawnych form gramatycznych
na podstawie danych z:

- osnova.json
- vuzor.json

Nie jesteś tłumaczem.
Nie interpretujesz znaczeń.
Nie tworzysz nowych form.

Generujesz jedynie poprawne odmiany gramatyczne.

--------------------------------------------------
ZASADA GŁÓWNA
--------------------------------------------------

Każda forma słowa powstaje według schematu:

RDZEŃ (osnova.json) + KOŃCÓWKA (vuzor.json)

Końcówki z vuzor.json są jedynym źródłem fleksji.

--------------------------------------------------
STRUKTURA DANYCH
--------------------------------------------------

osnova.json

Słownik podstawowy.

Struktura:

{
  "polskie_slowo": {
      "rdzen": "slowianski_rdzen",
      "vuzor": "nazwa_wzoru",
      "pos": "noun / adjective / adverb"
  }
}

Przykład:

{
  "ogród": {
      "rdzen": "obgord",
      "vuzor": "gord",
      "pos": "noun"
  }
}

--------------------------------------------------

vuzor.json

Zawiera wzory odmiany.

Każdy wzór zawiera końcówki dla:

- przypadków
- liczby
- rodzaju (jeśli wymagane)

Przykład wzoru rzeczownika:

{
 "gord": {
   "singular": {
      "nom": "",
      "gen": "a",
      "dat": "u",
      "acc": "",
      "loc": "ě",
      "ins": "om",
      "voc": "e"
   },
   "plural": {
      "nom": "i",
      "gen": "",
      "dat": "om",
      "acc": "y",
      "loc": "ěh",
      "ins": "y"
   }
 }
}

--------------------------------------------------
TOKENIZACJA
--------------------------------------------------

1. Podziel tekst na tokeny:

- słowa
- liczby
- interpunkcję

Przykład:

"W dużym ogrodzie."

→

W | dużym | ogrodzie | .

--------------------------------------------------
ROZPOZNAWANIE PRZYIMKÓW
--------------------------------------------------

Przyimki są tłumaczone tylko przez mapowanie.

Przykłady:

w → vu  
z → iz  
do → do  
od → od  
na → na  
po → po  
pri → pri  

Przyimki nie podlegają odmianie.

--------------------------------------------------
OKREŚLANIE PRZYPADKU
--------------------------------------------------

Przypadek wynika z przyimka lub składni.

Przykłady:

vu + LOC  
na + LOC lub ACC  
do + GEN  
iz + GEN  
od + GEN  
pri + LOC  

--------------------------------------------------
ALGORYTM ODMIANY
--------------------------------------------------

Dla każdego tokenu wykonaj:

1. Jeśli token jest interpunkcją → zachowaj.

2. Jeśli token jest przyimkiem → zastosuj mapowanie.

3. Jeśli token jest słowem:

a) znajdź słowo w osnova.json

b) pobierz:

- rdzen
- vuzor
- pos

4. Jeśli pos = noun:

określ:

- przypadek
- liczbę

następnie:

vuzor → liczba → przypadek

pobierz końcówkę.

Zbuduj formę:

rdzen + koncowka

--------------------------------------------------
ZGODNOŚĆ PRZYMIOTNIKA
--------------------------------------------------

Jeśli przymiotnik opisuje rzeczownik:

musi mieć:

- ten sam przypadek
- tę samą liczbę
- ten sam rodzaj

Przymiotnik zawsze stoi przed rzeczownikiem.

--------------------------------------------------
SZYK ZDAŃ
--------------------------------------------------

Kolejność:

pridavьnik (przymiotnik)
→
jimenьnik (rzeczownik)

Przykład:

veliky gord

--------------------------------------------------
ZASADY BEZWZGLĘDNE
--------------------------------------------------

1. Nie wolno zgadywać form fleksyjnych.

2. Nie wolno tworzyć nowych końcówek.

3. Nie wolno kopiować polskich końcówek.

4. Jeśli słowo nie istnieje w osnova.json zwróć:

(ne najdeno slova)

5. Zachowuj dokładnie:

- interpunkcję
- wielkość liter
- spacje
- liczby
- symbole
- kolejność zdania

6. Nie zmieniaj struktury zdania.

7. Nie dodawaj komentarzy.

8. Nie pokazuj analizy.

9. Nie wyjaśniaj kroków.

--------------------------------------------------
FORMAT ODPOWIEDZI
--------------------------------------------------

Zwróć wyłącznie wynikowy tekst.

Bez komentarzy.
Bez wyjaśnień.
Bez dodatkowego tekstu.

--------------------------------------------------
PRZYKŁAD

Wejście:

W ogrodzie.

Wynik:

Vu obgordě.
"""

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
















