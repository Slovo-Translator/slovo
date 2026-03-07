import streamlit as st
import json
import os
import re
from collections import defaultdict

st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")

st.markdown("""
<style>
.main {background:#0e1117}
.stTextArea textarea {background:#1a1a1a;color:#dcdcdc}
</style>
""", unsafe_allow_html=True)


# ================== ŁADOWANIE ==================

@st.cache_data
def load_json(filename):

    if not os.path.exists(filename):
        return []

    with open(filename,"r",encoding="utf-8") as f:
        return json.load(f)


osnova = load_json("osnova.json")
vuzor  = load_json("vuzor.json")


# ================== SŁOWNIK ==================

@st.cache_data
def build_dictionary(data):

    dic = defaultdict(list)

    for entry in data:

        key = entry.get("polish","").lower().strip()

        if key:
            dic[key].append(entry)

    return dic


dictionary = build_dictionary(osnova)


# ================== TOKENIZACJA ==================

def tokenize(text):

    tokens = re.findall(r'\w+|[^\w\s]', text, re.UNICODE)
    return tokens


# ================== ZACHOWANIE WIELKOŚCI LITER ==================

def match_case(original, translated):

    if original.isupper():
        return translated.upper()

    if original[0].isupper():
        return translated.capitalize()

    return translated


# ================== TŁUMACZENIE SŁOWA ==================

def translate_word(word):

    key = word.lower()

    if key in dictionary:

        entry = dictionary[key][0]

        slov = entry.get("slovian","")

        return match_case(word, slov)

    return "(ne najdeno slova)"


# ================== TŁUMACZENIE TEKSTU ==================

def translate_text(text):

    tokens = tokenize(text)

    output = []

    for t in tokens:

        if re.match(r'\w+', t):

            output.append(translate_word(t))

        else:
            output.append(t)

    return " ".join(output)\
        .replace(" ,",",")\
        .replace(" .",".")\
        .replace(" !","!")\
        .replace(" ?","?")


# ================== INTERFEJS ==================

st.title("Perkladačь slověnьskogo ęzyka")

user_input = st.text_area(
    "Vupiši slovo alibo rěčenьje:",
    placeholder="Np. W miastach siła.",
    height=150
)

if user_input:

    with st.spinner("Przetwarzanie..."):

        result = translate_text(user_input)

        st.markdown("### Vynik perklada:")
        st.success(result)
