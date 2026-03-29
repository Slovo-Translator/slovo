let plToSlo = {}, sloToPl = {};
let wordTypes = {};

const languageData = [
    { code: 'slo', pl: 'Słowiański', en: 'Slovian (Slavic)', slo: 'Slověnьsky' },
    { code: 'pl', pl: 'Polski', en: 'Polish', slo: "Pol'ьsky" },
    { code: 'en', pl: 'Angielski', en: 'English', slo: "Angol'ьsky" }
];

// Funkcja pomocnicza do sprawdzania wielkości liter
function getCase(word) {
    if (!word) return "lower";
    if (word === word.toUpperCase() && word.length > 1) return "upper";
    if (word[0] === word[0].toUpperCase()) return "title";
    return "lower";
}

// Funkcja ustawiająca wielkość liter
function applyCase(word, caseType) {
    if (!word) return "";
    if (caseType === "upper") return word.toUpperCase();
    if (caseType === "title") return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    return word.toLowerCase();
}

function dictReplace(text, dict) {
    if (!text) return "";
    return text.replace(/[a-ząćęłńóśźżěьъ']+/gi, (word) => {
        const lowWord = word.toLowerCase();
        if (dict[lowWord]) {
            return applyCase(dict[lowWord], getCase(word));
        }
        return word;
    });
}

function reorderSmart(text) {
    if (!text) return "";
    // Dzielenie na słowa i interpunkcję
    const tokens = text.split(/(\s+|[.,!?;:()]+)/g).filter(t => t !== "" && t !== undefined);
    const result = [];

    for (let i = 0; i < tokens.length; i++) {
        let token = tokens[i];
        let lowToken = token.toLowerCase();

        // Pomiń znaki interpunkcyjne i spacje
        if (/^[\s.,!?;:()]+$/.test(token)) {
            result.push(token);
            continue;
        }

        let nextIdx = i + 1;
        while (nextIdx < tokens.length && /^[\s]+$/.test(tokens[nextIdx])) nextIdx++;

        if (nextIdx < tokens.length) {
            let nextToken = tokens[nextIdx];
            let nextLow = nextToken.toLowerCase();

            // LOGIKA: Rzeczownik + (Przymiotnik LUB Liczebnik) -> Zamiana
            const isNounFirst = wordTypes[lowToken] === "noun";
            const isAdjOrNumSecond = (wordTypes[nextLow] === "adjective" || wordTypes[nextLow] === "numeral");

            if (isNounFirst && isAdjOrNumSecond) {
                const firstCase = getCase(token); // Pobierz wielkość liter z "Język"
                
                // Zamiana: Przymiotnik/Liczebnik idzie na przód i dostaje wielkość liter pierwszego słowa
                result.push(applyCase(nextToken, firstCase));
                
                // Dodaj spacje/znaki pomiędzy
                for (let j = i + 1; j < nextIdx; j++) result.push(tokens[j]);
                
                // Rzeczownik idzie na drugie miejsce i staje się mały (chyba że był cały w Caps)
                result.push(firstCase === "upper" ? token.toUpperCase() : token.toLowerCase());
                
                i = nextIdx;
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
    const src = document.getElementById('srcLang').value;
    const tgt = document.getElementById('tgtLang').value;

    if (!input.value.trim()) { out.innerText = ""; return; }

    try {
        let finalResult = "";
        if (src === 'pl' && tgt === 'slo') {
            let translated = dictReplace(input.value, plToSlo);
            finalResult = reorderSmart(translated);
        } else if (src === 'slo' && tgt === 'pl') {
            finalResult = dictReplace(input.value, sloToPl);
        } else {
            // Google Translate dla innych par
            const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${src}&tl=${tgt}&dt=t&q=${encodeURIComponent(input.value)}`;
            const res = await fetch(url);
            const data = await res.json();
            finalResult = data[0].map(x => x[0]).join('');
        }
        out.innerText = finalResult;
    } catch (e) { out.innerText = "Error..."; }
}

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

                        if (item["type and case"]) {
                            const info = item["type and case"].toLowerCase();
                            if (info.includes("jimenьnik") || info.includes("noun")) wordTypes[slo] = "noun";
                            if (info.includes("priloga") || info.includes("adjective")) wordTypes[slo] = "adjective";
                            if (info.includes("ličьnik") || info.includes("numeral")) wordTypes[slo] = "numeral";
                        }
                    }
                });
            }
        }
        if (status) status.innerText = "Silnik gotowy.";
    } catch (e) { if (status) status.innerText = "Błąd."; }
}

function debounce(func, wait) {
    let timeout;
    return function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, arguments), wait);
    };
}

async function init() {
    await loadDictionaries();
    document.getElementById('userInput').addEventListener('input', debounce(translate, 300));
}

window.onload = init;
