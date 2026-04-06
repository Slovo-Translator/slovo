// ==================== GOTOWY JAVASCRIPT ====================

let plToSlo = {}, sloToPl = {};
let wordTypes = {};

// ---------------- WIELKOŚĆ LITER ----------------
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

// ---------------- REPLACE SŁOWNIKOWY ----------------
function dictReplace(text, dict) {
    if (!text) return "";
    const urlRegex = /(https?:\/\/[^\s]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
    let placeholders = [];
    let tempText = text.replace(urlRegex, match => {
        placeholders.push(match);
        return `__URL_PH_${placeholders.length - 1}__`;
    });
    tempText = tempText.replace(/[a-ząćęłńóśźżěьъ']+/gi, word => {
        const low = word.toLowerCase();
        return dict[low] ? applyCase(dict[low], getCase(word)) : "__MISSING__";
    });
    return tempText.replace(/__URL_PH_(\d+)__/g, (_, id) => placeholders[id]);
}

// ---------------- REORDER SMART ----------------
function reorderSmart(text) {
    if (!text) return "";
    const tokens = text.split(/(\s+|[.,!?;:()=+\-%*/]+)/g).filter(t => t);
    const result = [];
    for (let i = 0; i < tokens.length; i++) {
        let token = tokens[i];
        if (/^[\s.,!?;:()=+\-%*/]+$/.test(token)) {
            result.push(token); continue;
        }
        const low = token.toLowerCase();
        if (wordTypes[low] && ["noun","adjective","numeral"].includes(wordTypes[low])) {
            let group = [], idx = i;
            while (idx < tokens.length) {
                let curLow = tokens[idx].toLowerCase().trim();
                if (/^[\s]+$/.test(tokens[idx])) { idx++; continue; }
                let type = wordTypes[curLow];
                if (type === "noun" || type === "adjective" || type === "numeral") {
                    group.push({val: tokens[idx], type});
                    idx++;
                } else break;
            }
            if (group.length > 1) {
                const order = {numeral:1, adjective:2, noun:3};
                group.sort((a,b) => (order[a.type]||99) - (order[b.type]||99));
                group.forEach((w, j) => {
                    let f = w.val.toLowerCase();
                    if (j === 0) f = applyCase(w.val, getCase(group[0].val));
                    result.push(f);
                    if (j < group.length-1) result.push(" ");
                });
                i = idx - 1;
                continue;
            }
        }
        result.push(token);
    }
    return result.join("");
}

// ---------------- GŁÓWNA FUNKCJA TŁUMACZENIA ----------------
async function translatePlToSlo(text) {
    let result = dictReplace(text, plToSlo);
    if (result.includes("__MISSING__")) {
        result = text; // fallback
    }
    return reorderSmart(result);
}

// ---------------- ŁADOWANIE SŁOWNIKÓW ----------------
async function loadDictionaries() {
    const files = ['osnova.json', 'vuzor.json'];
    for (const file of files) {
        try {
            const res = await fetch(file);
            if (!res.ok) continue;
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
                        if (info.includes("pridavьnik") || info.includes("adjective")) wordTypes[slo] = "adjective";
                        if (info.includes("ličebьnik") || info.includes("numeral")) wordTypes[slo] = "numeral";
                    }
                }
            });
        } catch(e) {}
    }
    console.log("Slovian translator ready. Dictionaries loaded.");
}

// ---------------- PRZYKŁAD UŻYCIA ----------------
async function test() {
    await loadDictionaries();
    const input = "moja matka jest w domu";
    const output = await translatePlToSlo(input);
    console.log(output);   // → moja mati estь vu domě
}

// Uruchom test po załadowaniu
// test();

export { translatePlToSlo, loadDictionaries };
