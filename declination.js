// declination.js — VERSION THAT ACTUALLY USES YOUR FILES

let LEMMA_DICT = {};   // polish → lemma
let FORMS = {};        // lemma → {case_number → form}

// =====================
// INIT
// =====================
async function initDeclination() {
    const [osnovaRes, vuzorRes] = await Promise.all([
        fetch('osnova.json'),
        fetch('vuzor.json')
    ]);

    const osnova = await osnovaRes.json();
    const vuzor = await vuzorRes.json();

    processData([...osnova, ...vuzor]);
}

// =====================
// PARSE TYPE STRING
// =====================
function extractLemma(typeStr) {
    const match = typeStr.match(/jimenьnik: "([^"]+)"/);
    return match ? match[1] : null;
}

function extractCase(typeStr) {
    if (typeStr.includes("nominative")) return "nominative";
    if (typeStr.includes("genitive")) return "genitive";
    if (typeStr.includes("accusative")) return "accusative";
    if (typeStr.includes("dative")) return "dative";
    if (typeStr.includes("instrumental")) return "instrumental";
    if (typeStr.includes("locative")) return "locative";
    if (typeStr.includes("vocative")) return "vocative";
    return null;
}

function extractNumber(typeStr) {
    if (typeStr.includes("plural")) return "plural";
    return "singular";
}

// =====================
// BUILD DATABASE
// =====================
function processData(data) {
    data.forEach(entry => {
        const typeStr = entry["type and case"];
        const polish = entry["polish"]?.toLowerCase();
        const slovian = entry["slovian"];

        if (!typeStr || !slovian) return;

        const lemma = extractLemma(typeStr);
        const grammaticalCase = extractCase(typeStr);
        const number = extractNumber(typeStr);

        if (!lemma || !grammaticalCase) return;

        // 🔥 build lemma → forms
        if (!FORMS[lemma]) {
            FORMS[lemma] = {};
        }

        FORMS[lemma][`${grammaticalCase}_${number}`] = slovian;

        // 🔥 build polish → lemma (ONLY nominative singular!)
        if (
            polish &&
            grammaticalCase === "nominative" &&
            number === "singular"
        ) {
            LEMMA_DICT[polish] = lemma;
        }
    });

    console.log("LEMMA_DICT", Object.keys(LEMMA_DICT).length);
    console.log("FORMS", Object.keys(FORMS).length);
}

// =====================
// INFLECT
// =====================
function inflect(lemma, grammaticalCase, number = "singular") {
    const forms = FORMS[lemma];
    if (!forms) return lemma;

    return forms[`${grammaticalCase}_${number}`] || lemma;
}

// =====================
// SIMPLE NLP
// =====================
function detectCase(plWord, prevWord = "") {
    prevWord = prevWord.toLowerCase();

    if (["do", "od", "bez"].includes(prevWord)) return "genitive";
    if (["dla"].includes(prevWord)) return "dative";
    if (["z", "ze"].includes(prevWord)) return "instrumental";
    if (["o", "w", "na"].includes(prevWord)) return "locative";

    return "nominative";
}

function detectNumber(word) {
    return word.endsWith("y") || word.endsWith("i");
}

// =====================
// TRANSLATE
// =====================
function translateWord(word, prevWord = "") {
    const clean = word.toLowerCase();

    const lemma = LEMMA_DICT[clean];
    if (!lemma) return word;

    const grammaticalCase = detectCase(clean, prevWord);
    const number = detectNumber(clean) ? "plural" : "singular";

    return inflect(lemma, grammaticalCase, number);
}

function translateSentence(sentence) {
    const words = sentence.split(/\s+/);

    return words.map((w, i) => {
        const prev = i > 0 ? words[i - 1] : "";
        return translateWord(w, prev);
    }).join(" ");
}

// =====================
// DEBUG
// =====================
function debugLemma(plWord) {
    const lemma = LEMMA_DICT[plWord.toLowerCase()];
    if (!lemma) return null;

    return FORMS[lemma];
}

// =====================
export {
    initDeclination,
    inflect,
    translateWord,
    translateSentence,
    debugLemma
};
