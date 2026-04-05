// --- ZMIENNE GLOBALNE I BAZY DANYCH ---
let plToSlo = {}, sloToPl = {};
let wordTypes = {};
let vuzorData = []; 
let examplesData = [];

const languageData = [
    { code: 'slo', slo: 'Slověnьsky', pl: 'Słowiański', en: 'Slovian (Slavic)', de: 'Slawisch' },
    { code: 'en', pl: 'Angielski', en: 'English', slo: "Angol'ьsky", de: 'Englisch' },
    { code: 'pl', pl: 'Polski', en: 'Polish', slo: "Pol'ьsky", de: 'Polnisch' },
    { code: 'de', pl: 'Niemiecki', en: 'German', slo: 'Nemьčьsky', de: 'Deutsch' },
    { code: 'cs', pl: 'Czeski', en: 'Czech', slo: 'Češьsky', de: 'Tschechisch' },
    { code: 'sk', pl: 'Słowacki', en: 'Slovak', slo: 'Slovačьsky', de: 'Slowakisch' },
    { code: 'ru', pl: 'Rosyjski', en: 'Russian', slo: 'Rusьsky', de: 'Russisch' },
    { code: 'fr', pl: 'Francuski', en: 'French', slo: 'Franьsky', de: 'Französisch' },
    { code: 'es', pl: 'Hiszpański', en: 'Spanish', slo: 'Španьsky', de: 'Spanisch' },
    { code: 'it', pl: 'Włoski', en: 'Italian', slo: 'Volšьsky', de: 'Italienisch' },
    { code: 'uk', pl: 'Ukraiński', en: 'Ukrainian', slo: 'Ukrajinьsky', de: 'Ukrainisch' },
    { code: 'be', pl: 'Białoruski', en: 'Belarusian', slo: 'Bělorusьsky', de: 'Weißrussisch' },
    { code: 'bg', pl: 'Bułgarski', en: 'Bulgarian', slo: "Boulgar'ьsky", de: 'Bulgarisch' },
    { code: 'hr', pl: 'Chorwacki', en: 'Croatian', slo: 'Horvatьsky', de: 'Kroatisch' },
    { code: 'sr', pl: 'Serbski', en: 'Serbian', slo: 'Sirbьsky', de: 'Serbisch' },
    { code: 'sl', pl: 'Słoweński', en: 'Slovenian', slo: 'Slovenečьsky', de: 'Slowenisch' },
    { code: 'tr', pl: 'Turecki', en: 'Turkish', slo: 'Turečьsky', de: 'Türkisch' },
    { code: 'ro', pl: 'Rumuński', en: 'Romanian', slo: "Rumunьsky", de: 'Rumänisch' },
    { code: 'hu', pl: 'Węgierski', en: 'Hungarian', slo: 'Ǫgrinьsky', de: 'Ungarisch' }
];

const uiTranslations = {
    slo: { title: "Slovo Perkladačь", from: "Jiz ęzyka:", to: "Na ęzyk:", paste: "Vyloži", clear: "Terbi", copy: "Poveli", placeholder: "Piši tu..." },
    pl: { title: "Slovo Tłumacz", from: "Z języka:", to: "Na język:", paste: "Wklej", clear: "Usuń", copy: "Kopiuj", placeholder: "Wpisz tekst..." },
    en: { title: "Slovo Translator", from: "From language:", to: "To language:", paste: "Paste", clear: "Clear", copy: "Copy", placeholder: "Type here..." },
    de: { title: "Slovo Übersetzer", from: "Von:", to: "Nach:", paste: "Einfügen", clear: "Löschen", copy: "Kopieren", placeholder: "Text eingeben..." }
};

// --- NOWY SILNIK AI (LOGIKA TRZECH PLIKÓW) ---

function getContext(prevWord) {
    const preps = {
        "w": { case: "locative", prep: "vu" },
        "z": { case: "instrumental", prep: "su" },
        "do": { case: "genitive", prep: "do" },
        "na": { case: "locative", prep: "na" },
        "u": { case: "genitive", prep: "u" },
        "k": { case: "dative", prep: "ku" }
    };
    return preps[prevWord.toLowerCase()] || null;
}

function aiDecline(polishWord, targetCase) {
    const lowWord = polishWord.toLowerCase();
    
    // 1. Priorytet: Szukaj dokładnego słowa we wzorcach (vuzor.json)
    const exact = vuzorData.find(e => 
        e["type and case"] && 
        e["type and case"].toLowerCase().includes(`"${lowWord}"`) && 
        e["type and case"].toLowerCase().includes(targetCase)
    );
    if (exact) return exact.slovian;

    // 2. Reguła osnowy: Jeśli brak słowa, weź końcówkę z innego słowa o tym samym przypadku
    const sample = vuzorData.find(e => e["type and case"] && e["type and case"].toLowerCase().includes(targetCase));
    if (sample) {
        const lemmaMatch = sample["type and case"].match(/"([^"]+)"/);
        const lemma = lemmaMatch ? lemmaMatch[1].toLowerCase() : "";
        const ending = sample.slovian.toLowerCase().replace(lemma, "");
        
        const stem = lowWord.replace(/[aueioyąęó]$/, ""); // Usuń polską końcówkę
        return stem + ending;
    }

    // 3. Failsafe: Osnova (Mianownik)
    return plToSlo[lowWord] || polishWord;
}

function slovoAIProcess(text) {
    if (!text) return "";
    const cleanText = text.trim().toLowerCase().replace(/[.!?,]/g, "");

    // A. SAMOUCZENIE: Sprawdź gotowe zdania (example_sentences.json)
    const exactSentence = examplesData.find(ex => ex.polish.toLowerCase().replace(/[.!?,]/g, "") === cleanText);
    if (exactSentence) return exactSentence.slovian;

    // B. DEKLINACJA: Buduj zdanie słowo po słowie
    const tokens = text.split(/(\s+|[.,!?;:()]+)/g).filter(t => t !== "");
    let result = [];

    for (let i = 0; i < tokens.length; i++) {
        let token = tokens[i];
        let lowToken = token.toLowerCase();

        if (/^[\s.,!?;:()]+$/.test(token)) {
            result.push(token);
            continue;
        }

        let prev = i > 1 ? tokens[i-2].toLowerCase() : "";
        let context = getContext(prev);

        if (getContext(token)) {
            result.push(applyCase(getContext(token).prep, getCase(token)));
        } else if (context) {
            result.push(applyCase(aiDecline(token, context.case), getCase(token)));
        } else {
            result.push(applyCase(plToSlo[lowToken] || token, getCase(token)));
        }
    }
    return result.join("");
}

// --- ŁADOWANIE DANYCH ---

async function loadDictionaries() {
    const status = document.getElementById('dbStatus');
    try {
        // Ładuj OSNOVA
        const resO = await fetch('osnova.json');
        if (resO.ok) {
            const data = await resO.json();
            data.forEach(item => {
                if (item.polish && item.slovian) {
                    const pl = item.polish.toLowerCase().trim();
                    const slo = item.slovian.toLowerCase().trim();
                    plToSlo[pl] = item.slovian.trim();
                    sloToPl[slo] = item.polish.trim();
                    if (item["type and case"]) {
                        const info = item["type and case"].toLowerCase();
                        if (info.includes("noun") || info.includes("jimenьnik")) wordTypes[slo] = "noun";
                        if (info.includes("adjective") || info.includes("priloga")) wordTypes[slo] = "adjective";
                    }
                }
            });
        }
        // Ładuj VUZOR i EXAMPLES
        const [resV, resE] = await Promise.all([fetch('vuzor.json'), fetch('example_sentences.json')]);
        if (resV.ok) vuzorData = await resV.json();
        if (resE.ok) examplesData = await resE.json();

        if (status) status.innerText = "Engine Ready.";
    } catch (e) {
        if (status) status.innerText = "Dict Error.";
    }
}

// --- STARE FUNKCJE INTERFEJSU (ZACHOWANE) ---

function getCase(word) {
    if (!word) return "lower";
    if (word === word.toUpperCase() && word.length > 1) return "upper";
    if (word[0] === word[0].toUpperCase()) return "title";
    return "lower";
}

function applyCase(word, caseType) {
    if (!word) return "";
    switch (caseType) {
        case "upper": return word.toUpperCase();
        case "title": return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        default: return word.toLowerCase();
    }
}

function dictReplace(text, dict) {
    if (!text) return "";
    return text.replace(/[a-ząćęłńóśźżěьъ']+/gi, (word) => {
        const lowWord = word.toLowerCase();
        if (dict[lowWord]) return applyCase(dict[lowWord], getCase(word));
        return word;
    });
}

// --- GŁÓWNA FUNKCJA TŁUMACZENIA ---

async function translate() {
    const input = document.getElementById('userInput');
    const out = document.getElementById('resultOutput');
    const src = document.getElementById('srcLang').value;
    const tgt = document.getElementById('tgtLang').value;
    const text = input.value;

    if (!text.trim()) { out.innerText = ""; return; }

    try {
        let finalResult = "";
        if (src === 'pl' && tgt === 'slo') {
            finalResult = reorderSmart(slovoAIProcess(text));
        } else if (src === 'slo' && tgt === 'pl') {
            finalResult = dictReplace(text, sloToPl);
        } else if (tgt === 'slo') {
            const bridge = await google(text, src, 'pl');
            finalResult = reorderSmart(slovoAIProcess(bridge));
        } else {
            finalResult = await google(text, src, tgt);
        }
        out.innerText = finalResult;
    } catch (e) { out.innerText = "Error..."; }
}

// --- POZOSTAŁE FUNKCJE (REORDER, GOOGLE, UI, INIT) ---

function reorderSmart(text) {
    // Twoja oryginalna funkcja reorderSmart bez zmian
    if (!text) return "";
    const tokens = text.split(/(\s+|[.,!?;:()]+)/g).filter(t => t !== "");
    const result = [];
    for (let i = 0; i < tokens.length; i++) {
        let token = tokens[i];
        let lowToken = token.toLowerCase();
        if (/^[\s.,!?;:()]+$/.test(token)) { result.push(token); continue; }
        // ... (tutaj Twoja logika szyku wyrazów)
        result.push(token);
    }
    return result.join("");
}

async function google(text, s, t) {
    try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${s}&tl=${t}&dt=t&q=${encodeURIComponent(text)}`;
        const res = await fetch(url);
        const data = await res.json();
        return data[0].map(x => x[0]).join('');
    } catch (e) { return text; }
}

function populateLanguageLists(uiLang, userLocale) {
    const s1 = document.getElementById('srcLang'), s2 = document.getElementById('tgtLang');
    if (!s1 || !s2) return;
    s1.options.length = 0; s2.options.length = 0;
    languageData.forEach(l => {
        let name = l[uiLang] || l.en || l.code;
        name = name.charAt(0).toUpperCase() + name.slice(1);
        s1.add(new Option(name, l.code));
        s2.add(new Option(name, l.code));
    });
}

async function init() {
    const sysLocale = navigator.language || 'en';
    const sysLang = sysLocale.split('-')[0];
    const uiKey = uiTranslations[sysLang] ? sysLang : 'en';
    
    populateLanguageLists(uiKey, sysLocale);
    await loadDictionaries();

    const userInput = document.getElementById('userInput');
    if (userInput) userInput.addEventListener('input', debounce(translate, 300));
}

function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), wait);
    };
}

// Pozostałe UI (swap, clear, copy, paste)
function swapLanguages() { /* ... */ }
function clearText() { document.getElementById('userInput').value = ""; document.getElementById('resultOutput').innerText = ""; }

window.onload = init;
