import streamlit as st
import json
import os
import re
from groq import Groq

st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="centered")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextArea > div > div > textarea { background-color: #1a1a1a; color: #dcdcdc; border: 1px solid #333; }
    .stSuccess { background-color: #050505; border: 1px solid #2e7d32; color: #dcdcdc; font-size: 1.2rem; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

@st.cache_data
def load_json(filename):
    if not os.path.exists(filename): return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

osnova = load_json("osnova.json")
dictionary = {}
for entry in osnova:
    pl = entry.get("polish", "").lower().strip()
    if pl:
        if pl not in dictionary: dictionary[pl] = []
        dictionary[pl].append(entry)

DECLENSION_RULES = """
=== DOKŁADNE WZORY ===
ludzie (ljudьje) – męski animate, loc pl: ljudih
W ludziach = vu ljudih

nadzieja → naděja (żeński, loc sg: naději ale tutaj nom: naděja)

jest → estь
w → vu (przyimek + loc)
"""

def get_context(text, dic):
    words = re.findall(r'\w+', text.lower())
    entries = []
    endings = ['ie','u','em','ach','om','ami','ów','a','y','i','ego','emu','ej','ą','e','iach','dziach']
    for w in words:
        if w in dic:
            entries.extend(dic[w])
            continue
        for end in endings:
            if w.endswith(end) and len(w) > len(end)+2:
                stem = w[:-len(end)]
                if stem in dic:
                    entries.extend(dic[stem])
                    break
        if any(x in w for x in ['ludz','ludzi','ludzie']) and 'ludzie' in dic:
            entries.extend(dic['ludzie'])
        if 'nadziej' in w and 'nadzieja' in dic:
            entries.extend(dic['nadzieja'])
    seen = {(e['polish'].lower(), e['slovian'].lower()) for e in entries}
    return [e for e in entries if (e['polish'].lower(), e['slovian'].lower()) in seen]

st.title("Perkladačь slověnьskogo ęzyka")
user_input = st.text_area("Vupiši slovo alibo rěčenьje:", placeholder="Np. W ludziach jest nadzieja.", height=150)

if user_input:
    with st.spinner("Przetwarzanie..."):
        matches = get_context(user_input, dictionary)
        mapping = "\n".join([f"PL '{m['polish']}' → SL '{m['slovian']}'" for m in matches])

        system_prompt = f"""
Jesteś precyzyjnym tłumaczem na prasłowiański.
Używaj TYLKO tych form:

WZORY:
{DECLENSION_RULES}

ALGORYTM:
1. Rozpoznaj "w" + loc → vu + loc
2. "ludziach" → ljudih
3. "jest" → estь
4. "nadzieja" → naděja

DANE:
{mapping}

Tylko czysty wynik. Bez komentarzy.
"""

        try:
            chat = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Przetłumacz: {user_input}"}
                ],
                temperature=0.0,
                max_tokens=1024
            )
            result = chat.choices[0].message.content.strip()
            st.markdown("### Vynik perklada:")
            st.success(result)
        except Exception as e:
            st.error(f"Błąd: {e}")

        if matches:
            with st.expander("Użyte mapowanie z bazy"):
                for m in matches:
                    st.write(f"'{m['polish']}' → `{m['slovian']}`")
