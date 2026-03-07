import streamlit as st
import json
import os
import re
from groq import Groq

# ================== 1. KONFIGURACJA SYSTEMU ==================
st.set_page_config(page_title="Ekspercki Perkladačь (Hoenir Engine)", layout="wide")

# Mapowanie ortograficzne dla zapewnienia czystości słowiańskiej formy
def clear_orthography(text):
    mapping = {'ą': 'ę', 'ć': 'ć', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'}
    for pl, sl in mapping.items():
        text = text.replace(pl, sl)
    return text

# ================== 2. POŁĄCZENIE Z MOZGIEM AI ==================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("Błąd: Skonfiguruj GROQ_API_KEY w Streamlit Secrets.")
    st.stop()

# ================== 3. ZASOBY DANYCH (OSNOVA & VUZOR) ==================
@st.cache_data
def load_machine_data():
    def get_data(file):
        if not os.path.exists(file): return []
        with open(file, "r", encoding="utf-8") as f:
            return [obj for obj in json.load(f) if isinstance(obj, dict)]
    return get_data("osnova.json"), get_data("vuzor.json")

osnova_db, vuzor_db = load_machine_data()

# ================== 4. SILNIK TŁUMACZENIA MASZYNOWEGO ==================

def hoenir_translate_engine(polish_text):
    # KROK 1: Lingwistyczna dekompozycja zdania (LLM Analysis)
    # Model AI rozpoznaje przypadki, liczby i rodzaje
    analysis_prompt = f"""Analyze the Polish sentence. 
Return ONLY lines in format: original_word | case | number | gender
Use tags: nominative, genitive, dative, accusative, instrumental, locative, vocative.
Number: singular, plural. Gender: masculine, feminine, neuter.

Sentence: {polish_text}"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0 # Blokada kreatywności na rzecz precyzji
        )
        morphology = completion.choices[0].message.content.strip().split('\n')
    except Exception as e:
        return f"Błąd ML: {e}", []

    translated_chain = []
    process_logs = []

    # KROK 2: Fizyczne mapowanie na tabele (Database Retrieval)
    for entry in morphology:
        if "|" not in entry: continue
        parts = [p.strip().lower() for p in entry.split('|')]
        if len(parts) < 3: continue
        
        pl_word = re.sub(r'[^\w\s]', '', parts[0])
        req_case, req_num = parts[1], parts[2]

        # Wyszukiwanie rdzenia w osnova.json
        base_slovian = next((item['slovian'] for item in osnova_db if item.get('polish', '').lower() == pl_word), None)
        
        if base_slovian:
            # Wyszukiwanie precyzyjnej formy w vuzor.json
            found_form = None
            for pattern in vuzor_db:
                v_case_info = pattern.get("type and case", "").lower()
                v_word = pattern.get("slovian", "")
                
                # Warunek: Rdzeń musi być powiązany z wzorem, a gramatyka musi się zgadzać
                if (f"'{base_slovian}'" in v_case_info or base_slovian == v_word) and \
                   req_case in v_case_info and req_num in v_case_info:
                    found_form = v_word
                    break
            
            if found_form:
                clean_word = clear_orthography(found_form)
                translated_chain.append(clean_word)
                process_logs.append(f"MAP: {pl_word} -> {clean_word} [{req_case}, {req_num}]")
            else:
                translated_chain.append(f"{clear_orthography(base_slovian)}?")
                process_logs.append(f"MISS: Brak formy '{base_slovian}' dla {req_case} {req_num}")
        else:
            # Obsługa słów statycznych (przyimki itp.)
            static_map = {"w": "vu", "na": "na", "z": "iz", "i": "i", "siła": "sila"}
            token = static_map.get(pl_word, clear_orthography(pl_word))
            translated_chain.append(token)
            process_logs.append(f"STATIC: {pl_word} -> {token}")

    return " ".join(translated_chain).capitalize(), process_logs

# ================== 5. INTERFEJS UŻYTKOWNIKA (UX) ==================

st.title("🏛️ Perkladačь slověnьskogo ęzyka")
st.markdown("#### System Hoenir: Analiza ML + Mapowanie Tablicowe")

user_sentence = st.text_input("Vupiši slovo alibo rěčenьje (PL):", value="W Słowianach siła.")

if user_sentence:
    with st.spinner("Uruchamianie silnika morfologicznego..."):
        output, logs = hoenir_translate_engine(user_sentence)
        
        st.write("### Vynik perklada:")
        st.success(output)
        
        with st.expander("Logi procesowe (Uczenie maszynowe i mapowanie)"):
            for log in logs:
                st.code(log)

st.divider()
st.caption(f"Status bazy: {len(osnova_db)} słów | {len(vuzor_db)} form odmiany. Tryb: Machine Learning.")
