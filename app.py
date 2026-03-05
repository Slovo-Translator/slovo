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
    .stTextInput > div > div > input { background-color: #1a1a1a; color: #dcdcdc; border: 1px solid #333; }
    .stSuccess { background-color: #050505; border: 1px solid #2e7d32; color: #dcdcdc; font-size: 1.2rem; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. INICJALIZACJA SILNIKA
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
# 3. ŁADOWANIE BAZY
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
# 4. LOGIKA TRANSFORMACJI
# ============================================================

def match_case(original, translated):
    if original.isupper(): return translated.upper()
    if original and original[0].isupper(): return translated.capitalize()
    return translated.lower()

def custom_translate(text):
    # Rozbijanie tekstu z zachowaniem separatorów (interpunkcja, spacje, znaki matematyczne)
    # \w+ to słowa, [^\w\s] to znaki interpunkcyjne/matematyczne, \s+ to białe znaki
    tokens = re.findall(r'\w+|[^\w\s]|\s+', text)
    
    processed_tokens = []
    found_in_base = []

    # Faza 1: Tłumaczenie słów, zachowanie reszty
    for token in tokens:
        # Jeśli token to słowo (litery/cyfry)
        if re.match(r'\w+', token):
            clean = token.lower()
            if clean in dictionary:
                entry = dictionary[clean][0]
                slov_word = entry['slovian']
                word_type = entry.get('type and case', '').lower()
                
                final_word = match_case(token, slov_word)
                processed_tokens.append({'text': final_word, 'type': word_type, 'is_word': True})
                found_in_base.append(entry)
            else:
                # Fallback do Argos dla słów, których nie ma w bazie
                try:
                    translated = argostranslate.translate.translate(token, 'pl', 'en')
                    processed_tokens.append({'text': match_case(token, translated), 'type': 'unknown', 'is_word': True})
                except:
                    processed_tokens.append({'text': token, 'type': 'unknown', 'is_word': True})
        else:
            # Jeśli token to interpunkcja, spacja lub znak matematyczny - zostawiamy jak jest
            processed_tokens.append({'text': token, 'type': 'separator', 'is_word': False})

    # Faza 2: Logika gramatyczna (Przymiotnik przed Rzeczownik)
    # Przeszukujemy tylko tokeny będące słowami, ignorując separatory między nimi
    i = 0
    final_result = []
    
    while i < len(processed_tokens):
        current = processed_tokens[i]
        
        # Próba znalezienia pary Rzeczownik + (opcjonalny separator) + Przymiotnik
        if current['is_word'] and "noun" in current['type']:
            next_word_idx = -1
            separator_idx = -1
            
            # Szukaj następnego słowa, pomijając ewentualne spacje/interpunkcję
            for j in range(i + 1, len(processed_tokens)):
                if processed_tokens[j]['is_word']:
                    next_word_idx = j
                    break
                else:
                    separator_idx = j # Zapamiętaj separator między słowami
            
            if next_word_idx != -1:
                next_word = processed_tokens[next_word_idx]
                if "adj" in next_word['type']:
                    # Zamiana: Przymiotnik + Separator + Rzeczownik
                    final_result.append(next_word['text'])
                    if separator_idx != -1:
                        final_result.append(processed_tokens[separator_idx]['text'])
                    final_result.append(current['text'])
                    i = next_word_idx + 1
                    continue
        
        final_result.append(current['text'])
        i += 1
    
    return "".join(final_result), found_in_base

# ============================================================
# 5. INTERFEJS
# ============================================================
st.title("Perkladačь slověnьskogo ęzyka")
st.caption("Lokalny przekład: zachowanie interpunkcji, spacji i znaków matematycznych")

user_input = st.text_area("Vupiši tekst:", placeholder="np. Wojsko Słowiańskie + Wojsko Polskie = ?", height=150)

if user_input:
    if not translator_ready:
        st.info("Inicjalizacja silnika...")
    else:
        with st.spinner("Przetwarzanie..."):
            result, matches = custom_translate(user_input)
            
            st.markdown("### Vynik perklada:")
            st.success(result)
            
            if matches:
                with st.expander("Užito jiz Twojej podstawy"):
                    # Usuwanie duplikatów w wyświetlaniu źródła
                    unique_matches = {m['slovian']: m for m in matches}.values()
                    for m in unique_matches:
                        st.write(f"**{m['polish']}** → `{m['slovian']}` ({m.get('type and case','')})")
