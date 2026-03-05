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
    .stSuccess { background-color: #050505; border: 1px solid #2e7d32; color: #dcdcdc; font-size: 1.2rem; }
    .stCaption { color: #888; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. SILNIK TŁUMACZENIA (ARGOS TRANSLATE - BEZ LIMITÓW)
# ============================================================
@st.cache_resource
def init_translator(from_code="pl", to_code="en"):
    """Inicjalizacja darmowego silnika tłumaczeń bez API"""
    try:
        # Aktualizacja indeksu paczek
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Szukanie odpowiedniej paczki (np. polski -> angielski)
        package_to_install = next(
            filter(
                lambda x: x.from_code == from_code and x.to_code == to_code,
                available_packages
            ), None
        )
        
        if package_to_install:
            argostranslate.package.install_from_path(package_to_install.download())
        return True
    except Exception as e:
        st.error(f"Nie udało się zainstalować silnika tłumaczeń: {e}")
        return False

# Inicjalizacja (może chwilę potrwać przy pierwszym uruchomieniu)
translator_ready = init_translator("pl", "en")

# ============================================================
# 3. ŁADOWANIE BAZY DANYCH (RAG)
# ============================================================
@st.cache_data
def load_json_file(filename):
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Blǫd osnovy: {e}")
        return {}

data_osnova = load_json_file("osnova.json")
vuzor_data = load_json_file("vuzor.json")

# Indeksowanie słownika
dictionary = {}
if isinstance(data_osnova, list):
    for entry in data_osnova:
        pl = entry.get("polish", "").lower().strip()
        if pl:
            if pl not in dictionary: dictionary[pl] = []
            dictionary[pl].append(entry)

# ============================================================
# 4. LOGIKA TŁUMACZENIA I RAG
# ============================================================
def get_relevant_context(text, dic):
    search_text = re.sub(r'[^\w\s]', '', text.lower())
    words = search_text.split()
    relevant_entries = []
    for word in words:
        if word in dic:
            relevant_entries.extend(dic[word])
    return relevant_entries[:20]

def translate_logic(text):
    """
    Główna funkcja tłumacząca. 
    Najpierw szuka w Twoich plikach JSON (RAG), 
    a jeśli nie znajdzie, używa darmowego silnika Argos.
    """
    matches = get_relevant_context(text, dictionary)
    
    # Jeśli słowo jest w Twojej bazie osnova.json:
    if matches:
        # Priorytetowo traktujemy słowo z bazy (logika 1:1)
        return matches[0]['slovian'], matches
    
    # Jeśli słowa NIE MA w bazie, używamy Argos Translate (jako fallback)
    # Uwaga: Argos tłumaczy ogólnie, nie zna zasad prasłowiańskich 
    # bez Twojej bazy, więc służy jako "ratunek".
    try:
        translated = argostranslate.translate.translate(text, "pl", "en")
        return translated, []
    except:
        return "(ne najdeno slova)", []

# ============================================================
# 5. INTERFEJS UŻYTKOWNIKA
# ============================================================
st.title("Perkladačь slověnьskogo ęzyka")
st.caption("Darmowe tłumaczenie bez limitów (Argos Engine + Twoja Baza)")

user_input = st.text_input("Vupiši slovo alibo rěčenьje:", placeholder="")

if user_input:
    if not translator_ready:
        st.warning("Silnik tłumaczenia jest jeszcze konfigurowany... Czekaj.")
    else:
        with st.spinner("Przekładanie bez limitów..."):
            result, matches = translate_logic(user_input)
            
            st.markdown("### Vynik perklada:")
            st.success(result)
            
            if matches:
                with st.expander("Užito žerdlo jiz Twojej podstawy (osnova.json)"):
                    for m in matches:
                        st.write(f"**{m['polish']}** → `{m['slovian']}` ({m.get('type and case','')})")
            else:
                st.info("Słowo przetłumaczone przez silnik ogólny (brak w osnova.json).")

# ============================================================
# STOPKA
# ============================================================
st.divider()
st.caption("Aplikacja korzysta z lokalnego silnika Argos Translate. Brak opłat i limitów API.")
