let plToSlo = {}, sloToPl = {};
let wordTypes = {};

const languageData = [
    { code: 'slo', slo: 'Slověnьsky', pl: 'Słowiański', en: 'Slovian (Slavic)', de: 'Slawisch' },
    { code: 'pl', pl: 'Polski', en: 'Polish', slo: "Pol'ьsky", de: 'Polnisch' },
    { code: 'en', pl: 'Angielski', en: 'English', slo: "Angol'ьsky", de: 'Englisch' },
    { code: 'de', pl: 'Niemiecki', en: 'German', slo: 'Nemьčьsky', de: 'Deutsch' },
    { code: 'cs', pl: 'Czeski', en: 'Czech', slo: 'Češьsky', de: 'Tschechisch' },
    { code: 'sk', pl: 'Słowacki', en: 'Slovak', slo: 'Slovačьsky', de: 'Slowakisch' },
    { code: 'ru', pl: 'Rosyjski', en: 'Russian', slo: 'Rusьsky', de: 'Russisch' },
    { code: 'uk', pl: 'Ukraiński', en: 'Ukrainian', slo: 'Ukrajinьsky', de: 'Ukrainisch' },
    { code: 'be', pl: 'Białoruski', en: 'Belarusian', slo: 'Bělorusьsky', de: 'Weißrussisch' },
    { code: 'bg', pl: 'Bułgarski', en: 'Bulgarian', slo: "Boulgar'ьsky", de: 'Bulgarisch' },
    { code: 'hr', pl: 'Chorwacki', en: 'Croatian', slo: 'Horvatьsky', de: 'Kroatisch' },
    { code: 'sr', pl: 'Serbski (cyrylica)', en: 'Serbian (Cyrillic)', slo: 'Sirbьsky (kyrilica)', de: 'Serbisch (Kyrillisch)' },
    { code: 'sr-Latn', pl: 'Serbski (łacina)', en: 'Serbian (Latin)', slo: 'Sirbьsky (latinica)', de: 'Serbisch (Latein)' },
    { code: 'sl', pl: 'Słoweński', en: 'Slovenian', slo: 'Slovenečьsky', de: 'Slowenisch' },
    { code: 'mk', pl: 'Macedoński', en: 'Macedonian', slo: 'Makedonьsky', de: 'Macedonisch' },
    { code: 'tr', pl: 'Turecki', en: 'Turkish', slo: 'Turečьsky', de: 'Türkisch' }
];

const uiTranslations = {
    slo: { title: "Slovo Perkladačь", from: "Jiz ęzyka:", to: "Na ęzyk:", paste: "Vyloži", clear: "Terbi", copy: "Poveli", placeholder: "Piši tu...", didYouMean: "Ili vy mьnite:" },
    pl: { title: "Slovo Tłumacz", from: "Z języka:", to: "Na język:", paste: "Wklej", clear: "Usuń", copy: "Kopiuj", placeholder: "Wpisz tekst...", didYouMean: "Czy chodziło Ci o:" },
    en: { title: "Slovo Translator", from: "From language:", to: "To language:", paste: "Paste", clear: "Clear", copy: "Copy", placeholder: "Type here...", didYouMean: "Did you mean:" }
};

// --- POPULATE ---
function populateLanguageLists(uiLang, userLocale) {
    const s1 = document.getElementById('srcLang'), s2 = document.getElementById('tgtLang');
    if (!s1 || !s2) return;
    let dn;
    try { dn = new Intl.DisplayNames([userLocale], { type: 'language' }); } catch (e) {}

    [s1, s2].forEach(s => {
        s.options.length = 0;
        languageData.forEach(l => {
            let name = "";
            if (l.code === 'slo') { name = l[uiLang] || l.en; }
            else { name = dn ? dn.of(l.code) : (l[uiLang] || l.en); }
            if (l.code === 'sr') name = (uiLang === 'pl') ? "Serbski (cyrylica)" : "Serbian (Cyrillic)";
            if (l.code === 'sr-Latn') name = (uiLang === 'pl') ? "Serbski (łacina)" : "Serbian (Latin)";
            s.add(new Option(name.charAt(0).toUpperCase() + name.slice(1), l.code));
        });
    });
}

// --- CASE MAPPING ---
function getCase(word) {
    if (!word) return "lower";
    if (word === word.toUpperCase() && word.length > 1) return "upper";
    if (word[0] === word[0].toUpperCase()) return "title";
    return "lower";
}

function applyCase(word, caseType) {
    if (!word) return "";
    if (caseType === "upper") return word.toUpperCase();
    if (caseType === "title") return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    return word.toLowerCase();
}

// --- TRANSLATION CORE ---
async function google(text, s, t) {
    try {
        // Dodano dt=qca dla sprawdzania pisowni
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${s}&tl=${t}&dt=t&dt=qca&q=${encodeURIComponent(text)}`;
        const res = await fetch(url);
        const data = await res.json();

        // Obsługa sugestii (Spellcheck)
        const suggestionBox = document.getElementById('suggestionBox');
        if (suggestionBox) {
            if (data[7] && data[7][1]) {
                const cleanSuggest = data[7][1].replace(/<b>|<\/b>|<i>|<\/i>/g, "");
                const currentUi = document.documentElement.lang || 'en';
                const label = uiTranslations[currentUi]?.didYouMean || uiTranslations.en.didYouMean;
                suggestionBox.innerHTML = `${label} <span class="suggest-link" onclick="applySuggestion('${cleanSuggest.replace(/'/g, "\\'")}')">${cleanSuggest}</span>`;
                suggestionBox.style.display = 'block';
            } else {
                suggestionBox.style.display = 'none';
            }
        }
        return data[0].map(x => x[0]).join('');
    } catch (e) { return text; }
}

function applySuggestion(text) {
    const input = document.getElementById('userInput');
    if (input) {
        input.value = text;
        translate();
    }
}

function dictReplace(text, dict) {
    if (!text) return "";
    return text.replace(/[a-ząćęłńóśźżěьъǫę']+/gi, (word) => {
        const lowWord = word.toLowerCase();
        if (dict[lowWord]) return applyCase(dict[lowWord], getCase(word));
        return word;
    });
}

function reorderSmart(text) {
    if (!text) return "";
    const tokens = text.split(/(\s+|[.,!?;:()=+\-%*/]+)/g).filter(t => t);
    const result = [];
    for (let i = 0; i < tokens.length; i++) {
        let token = tokens[i];
        let lowToken = token.toLowerCase();
        if (/^[\s.,!?;:()=+\-%*/]+$/.test(token)) { result.push(token); continue; }
        if (wordTypes[lowToken]) {
            let group = [], currentIdx = i, firstWordCase = getCase(tokens[i]);
            while (currentIdx < tokens.length) {
                let currentToken = tokens[currentIdx];
                if (/^[\s]+$/.test(currentToken)) { currentIdx++; continue; }
                let type = wordTypes[currentToken.toLowerCase()];
                if (type === "noun" || type === "adjective" || type === "numeral") {
                    group.push({ val: currentToken, type: type });
                    i = currentIdx; currentIdx++;
                } else break;
            }
            if (group.length > 1) {
                const order = { "numeral": 1, "adjective": 2, "noun": 3 };
                group.sort((a, b) => (order[a.type] || 99) - (order[b.type] || 99));
                group.forEach((word, index) => {
                    let formatted = (index === 0) ? applyCase(word.val, firstWordCase) : 
                                    (firstWordCase === "upper" ? word.val.toUpperCase() : word.val.toLowerCase());
                    result.push(formatted);
                    if (index < group.length - 1) result.push(" ");
                });
                continue;
            }
        }
        result.push(token);
    }
    return result.join("");
}

async function translate() {
    const input = document.getElementById('userInput');
    const out = document.getElementById('resultOutput');
    if (!input || !out) return;
    const text = input.value, src = document.getElementById('srcLang').value, tgt = document.getElementById('tgtLang').value;
    if (!text.trim()) { out.innerText = ""; return; }

    try {
        let finalResult = "";
        // PIPELINE: X -> Google (PL) -> Słowiański
        if (tgt === 'slo') {
            const bridge = await google(text, src, 'pl');
            let translated = dictReplace(bridge, plToSlo);
            finalResult = reorderSmart(translated);
        } 
        else if (src === 'slo') {
            const bridge = dictReplace(text, sloToPl);
            finalResult = (tgt === 'pl') ? bridge : await google(bridge, 'pl', tgt);
        } 
        else {
            finalResult = await google(text, src, tgt);
        }
        out.innerText = finalResult;
    } catch (e) { out.innerText = "Error..."; }
}

// --- INITIALIZATION ---
async function loadDictionaries() {
    const status = document.getElementById('dbStatus');
    try {
        const files = ['osnova.json', 'vuzor.json'];
        for (const file of files) {
            const res = await fetch(file);
            if (res.ok) {
                const data = await res.json();
                data.forEach(item => {
                    if (item.polish && item.slovian) {
                        const pl = item.polish.toLowerCase().trim();
                        const slo = item.slovian.toLowerCase().trim();
                        plToSlo[pl] = item.slovian.trim();
                        sloToPl[slo] = item.polish.trim();
                        const info = (item["type and case"] || "").toLowerCase();
                        if (info.includes("jimenьnik") || info.includes("noun")) wordTypes[slo] = "noun";
                        if (info.includes("priloga") || info.includes("adjective")) wordTypes[slo] = "adjective";
                        if (info.includes("ličьnik") || info.includes("numeral")) wordTypes[slo] = "numeral";
                    }
                });
            }
        }
        if (status) status.innerText = "Engine Ready.";
    } catch (e) { if (status) status.innerText = "Dict Error."; }
}

async function init() {
    const sysLocale = navigator.language || 'en';
    const sysLang = sysLocale.split('-')[0];
    const uiKey = uiTranslations[sysLang] ? sysLang : 'en';
    document.documentElement.lang = uiKey;
    applyUI(uiKey);
    populateLanguageLists(uiKey, sysLocale);
    
    const srcS = document.getElementById('srcLang'), tgtS = document.getElementById('tgtLang');
    srcS.value = localStorage.getItem('srcLang') || 'pl';
    tgtS.value = localStorage.getItem('tgtLang') || 'slo';

    [srcS, tgtS].forEach(s => s.addEventListener('change', () => {
        localStorage.setItem('srcLang', srcS.value);
        localStorage.setItem('tgtLang', tgtS.value);
        translate();
    }));

    await loadDictionaries();
    document.getElementById('userInput')?.addEventListener('input', debounce(translate, 400));
}

function applyUI(lang) {
    const ui = uiTranslations[lang] || uiTranslations.en;
    ['title', 'label-from', 'label-to', 'paste', 'clear', 'copy'].forEach(id => {
        const el = document.getElementById('ui-' + id);
        if (el) el.innerText = ui[id.replace('label-', '')] || "";
    });
    const input = document.getElementById('userInput');
    if (input) input.placeholder = ui.placeholder;
}

function swapLanguages() {
    const s = document.getElementById('srcLang'), t = document.getElementById('tgtLang');
    const i = document.getElementById('userInput'), o = document.getElementById('resultOutput');
    [s.value, t.value] = [t.value, s.value];
    localStorage.setItem('srcLang', s.value);
    localStorage.setItem('tgtLang', t.value);
    if (o.innerText.trim()) i.value = o.innerText;
    translate();
}

function clearText() {
    document.getElementById('userInput').value = "";
    document.getElementById('resultOutput').innerText = "";
    const sb = document.getElementById('suggestionBox');
    if (sb) sb.style.display = 'none';
}

function copyText() { navigator.clipboard.writeText(document.getElementById('resultOutput').innerText); }

async function pasteText() {
    try {
        document.getElementById('userInput').value = await navigator.clipboard.readText();
        translate();
    } catch(e) {}
}

function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), wait);
    };
}

window.onload = init;
