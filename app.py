import streamlit as st
import json
import os
import re
import argostranslate.package
import argostranslate.translate
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. KONFIGURACJA I STYLIZACJA
# ============================================================
st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextArea textarea { background-color: #1a1a1a; color: #dcdcdc; border: 1px solid #333; height: 200px !important; }
    .stSuccess { background-color: #050505; border: 1px solid #2e7d32; color: #dcdcdc; font-size: 1.2rem; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. SILNIK TŁUMACZĄCY (LOKALNY)
# ============================================================
@st.cache_resource
def setup_translator():
    try:
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next(filter(lambda x: x.from_code == 'pl' and x.to_code == 'en', available_packages), None)
        if package_to_install:
            argostranslate.package.install_from_path(package_to_install.download())
        return True
    except: return False

translator_ready = setup_translator()

# ============================================================
# 3. ŁADOWANIE BAZY (TWOJE PLIKI)
# ============================================================
@st.cache_data
def load_data():
    def read_json(fn):
        if not os.path.exists(fn): return []
        with open(fn, "r", encoding="utf-8") as f: return json.load(f)
    osnova = read_json("osnova.json")
    vuzor = read_json("vuzor.json")
    dic = {}
    for entry in osnova:
        pl = entry.get("polish", "").lower().strip()
        if pl:
            if pl not in dic: dic[pl] = []
            dic[pl].append(entry)
    return dic, vuzor

dictionary, vuzor_data = load_data()

# ============================================================
# 4. LOGIKA TRANSFORMACJI (RYGOR TWOICH ZASAD)
# ============================================================

def match_case(original, translated):
    if original.isupper(): return translated.upper()
    if original and original[0].isupper(): return translated.capitalize()
    return translated.lower()

def custom_translate(text):
    if not text: return "", []
    
    # Tokenizacja zachowująca interpunkcję i spacje
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    processed_tokens = []
    found_in_base = []

    for token in tokens:
        if re.match(r'\w+', token):
            clean = token.lower()
            # KROK 1: Twoja baza (Priorytet ABSOLUTNY)
            if clean in dictionary:
                entry = dictionary[clean][0]
                info = entry.get('type and case', '').lower()
                final_word = match_case(token, entry['slovian'])
                processed_tokens.append({'text': final_word, 'type': info, 'is_word': True})
                found_in_base.append(entry)
            else:
                # KROK 2: Zakaz angielskiego! Jeśli nie ma w bazie, zwróć błąd z promptu.
                missing_label = match_case(token, "(ne najdeno slova)")
                processed_tokens.append({'text': missing_label, 'type': 'unknown', 'is_word': True})
        else:
            # Zachowanie interpunkcji i znaków matematycznych
            processed_tokens.append({'text': token, 'type': 'separator', 'is_word': False})

    # KROK 3: Gramatyka - Przymiotnik przed Rzeczownik
    i = 0
    final_output = []
    while i < len(processed_tokens):
        current = processed_tokens[i]
        if current['is_word'] and "noun" in current['type']:
            next_word_idx = -1
            sep_idx = -1
            for j in range(i + 1, len(processed_tokens)):
                if processed_tokens[j]['is_word']:
                    next_word_idx = j
                    break
                else: sep_idx = j
            
            if next_word_idx != -1:
                nxt = processed_tokens[next_word_idx]
                if "adj" in nxt['type'] or "adjective" in nxt['type']:
                    final_output.append(nxt['text'])
                    if sep_idx != -1: final_output.append(processed_tokens[sep_idx]['text'])
                    final_output.append(current['text'])
                    i = next_word_idx + 1
                    continue
        final_output.append(current['text'])
        i += 1
    
    return "".join(final_output), found_in_base

# ============================================================
# 5. INTERFEJS UŻYTKOWNIKA (PRAWDZIWY LIVE)
# ============================================================
st.title("Perkladačь slověnьskogo ęzyka")

# Aby działało bez Entera, musimy wymusić odświeżanie formularza
if 'translation' not in st.session_state:
    st.session_state.translation = ""

# text_area z unikalnym kluczem i automatycznym wyzwalaniem
user_input = st.text_area(
    "Vupiši slovo alibo rěčenьje:", 
    height=200,
    placeholder="Pisz tutaj, przekład pojawi się pod spodem...",
    key="input_area"
)

# Kontener na wynik (zawsze widoczny, aktualizuje się natychmiast)
if user_input:
    result, matches = custom_translate(user_input)
    st.markdown("### Vynik perklada:")
    st.success(result)
    
    if matches:
        with st.expander("Užito žerdlo jiz Twojej podstawy (osnova.json)"):
            unique_matches = {m['slovian']: m for m in matches}.values()
            for m in unique_matches:
                st.write(f"**{m['polish']}** → `{m['slovian']}`")
else:
    st.info("Czekam na tekst do tłumaczenia...")
