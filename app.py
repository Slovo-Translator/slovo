import streamlit as st
import json
import os
import re

st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="wide")

# =========================
# STYL (biały jak DeepL)
# =========================

st.markdown("""
<style>

body {
background:white;
color:black;
}

textarea {
background:white !important;
color:black !important;
border:1px solid #ccc !important;
}

input {
background:white !important;
color:black !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# ŁADOWANIE JSON
# =========================

@st.cache_data
def load_json(file):

    if not os.path.exists(file):
        return {}

    try:
        with open(file, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# =========================
# ZAPIS DO MEMORY
# =========================

def save_memory(source, target):

    if os.path.exists("memory.json"):
        with open("memory.json", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data[source] = target

    with open("memory.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# ŁADOWANIE DANYCH
# =========================

osnova = load_json("osnova.json")
vuzor = load_json("vuzor.json")
memory = load_json("memory.json")

dictionary = {}

if isinstance(osnova, list):
    for item in osnova:
        if "polish" in item and "slovian" in item:
            dictionary[item["polish"].lower()] = item["slovian"]

dictionary.update(memory)

# =========================
# WIELKIE LITERY
# =========================

def match_case(source, target):

    if source.isupper():
        return target.upper()

    if source and source[0].isupper():
        return target.capitalize()

    return target

# =========================
# TOKENIZACJA
# =========================

def tokenize(text):
    return re.findall(r"\w+|[^\w\s]|\s+", text, re.UNICODE)

# =========================
# TŁUMACZENIE
# =========================

def translate(text):

    tokens = tokenize(text)
    result = []

    for token in tokens:

        word = token.lower()

        if word in dictionary:

            t = dictionary[word]
            t = match_case(token, t)

            result.append(t)

        else:
            result.append(token)

    return "".join(result)

# =========================
# INTERFEJS
# =========================

st.title("Perkladačь slověnьskogo ęzyka")

col1, col2 = st.columns(2)

with col1:
    source_lang = st.selectbox(
        "Język źródłowy",
        ["polski", "prasłowiański"]
    )

with col2:
    target_lang = st.selectbox(
        "Język docelowy",
        ["prasłowiański", "polski"]
    )

text = st.text_area("Tekst", height=200)

if st.button("Tłumacz"):
    translation = translate(text)
else:
    translation = ""

st.text_area("Tłumaczenie", translation, height=200)

# =========================
# POPRAWKI (HASŁO)
# =========================

st.markdown("---")

st.subheader("Popraw tłumaczenie (samouczenie)")

password = st.text_input("Hasło", type="password")

if password == "Rozeta*8":

    col1, col2 = st.columns(2)

    with col1:
        src = st.text_input("Słowo źródłowe")

    with col2:
        trg = st.text_input("Poprawne tłumaczenie")

    if st.button("Dodaj do bazy"):

        if src and trg:

            save_memory(src.lower(), trg)

            st.success("Dodano do pamięci")

else:

    if password != "":
        st.error("Błędne hasło")
