/**
 * SLOVO TRANSLATOR ENGINE v5.2
 * Naprawione błędy: undefined UI, domyślne języki, szyk frazy nominalnej.
 */

let plToSlo = {}, sloToPl = {};
let dictionaryData = [];

const languageData = [
    { code: 'slo', pl: 'Słowiański', en: 'Slovian (Slavic)', slo: 'Slověnьsky' },
    { code: 'pl', pl: 'Polski', en: 'Polish', slo: "Pol'ьsky" },
    { code: 'en', pl: 'Angielski', en: 'English', slo: "Angol'ьsky" },
    { code: 'de', pl: 'Niemiecki', en: 'German', slo: 'Nemьčьsky' },
    { code: 'ru', pl: 'Rosyjski', en: 'Russian', slo: 'Rusьsky' },
    { code: 'cs', pl: 'Czeski', en: 'Czech', slo: 'Češьsky' },
    { code: 'sk', pl: 'Słowacki', en: 'Slovak', slo: 'Slovačьsky' },
    { code: 'uk', pl: 'Ukraiński', en: 'Ukrainian', slo: 'Ukrajinьsky' }
];

const uiTranslations = {
    slo: { title: "Slovo Perkladačь", from: "Jiz ęzyka:", to: "Na ęzyk:", paste: "Vyloži", clear: "Terbi", copy: "Poveli", placeholder: "Piši tu..." },
    pl: { title: "Slovo Tłumacz", from: "Z języka:", to: "Na język:", paste: "Wklej", clear: "Usuń", copy: "Kopiuj", placeholder: "Wpisz tekst..." },
    en: { title: "Slovo Translator", from: "From language:", to: "To language:", paste: "Paste", clear: "Clear", copy: "Copy", placeholder: "Type here..." }
};

// --- LOGIKA SORTOWANIA (SZYK ROSYJSKI) ---

function findType(word) {
    const clean = word.toLowerCase().replace(/[.!?,\s'‘’\u0300-\u036f]/g, '');
    if (!clean) return 99;

    const entry = dictionaryData.find(d => d.slovian && d.slovian.toLowerCase() === clean);
    
    if (entry && entry['type and case']) {
        const t = entry['type and case'].toLowerCase();
        if (t.includes('pronoun')) return 0;   // Mojь
        if (t.includes('numeral')) return 1;   // pirvy
        if (t.includes('adjective')) return 2; // moskal'ьsky
        if (t.includes('noun')) return 3;      // ęzyk
    }
    return 99;
}

function smartReorder(text) {
    return text.split(/([.!?\n]+)/).map(segment => {
        if (/^[.!?\n]+$/.test(segment) || !segment.trim()) return segment;

        const tokens = segment.split(/(\s+)/);
        let result = [];

        for (let i = 0; i < tokens.length; i++) {
            let token = tokens[i];
            let weight = /[a-ząćęłńóśźżěьъǫ\u0300-\u036f]+/i.test(token) ? findType(token) : 100;

            if (weight <= 3) {
                let group = [];
                while (i < tokens.length) {
                    let t = tokens[i];
                    let w = /[a-ząćęłńóśźżěьъǫ\u0300-\u036f]+/i.test(t) ? findType(t) : 100;

                    if (w <= 3 || (t.trim() === "" && group.length > 0)) {
                        if (/[a-ząćęłńóśźżěьъǫ\u0300-\u036f]+/i.test(t)) {
                            group.push({ text: t, weight: w });
                        }
                        i++;
                    } else break;
                }
                group.sort((a, b) => a.weight - b.weight);
                result.push(group.map(g => g.text).join(' '));
                i--; 
            } else {
                result.push(token);
            }
        }
        return result.join('');
    }).join('');
}

// --- TŁUMACZENIE I SŁOWNIK ---

function dictReplace(text, dict) {
    return text.replace(/[a-ząćęłńóśźżěьъǫ\u0300-\u036f'‘’]+/gi, (m) => {
        const low = m.toLowerCase();
        if (dict[low]) {
            const r = dict[low];
            if (m === m.toUpperCase()) return r.toUpperCase();
            if (m[0] === m[0].toUpperCase()) return r.charAt(0).toUpperCase() + r.slice(1);
            return r;
        }
        return m;
    });
}

async function translate() {
    const input = document.getElementById('userInput');
    const out = document.getElementById('resultOutput');
    const src = document.getElementById('srcLang').value;
    const tgt = document.getElementById('tgtLang').value;
    const text = input.value.trim();

    if (!text) { out.innerText = ""; return; }

    try {
        let res = "";
        if (src === 'pl' && tgt === 'slo') {
            res = smartReorder(dictReplace(text, plToSlo));
        } else if (src === 'slo' && tgt === 'pl') {
            res = dictReplace(text, sloToPl);
        } else if (tgt === 'slo') {
            const bridge = await google(text, src, 'pl');
            res = smartReorder(dictReplace(bridge, plToSlo));
        } else if (src === 'slo') {
            const bridge = dictReplace(text, sloToPl);
            res = await google(bridge, 'pl', tgt);
        } else {
            res = await google(text, src, tgt);
        }
        out.innerText = res;
    } catch (e) { out.innerText = "Error..."; }
}

async function google(text, s, t) {
    try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${s}&tl=${t}&dt=t&q=${encodeURIComponent(text)}`;
        const res = await fetch(url);
        const data = await res.json();
        return data[0].map(x => x[0]).join('');
    } catch (e) { return text; }
}

// --- SYSTEM I INTERFEJS ---

async function loadDictionaries() {
    const status = document.getElementById('dbStatus');
    try {
        const files = ['osnova.json', 'vuzor.json'];
        for (const file of files) {
            const res = await fetch(file);
            if (res.ok) {
                const data = await res.json();
                dictionaryData = [...dictionaryData, ...data];
                data.forEach(item => {
                    if (item.polish && item.slovian) {
                        plToSlo[item.polish.toLowerCase().trim()] = item.slovian.trim();
                        sloToPl[item.slovian.toLowerCase().trim()] = item.polish.trim();
                    }
                });
            }
        }
        if(status) status.innerText = "Slovo Engine v5.2 Ready.";
    } catch (e) { if(status) status.innerText = "Dict Error."; }
}

function applyUI(lang) {
    const ui = uiTranslations[lang] || uiTranslations.en;
    const map = {
        'ui-title': ui.title,
        'ui-label-from': ui.from,
        'ui-label-to': ui.to,
        'ui-paste': ui.paste,
        'ui-clear': ui.clear,
        'ui-copy': ui.copy
    };
    Object.keys(map).forEach(id => {
        const el = document.getElementById(id);
        if(el) el.innerText = map[id];
    });
    const input = document.getElementById('userInput');
    if(input) input.placeholder = ui.placeholder;
}

function populateLanguageLists(uiLang) {
    const srcSelect = document.getElementById('srcLang');
    const tgtSelect = document.getElementById('tgtLang');
    if(!srcSelect || !tgtSelect) return;
    srcSelect.innerHTML = "";
    tgtSelect.innerHTML = "";
    languageData.forEach(lang => {
        const name = lang[uiLang] || lang.en || lang.pl;
        srcSelect.add(new Option(name, lang.code));
        tgtSelect.add(new Option(name, lang.code));
    });
}

async function init() {
    const sysLang = navigator.language.split('-')[0];
    const uiKey = uiTranslations[sysLang] ? sysLang : 'en';
    
    populateLanguageLists(uiKey);
    applyUI(uiKey);

    // Domyślne języki: jeśli PL to pl->slo, jeśli inne to en->slo
    const defaultSrc = sysLang === 'pl' ? 'pl' : 'en';
    document.getElementById('srcLang').value = localStorage.getItem('srcLang') || defaultSrc;
    document.getElementById('tgtLang').value = localStorage.getItem('tgtLang') || 'slo';

    await loadDictionaries();

    const input = document.getElementById('userInput');
    if(input) input.addEventListener('input', debounce(translate, 400));
    
    document.getElementById('srcLang').onchange = (e) => { localStorage.setItem('srcLang', e.target.value); translate(); };
    document.getElementById('tgtLang').onchange = (e) => { localStorage.setItem('tgtLang', e.target.value); translate(); };
}

// --- FUNKCJE POMOCNICZE ---

function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), wait);
    };
}

function swapLanguages() {
    const src = document.getElementById('srcLang');
    const tgt = document.getElementById('tgtLang');
    const tmp = src.value;
    src.value = tgt.value;
    tgt.value = tmp;
    localStorage.setItem('srcLang', src.value);
    localStorage.setItem('tgtLang', tgt.value);
    translate();
}

function clearText() {
    document.getElementById('userInput').value = "";
    document.getElementById('resultOutput').innerText = "";
}

function copyText() {
    const out = document.getElementById('resultOutput').innerText;
    if(out) navigator.clipboard.writeText(out);
}

async function pasteText() {
    try {
        const text = await navigator.clipboard.readText();
        const input = document.getElementById('userInput');
        if(input) { input.value = text; translate(); }
    } catch(e) {}
}

window.onload = init;
