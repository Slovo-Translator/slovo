<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slovo Translator</title>
    <style>
        :root {
            --primary: #2c3e50;
            --accent: #3498db;
            --bg: #f4f7f6;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 800px; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: var(--primary); margin-bottom: 25px; }
        .controls { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        select { padding: 10px; border-radius: 6px; border: 1px solid #ddd; flex: 1; min-width: 150px; }
        .swap-btn { background: var(--accent); color: white; border: none; padding: 10px 15px; border-radius: 50%; cursor: pointer; font-weight: bold; }
        .text-areas { display: grid; grid-template-columns: 1fr; gap: 20px; }
        textarea { width: 100%; height: 150px; padding: 15px; border-radius: 8px; border: 1px solid #eee; resize: none; font-size: 16px; box-sizing: border-box; }
        #resultOutput { min-height: 150px; padding: 15px; background: #f9f9f9; border-radius: 8px; border: 1px solid #eee; white-space: pre-wrap; font-size: 16px; }
        .button-group { margin-top: 15px; display: flex; gap: 10px; }
        button.action { flex: 1; padding: 10px; border: none; border-radius: 6px; cursor: pointer; background: #ecf0f1; transition: 0.3s; }
        button.action:hover { background: #dfe6e9; }
        #dbStatus { font-size: 12px; text-align: center; margin-top: 20px; color: #95a5a6; }
    </style>
</head>
<body>

<div class="container">
    <h1 id="ui-title">Slovo Translator</h1>
    
    <div class="controls">
        <div style="flex: 1;">
            <label id="ui-label-from" style="display:block; font-size: 12px; margin-bottom: 5px;">Z języka:</label>
            <select id="srcLang"></select>
        </div>
        
        <button class="swap-btn" onclick="swapLanguages()">⇄</button>
        
        <div style="flex: 1;">
            <label id="ui-label-to" style="display:block; font-size: 12px; margin-bottom: 5px;">Na język:</label>
            <select id="tgtLang"></select>
        </div>
    </div>

    <div class="text-areas">
        <div>
            <textarea id="userInput" placeholder="Wpisz tekst..."></textarea>
            <div class="button-group">
                <button class="action" id="ui-paste" onclick="pasteText()">Wklej</button>
                <button class="action" id="ui-clear" onclick="clearText()">Usuń</button>
            </div>
        </div>
        <div>
            <div id="resultOutput"></div>
            <div class="button-group">
                <button class="action" id="ui-copy" onclick="copyText()">Kopiuj</button>
            </div>
        </div>
    </div>

    <div id="dbStatus">Ładowanie silnika...</div>
</div>

<script>
/**
 * Logika sortowania słów: numeral -> adjective -> noun
 */
let plToSlo = {}, sloToPl = {};
let dictionaryData = []; // Baza do sprawdzania typów części mowy

const weights = { 'numeral': 1, 'adjective': 2, 'noun': 3 };

function orderSlovianPhrase(words) {
    return [...words].sort((a, b) => {
        const typeA = (a.type || '').toLowerCase();
        const typeB = (b.type || '').toLowerCase();
        return (weights[typeA] || 99) - (weights[typeB] || 99);
    });
}

const languageData = [
    { code: 'slo', pl: 'Słowiański', en: 'Slovian (Slavic)', slo: 'Slověnьsky', de: 'Slawisch' },
    { code: 'pl', pl: 'Polski', en: 'Polish', slo: "Pol'ьsky", de: 'Polnisch' },
    { code: 'en', pl: 'Angielski', en: 'English', slo: "Angol'ьsky", de: 'Englisch' },
    { code: 'de', pl: 'Niemiecki', en: 'German', slo: 'Nemьčьsky', de: 'Deutsch' },
    { code: 'cs', pl: 'Czeski', en: 'Czech', slo: 'Češьsky', de: 'Tschechisch' },
    { code: 'sk', pl: 'Słowacki', en: 'Slovak', slo: 'Slovačьsky', de: 'Slowakisch' },
    { code: 'ru', pl: 'Rosyjski', en: 'Russian', slo: 'Rusьsky', de: 'Russisch' },
    { code: 'fr', pl: 'Francuski', en: 'French', slo: 'Franьsky', de: 'Französisch' },
    { code: 'es', pl: 'Hiszpański', en: 'Spanish', slo: 'Španьsky', de: 'Spanisch' },
    { code: 'it', pl: 'Włoski', en: 'Italian', slo: 'Volšьsky', de: 'Italienisch' },
    { code: 'uk', pl: 'Ukraiński', en: 'Ukrainian', slo: 'Ukrajinьsky', de: 'Ukrainisch' },
    { code: 'zh-CN', pl: 'Chiński (upraszczony)', en: 'Chinese (Simplified)', slo: 'Kitajьsky (Uproščeny)', de: 'Chinesisch' }
];

const uiTranslations = {
    slo: { title: "Slovo Perkladačь", from: "Jiz ęzyka:", to: "Na ęzyk:", paste: "Vyloži", clear: "Terbi", copy: "Poveli", placeholder: "Piši tu..." },
    pl: { title: "Slovo Tłumacz", from: "Z języka:", to: "Na język:", paste: "Wklej", clear: "Usuń", copy: "Kopiuj", placeholder: "Wpisz tekst..." },
    en: { title: "Slovo Translator", from: "From language:", to: "To language:", paste: "Paste", clear: "Clear", copy: "Copy", placeholder: "Type here..." },
    de: { title: "Slovo Übersetzer", from: "Von:", to: "Nach:", paste: "Einfügen", clear: "Löschen", copy: "Kopieren", placeholder: "Text eingeben..." }
};

function dictReplace(text, dict) {
    // Regex uwzględniający szeroką gamę znaków słowiańskich
    return text.replace(/[a-ząćęłńóśźżěьъǫ\u0300-\u036f]+/gi, (m) => {
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

function smartReorder(text) {
    // Rozbijamy tekst na zdania/segmenty, by nie mieszać całego tekstu naraz
    return text.split(/([.!?\s,]+)/).map(segment => {
        if (/^[.!?\s,]+$/.test(segment) || segment.trim() === "") return segment;
        
        const wordsInSegment = segment.split(' ').filter(w => w.length > 0);
        if (wordsInSegment.length < 2) return segment;

        const mappedWords = wordsInSegment.map(w => {
            const low = w.toLowerCase();
            const entry = dictionaryData.find(d => d.slovian && d.slovian.toLowerCase() === low);
            let type = 'unknown';
            if (entry && entry['type and case']) {
                type = entry['type and case'].split(' - ')[0].trim().toLowerCase();
            }
            return { original: w, type: type };
        });

        return orderSlovianPhrase(mappedWords).map(obj => obj.original).join(' ');
    }).join('');
}

async function translate() {
    const text = document.getElementById('userInput').value.trim();
    const src = document.getElementById('srcLang').value;
    const tgt = document.getElementById('tgtLang').value;
    const out = document.getElementById('resultOutput');
    
    if (!text) { out.innerText = ""; return; }

    try {
        let finalResult = "";
        if (src === 'slo' && tgt === 'pl') {
            finalResult = dictReplace(text, sloToPl);
        } else if (src === 'pl' && tgt === 'slo') {
            let temp = dictReplace(text, plToSlo);
            finalResult = smartReorder(temp);
        } else if (src === 'slo') {
            const bridge = dictReplace(text, sloToPl);
            finalResult = await google(bridge, 'pl', tgt);
        } else if (tgt === 'slo') {
            const bridge = await google(text, src, 'pl');
            let temp = dictReplace(bridge, plToSlo);
            finalResult = smartReorder(temp);
        } else {
            finalResult = await google(text, src, tgt);
        }
        out.innerText = finalResult || "";
    } catch (e) { out.innerText = "Translation error..."; }
}

async function google(text, s, t) {
    try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${s}&tl=${t}&dt=t&q=${encodeURIComponent(text)}`;
        const res = await fetch(url);
        const data = await res.json();
        return data[0].map(x => x[0]).join('');
    } catch (e) { return text; }
}

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
        status.innerText = "Engine Ready.";
    } catch (e) { status.innerText = "Dict Error. Check JSON files."; }
}

async function init() {
    const sysLang = navigator.language.split('-')[0];
    const uiKey = uiTranslations[sysLang] ? sysLang : 'en';
    applyUI(uiKey);
    populateLanguageLists(uiKey);
    
    document.getElementById('srcLang').value = localStorage.getItem('srcLang') || (sysLang === 'pl' ? 'pl' : 'en');
    document.getElementById('tgtLang').value = localStorage.getItem('tgtLang') || 'slo';
    
    await loadDictionaries();
    
    document.getElementById('userInput').addEventListener('input', debounce(() => translate(), 300));
    document.getElementById('srcLang').onchange = (e) => { localStorage.setItem('srcLang', e.target.value); translate(); };
    document.getElementById('tgtLang').onchange = (e) => { localStorage.setItem('tgtLang', e.target.value); translate(); };
}

function applyUI(lang) {
    const ui = uiTranslations[lang] || uiTranslations.en;
    document.getElementById('ui-title').innerText = ui.title;
    document.getElementById('ui-label-from').innerText = ui.from;
    document.getElementById('ui-label-to').innerText = ui.to;
    document.getElementById('ui-paste').innerText = ui.paste;
    document.getElementById('ui-clear').innerText = ui.clear;
    document.getElementById('ui-copy').innerText = ui.copy;
    document.getElementById('userInput').placeholder = ui.placeholder;
}

function populateLanguageLists(uiLang) {
    const srcSelect = document.getElementById('srcLang');
    const tgtSelect = document.getElementById('tgtLang');
    languageData.forEach(lang => {
        const name = lang[uiLang] || lang.en;
        srcSelect.add(new Option(name, lang.code));
        tgtSelect.add(new Option(name, lang.code));
    });
}

function swapLanguages() {
    const src = document.getElementById('srcLang');
    const tgt = document.getElementById('tgtLang');
    [src.value, tgt.value] = [tgt.value, src.value];
    localStorage.setItem('srcLang', src.value);
    localStorage.setItem('tgtLang', tgt.value);
    translate();
}

async function pasteText() {
    try {
        const text = await navigator.clipboard.readText();
        document.getElementById('userInput').value = text;
        translate();
    } catch(e) { alert("Clipboard access denied."); }
}

function copyText() {
    const text = document.getElementById('resultOutput').innerText;
    navigator.clipboard.writeText(text);
}

function clearText() {
    document.getElementById('userInput').value = "";
    document.getElementById('resultOutput').innerText = "";
}

function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), wait);
    };
}

window.onload = init;
</script>
</body>
</html>
