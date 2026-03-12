import streamlit as st
import json
import os
import re

st.set_page_config(page_title="Perkladačь slověnьskogo ęzyka", layout="wide", page_icon="🌾")

if "theme" not in st.session_state: st.session_state.theme = "dark"
if "output" not in st.session_state: st.session_state.output = ""

def get_css(theme):
    if theme == "dark":
        return """<style>
.main {background:#0a0f1c;}
.stTextArea textarea {background:#111827 !important;color:#e2e8f0 !important;font-size:1.15rem;border-radius:16px;border:1px solid #334155;}
.translate-btn {background:linear-gradient(90deg,#2563eb,#1e40af);color:white;font-size:1.35rem;font-weight:700;padding:18px;border-radius:50px;border:none;width:100%;margin:12px 0;box-shadow:0 10px 30px rgba(37,99,235,0.4);}
.translate-btn:hover {background:linear-gradient(90deg,#3b82f6,#2563eb);}
h1 {color:#93c5fd;font-weight:700;}
</style>"""
    else:
        return """<style>
.main {background:#f8fafd;}
.stTextArea textarea {background:#ffffff !important;color:#0f172a !important;font-size:1.15rem;border-radius:16px;border:1px solid #94a3b8;}
.translate-btn {background:linear-gradient(90deg,#2563eb,#1e40af);color:white;font-size:1.35rem;font-weight:700;padding:18px;border-radius:50px;border:none;width:100%;margin:12px 0;}
.translate-btn:hover {background:linear-gradient(90deg,#3b82f6,#2563eb);}
h1 {color:#1e3a8a;font-weight:700;}
</style>"""

st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not os.path.exists("osnova.json"): return {}, {}
    data = json.load(open("osnova.json", encoding="utf-8"))
    pl_sl = {e["polish"].strip().lower(): e["slovian"].strip() for e in data if e.get("polish") and e.get("slovian")}
    return pl_sl, {v.lower(): k for k, v in pl_sl.items()}

pl_to_sl, sl_to_pl = load_data()

def translate(text, direction):
    if not text.strip(): return ""
    dic = pl_to_sl if direction == "pl→sl" else sl_to_pl
    def repl(m):
        w = m.group(0)
        lower = w.lower()
        t = dic.get(lower, w)
        if w.isupper(): return t.upper()
        if w and w[0].isupper(): return t.capitalize()
        return t
    return re.sub(r'\b\w+\b', repl, text)

col_t, col_th = st.columns([4,1])
with col_t: st.title("Perkladačь slověnьskogo ęzyka")
with col_th:
    if st.button("☀️" if st.session_state.theme == "dark" else "🌙", key="th"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

col1, colm, col2 = st.columns([5,1.1,5])

with col1:
    src = st.selectbox("Z:", ["Polski", "Prasłowiański"], key="src")
    txt = st.text_area("Tekst źródłowy", height=440, placeholder="Wpisz tekst...", key="in")

with colm:
    st.write(""); st.write(""); st.write("")
    if st.button("⇄", key="sw", use_container_width=True):
        st.session_state.in, st.session_state.output = st.session_state.get("output",""), st.session_state.get("in","")
        st.session_state.src = "Prasłowiański" if src == "Polski" else "Polski"
        st.rerun()

with col2:
    tgt = "Prasłowiański" if src == "Polski" else "Polski"
    st.selectbox("Na:", [tgt], disabled=True)
    st.text_area("Tłumaczenie", value=st.session_state.output, height=440, disabled=True)

if st.button("**Przełóż**", type="primary", use_container_width=True):
    if txt.strip():
        d = "pl→sl" if src == "Polski" else "sl→pl"
        st.session_state.output = translate(txt, d)
        st.rerun()

st.caption("Dla innych języków najpierw przetłumacz na polski (pośrednik zawsze polski)")
