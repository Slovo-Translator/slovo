import streamlit as st
from style import apply_custom_style, render_header
from logic import translate_text, get_languages

st.set_page_config(page_title="Tłumacz", layout="wide")
apply_custom_style()
LANGUAGES = get_languages()

# Inicjalizacja stanów
if "input_text" not in st.session_state: st.session_state.input_text = ""
if "translated_text" not in st.session_state: st.session_state.translated_text = ""
if "src_lang" not in st.session_state: st.session_state.src_lang = "pl"
if "tgt_lang" not in st.session_state: st.session_state.tgt_lang = "en"

def swap_langs():
    st.session_state.src_lang, st.session_state.tgt_lang = \
        st.session_state.tgt_lang, st.session_state.src_lang

render_header()

# RZĄD 1: Języki
c1, c2, c3 = st.columns([10, 1, 10])
with c1:
    st.selectbox("z", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="src_lang", label_visibility="collapsed")
with c2:
    st.markdown('<div class="swap-btn-container">', unsafe_allow_html=True)
    st.button("⇄", on_click=swap_langs, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.selectbox("na", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], key="tgt_lang", label_visibility="collapsed")

st.markdown('<div class="row-spacer"></div>', unsafe_allow_html=True)

# RZĄD 2: Przyciski Akcji
b1, b_mid, b2 = st.columns([10, 1, 10])
with b1:
    col_w1, col_w2 = st.columns([1, 1])
    with col_w1:
        st.button("📋 Wklej tekst")
    with col_w2:
        # GŁÓWNY PRZYCISK TŁUMACZENIA
        if st.button("🚀 TŁUMACZ", use_container_width=True):
            if st.session_state.input_text:
                with st.spinner('Tłumaczenie...'):
                    st.session_state.translated_text = translate_text(
                        st.session_state.input_text,
                        st.session_state.src_lang,
                        st.session_state.tgt_lang
                    )
            else:
                st.warning("Wpisz najpierw tekst!")

with b2:
    st.button("📋 Kopiuj wynik")

# RZĄD 3: Pola tekstowe
t1, _, t2 = st.columns([10, 1, 10])
with t1:
    st.session_state.input_text = st.text_area("in", value=st.session_state.input_text, height=250, label_visibility="collapsed", placeholder="Wpisz tekst...")

with t2:
    st.text_area("out", value=st.session_state.translated_text, height=250, label_visibility="collapsed", key="output_area")

st.markdown("---")
st.caption("Tłumacz gotowy do pracy.")
