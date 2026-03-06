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
# 2. KLUCZ API I NOWY MODEL (llama-3.3-70b-versatile)
# ============================================================
# Zaktualizowano model na llama-3.3-70b-versatile, który zastąpił wycofany model
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
# 4. INTELIGENTNA LOGIKA RAG
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
# 5. INTERFEJS I PROMPT
# ============================================================
st.title("Perkladačь slověnьskogo ęzyka")

user_input = st.text_input("Vupiši slovo alibo rěčenьje:", placeholder="")

if user_input:
    with st.spinner("Orzmyslь nad čęstьmi ęzyka i perklad..."):
        matches = get_relevant_context(user_input, dictionary)
        
        # Przygotowanie kontekstu tak, by AI widziało Mati i ogordě jako jedyne opcje
        context_str = "\n".join([
            f"- POLSKIE: {m['polish']} | UŻYJ FORMY: {m['slovian']} | GRAMATYKA: {m.get('type and case','')}"
            for m in matches
        ])

        system_prompt = """Jesteś rygorystycznym silnikiem tłumaczącym z języka polskiego na prasłowiański. Twoim jedynym źródłem danych są pliki osnova.json (słownictwo i kontekst) oraz vuzor.json (wzorce odmian).I. ZASADY FUNDAMENTALNE (KRYTYCZNE)ŹRÓDŁA: Nie zmyślaj słów ani form. Jeśli słowa nie ma w osnova.json (nawet w formie podstawowej), zwróć: (ne najdeno slova) z zachowaniem wielkości liter.SKŁADNIA: Przymiotnik ZAWSZE przed rzeczownikiem. To zasada bezwzględna (np. pol. "Wojsko Słowiańskie" → słow. "Slověnьsko Vojьsko").ALFABET: Używaj wyłącznie alfabetu łacińskiego z polskimi znakami oraz znakami specjalnymi: ě, ę, ǫ oraz jerem miękkim ь / Ь.ZAKAZ CYRYLICY: Całkowity zakaz używania cyrylicy (oprócz ь). Wszystkie znaki takie jak а, б, в, г, д, е, ж, з, и... są zabronione. Twardy jer ъ jest zabroniony.WIELKOŚĆ LITER (Case-by-Case): Musisz rygorystycznie odwzorować formatowanie użytkownika dla każdego słowa:Matka → Mati | matka → mati | MATKA → MATI | mATKA → mATI.NIEZMIENNE: Linki, liczby i symbole matematyczne pozostaw w oryginale.II. PROCEDURA ANALIZY I TŁUMACZENIAKOREKTA WEJŚCIA: Jeśli tekst polski zawiera błędy ortograficzne, popraw je w pamięci przed procesem tłumaczenia.IDENTYFIKACJA: Rozpoznaj część mowy (POS), liczbę, rodzaj i przypadek polskiego słowa w zdaniu.LOGIKA WYBORU (osnova.json):Dopasuj słowo na podstawie kolumn: Gramatyka (Type & Case) oraz Context (Okolьnosti).Przykład: "Północ" jako kierunek to sěver, ale jako pora dnia to polunotь. Wybierz to, które pasuje do opisu angielskiego w bazie.GENEROWANIE FORM (vuzor.json):Jeśli w osnova.json nie ma gotowej odmiany, znajdź formę podstawową słowa, a następnie zastosuj wzorzec końcówek z vuzor.json.Palatalizacja: Stosuj regułę $k \to c$ oraz $k \to \check{c}$ zgodnie z przykładami w vuzor.json (np. rěka → rěcě, vojьsko → vojьscě w miejscowniku).Zgodność: Przymiotnik musi mieć ten sam rodzaj, liczbę i przypadek co rzeczownik, do którego się odnosi.III. KONTROLA KOŃCOWASprawdź, czy przymiotnik stoi przed rzeczownikiem.Sprawdź, czy w wyniku nie ma zakazanych liter cyrylicy lub twardego jera ъ.Upewnij się, że wielkość liter i interpunkcja są identyczne jak w tekście źródłowym.Wyjście: Zwróć wyłącznie czyste tłumaczenie. Nie dodawaj żadnych komentarzy, wyjaśnień ani dopisków.

        try:
            # Wywołanie modelu tłumaczenia
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"BAZA:\n{context_str}\n\nDO TŁUMACZENIA: {user_input}"}
                ],
                model="openai/gpt-oss-safeguard-20b",
                temperature=0.0
            )

            response_text = chat_completion.choices[0].message.content.strip()

            st.markdown("### Vynik perklada:")
            st.success(response_text)

            if matches:
                with st.expander("Užito žerdlo jiz osnovy"):
                    for m in matches:
                        st.write(f"**{m['polish']}** → `{m['slovian']}` ({m.get('type and case','')})")

        except Exception as e:
            st.error(f"Blǫd umětьnogo uma: {e}")










