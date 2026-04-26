/* slovo_ml_bridge.js
 * Stabilna warstwa ML + JSON + odmiana + szyk części mowy.
 * v6: tłumaczy także tekst wklejany i układa grupy: liczebnik → przymiotnik → rzeczownik.
 *
 * Ładuj w index.html dokładnie w tej kolejności:
 * <script src="slovo_model.js"></script>
 * <script src="script.js"></script>
 * <script src="slovo_ml_bridge.js"></script>
 */
(function () {
    "use strict";

    let slovoMLBridgeModel = null;
    let slovoMLBridgeLoading = null;

    const BRIDGE = {
        loaded: false,
        loading: null,
        pl2slo: new Map(),
        slo2pl: new Map(),
        sentPl2Slo: new Map(),
        sentSlo2Pl: new Map(),
        formsByLemmaPl2Slo: new Map(),
        formsByLemmaSlo2Pl: new Map(),
        stats: { entries: 0, sentences: 0, lemmaForms: 0 }
    };

    const USE_GUESS_FALLBACK = false;
    const TRUST_MODEL_SINGLE_WORD = false;
    const MAX_PHRASE_WORDS = 10;

    const DATA_FILES = [
        { url: "vuzor.json", source: "vuzor", priority: 500 },
        { url: "osnova.json", source: "osnova", priority: 300 }
    ];

    const EXAMPLE_SENTENCE_FILES = [
        { url: "example_sentences.json", source: "example_sentences", priority: 1000 }
    ];

    const TOKEN_RE = /([\p{L}\p{M}0-9'’]+|\s+|[^\s\p{L}\p{M}0-9'’]+)/gu;
    const WORD_RE = /^[\p{L}\p{M}0-9'’]+$/u;
    const URL_RE = /(https?:\/\/[^\s]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
    const TERMINAL_PUNCT_RE = /([.!?…]+)$/u;

    const ORDER = { numeral: 1, adjective: 2, noun: 3 };

    const CASE_BY_PREPOSITION = {
        "do": "genitive", "od": "genitive", "bez": "genitive", "dla": "genitive", "u": "genitive",
        "około": "genitive", "wokół": "genitive", "podczas": "genitive", "według": "genitive", "oprócz": "genitive",
        "ku": "dative", "dzięki": "dative", "wbrew": "dative", "przeciw": "dative", "przeciwko": "dative",
        "o": "locative", "w": "locative", "we": "locative", "na": "locative", "po": "locative", "przy": "locative",
        "z": "instrumental", "ze": "instrumental", "nad": "instrumental", "pod": "instrumental", "przed": "instrumental",
        "między": "instrumental", "pomiędzy": "instrumental", "za": "instrumental"
    };

    const ACCUSATIVE_VERBS = new Set([
        "mam", "masz", "ma", "mamy", "macie", "mają",
        "widzę", "widzisz", "widzi", "widzimy", "widzicie", "widzą",
        "znam", "znasz", "zna", "znamy", "znacie", "znają",
        "lubię", "lubisz", "lubi", "lubimy", "lubicie", "lubią",
        "kocham", "kochasz", "kocha", "kochamy", "kochacie", "kochają",
        "biorę", "bierzesz", "bierze", "bierzemy", "bierzecie", "biorą",
        "daj", "daje", "daję", "dajesz", "dajemy", "dają",
        "kupuję", "kupujesz", "kupuje", "kupujemy", "kupują",
        "robię", "robisz", "robi", "robimy", "robią",
        "piszę", "piszesz", "pisze", "piszemy", "piszą",
        "czytam", "czytasz", "czyta", "czytamy", "czytają",
        "buduję", "budujesz", "buduje", "budują"
    ]);

    function normalizeKey(text) {
        return String(text ?? "")
            .normalize("NFC")
            .replace(/[’]/g, "'")
            .replace(/\s+/g, " ")
            .trim()
            .toLocaleLowerCase("pl");
    }

    function stripTerminalPunct(text) {
        return String(text ?? "").trim().replace(TERMINAL_PUNCT_RE, "").trim();
    }

    function getTerminalPunct(text) {
        const m = String(text ?? "").trim().match(TERMINAL_PUNCT_RE);
        return m ? m[1] : "";
    }

    function normalizeSentenceKey(text) {
        return normalizeKey(stripTerminalPunct(text)).replace(/\s+([,.;:!?])/g, "$1");
    }

    function isWord(token) {
        return WORD_RE.test(token) && /[\p{L}\p{M}0-9]/u.test(token);
    }

    function isSpace(token) {
        return /^\s+$/.test(token);
    }

    function wordCount(text) {
        const tokens = String(text ?? "").match(TOKEN_RE) || [];
        return tokens.filter(isWord).length;
    }

    function sameNormalized(a, b) {
        return normalizeKey(a) === normalizeKey(b);
    }

    function getCaseType(text) {
        const letters = Array.from(String(text || "")).filter(ch => /\p{L}/u.test(ch));
        if (!letters.length) return "lower";
        const joined = letters.join("");
        if (joined.length > 1 && joined === joined.toLocaleUpperCase("pl") && joined !== joined.toLocaleLowerCase("pl")) return "upper";
        const first = letters[0];
        if (first === first.toLocaleUpperCase("pl") && first !== first.toLocaleLowerCase("pl")) return "title";
        return "lower";
    }

    function applyCaseLike(source, target) {
        let result = String(target ?? "");
        const caseType = getCaseType(source);
        if (caseType === "upper") return result.toLocaleUpperCase("pl");
        if (caseType === "title") {
            const chars = Array.from(result);
            if (!chars.length) return result;
            chars[0] = chars[0].toLocaleUpperCase("pl");
            return chars.join("");
        }
        return result;
    }

    function protectSpecialText(text) {
        const placeholders = [];
        const safe = String(text ?? "").replace(URL_RE, function (match) {
            const key = "__SLOVO_SPECIAL_" + placeholders.length + "__";
            placeholders.push(match);
            return key;
        });
        return {
            text: safe,
            restore(value) {
                return String(value ?? "").replace(/__SLOVO_SPECIAL_(\d+)__/g, function (_, id) {
                    return placeholders[Number(id)] || "";
                });
            }
        };
    }

    function fixOutputSpacing(text) {
        return String(text ?? "")
            .replace(/\s+([,.;:!?%])/g, "$1")
            .replace(/([([{„«])\s+/g, "$1")
            .replace(/\s+([)\]}”»])/g, "$1")
            .replace(/\s*—\s*/g, " — ")
            .replace(/([\p{L}\p{M}0-9ьъěęǫšžčćńłóśźż])\s*-\s*([\p{L}\p{M}0-9ьъěęǫšžčćńłóśźż])/gu, "$1 - $2")
            .replace(/[ \t]{2,}/g, " ")
            .trim();
    }

    function parseMeta(typeCase) {
        const raw = String(typeCase || "");
        const info = normalizeKey(raw);
        const meta = { raw, wordClass: "unknown", grammaticalCase: null, number: null, isPhrase: false, lemma: null };

        const lemmaMatch = raw.match(/jimenьnik\s*:\s*"([^"]+)"/i);
        if (lemmaMatch && lemmaMatch[1]) meta.lemma = normalizeKey(lemmaMatch[1]);

        if (info.includes("phrase") || info.includes("rěčen")) meta.isPhrase = true;

        if (info.includes("noun") || info.includes("jimenьnik") || info.includes("imenьnik") || info.includes("rzeczownik")) {
            meta.wordClass = "noun";
        }
        if (info.includes("adjective") || info.includes("pridavьnik") || info.includes("pridavnik") || info.includes("priloga") || info.includes("przymiotnik")) {
            meta.wordClass = "adjective";
        }
        if (info.includes("numeral") || info.includes("ličьnik") || info.includes("ličebьnik") || info.includes("licebnik") || info.includes("liczebnik")) {
            meta.wordClass = "numeral";
        }
        if (info.includes("verb") || info.includes("glagol") || info.includes("czasownik")) {
            meta.wordClass = "verb";
        }
        if (meta.isPhrase) meta.wordClass = "phrase";

        if (info.includes("nominative") || info.includes("jimenovьnik")) meta.grammaticalCase = "nominative";
        else if (info.includes("accusative") || info.includes("vinьnik")) meta.grammaticalCase = "accusative";
        else if (info.includes("genitive") || info.includes("rodilьnik")) meta.grammaticalCase = "genitive";
        else if (info.includes("locative") || info.includes("městьnik")) meta.grammaticalCase = "locative";
        else if (info.includes("dative") || info.includes("měrьnik")) meta.grammaticalCase = "dative";
        else if (info.includes("instrumental") || info.includes("orǫdьnik")) meta.grammaticalCase = "instrumental";
        else if (info.includes("vocative") || info.includes("zovanьnik")) meta.grammaticalCase = "vocative";

        if (info.includes("singular") || info.includes("poedinьna")) meta.number = "singular";
        else if (info.includes("plural") || info.includes("munoga")) meta.number = "plural";

        return meta;
    }

    function compareCandidateStatic(a, b) {
        if ((b.priority || 0) !== (a.priority || 0)) return (b.priority || 0) - (a.priority || 0);
        const aw = wordCount(a.source), bw = wordCount(b.source);
        if (bw !== aw) return bw - aw;
        const an = a.meta && a.meta.grammaticalCase === "nominative" ? 1 : 0;
        const bn = b.meta && b.meta.grammaticalCase === "nominative" ? 1 : 0;
        if (bn !== an) return bn - an;
        return 0;
    }

    function lemmaFormKey(lemma, grammaticalCase, number) {
        return [normalizeKey(lemma), grammaticalCase || "", number || ""].join("|");
    }

    function addLemmaForm(map, candidate) {
        const meta = candidate && candidate.meta;
        if (!meta || !meta.lemma || !meta.grammaticalCase) return;
        if (!ORDER[meta.wordClass]) return;
        const lemmaMap = map === BRIDGE.slo2pl ? BRIDGE.formsByLemmaSlo2Pl : BRIDGE.formsByLemmaPl2Slo;
        const keys = [
            lemmaFormKey(meta.lemma, meta.grammaticalCase, meta.number || ""),
            lemmaFormKey(meta.lemma, meta.grammaticalCase, "")
        ];
        for (const key of keys) {
            const list = lemmaMap.get(key) || [];
            list.push(candidate);
            lemmaMap.set(key, list);
            BRIDGE.stats.lemmaForms++;
        }
    }

    function addToMap(map, source, target, data) {
        const src = String(source ?? "").trim();
        const tgt = String(target ?? "").trim();
        if (!src || !tgt) return;
        const meta = parseMeta(data.typeCase);
        const candidate = { source: src, target: tgt, context: data.context || "", typeCase: data.typeCase || "", sourceFile: data.source || "unknown", priority: data.priority || 0, meta };
        const key = normalizeKey(src);
        const list = map.get(key) || [];
        list.push(candidate);
        map.set(key, list);
        addLemmaForm(map, candidate);
        BRIDGE.stats.entries++;
    }

    function addSentencePair(polish, slovian, data) {
        const pl = String(polish ?? "").trim();
        const slo = String(slovian ?? "").trim();
        if (!pl || !slo) return;
        BRIDGE.sentPl2Slo.set(normalizeSentenceKey(pl), { source: pl, target: slo, priority: data.priority || 1000 });
        BRIDGE.sentSlo2Pl.set(normalizeSentenceKey(slo), { source: slo, target: pl, priority: data.priority || 1000 });
        BRIDGE.stats.sentences++;
    }

    function getPreviousWord(tokens, index, step) {
        let found = 0;
        for (let i = index - 1; i >= 0; i--) {
            if (isWord(tokens[i])) {
                found++;
                if (found === step) return normalizeKey(tokens[i]);
            } else if (!isSpace(tokens[i])) {
                if (found === 0) continue;
                break;
            }
        }
        return "";
    }

    function inferPolishCaseFromEnding(word) {
        const w = normalizeKey(word);
        if (!w) return null;
        if (/(ami|emi|mi)$/.test(w)) return "instrumental";
        if (/(ach|ech)$/.test(w)) return "locative";
        if (/(om)$/.test(w)) return "dative";
        if (/(ą)$/.test(w)) return "instrumental";
        if (/(ę)$/.test(w)) return "accusative";
        return null;
    }

    function inferWantedCase(tokens, startIndex, sourceText, direction) {
        if (direction === "slo2pl") return null;
        const byEnding = inferPolishCaseFromEnding(sourceText);
        const prev1 = getPreviousWord(tokens, startIndex, 1);
        const prev2 = getPreviousWord(tokens, startIndex, 2);
        if (prev1 && CASE_BY_PREPOSITION[prev1]) {
            if ((prev1 === "z" || prev1 === "ze") && byEnding === "genitive") return "genitive";
            return CASE_BY_PREPOSITION[prev1];
        }
        if (prev2 && prev1 && normalizeKey(prev2 + " " + prev1) === "z powodu") return "genitive";
        if (prev1 && ACCUSATIVE_VERBS.has(prev1)) return "accusative";
        if (byEnding) return byEnding;
        return "nominative";
    }

    function candidateScore(candidate, sourceText, tokens, startIndex, direction) {
        let score = candidate.priority || 0;
        score += wordCount(candidate.source) * 30;
        const wanted = inferWantedCase(tokens || [], startIndex || 0, sourceText, direction);
        const cCase = candidate.meta && candidate.meta.grammaticalCase;
        if (wanted && cCase) score += wanted === cCase ? 120 : -45;
        if (candidate.meta && candidate.meta.wordClass === "phrase") score += 40;
        if (candidate.meta && candidate.meta.number === "singular") score += 5;
        if (/[ьъ]$/.test(candidate.target)) score += 2;
        return score;
    }

    function chooseCandidate(candidates, sourceText, tokens, startIndex, direction) {
        if (!candidates || !candidates.length) return null;
        let best = null, bestScore = -Infinity;
        for (const cand of candidates) {
            const score = candidateScore(cand, sourceText, tokens, startIndex, direction);
            if (score > bestScore) { best = cand; bestScore = score; }
        }
        return best;
    }

    function lookupLemmaForm(candidate, wantedCase, direction) {
        if (!candidate || !candidate.meta || !candidate.meta.lemma || !wantedCase) return null;
        if (!ORDER[candidate.meta.wordClass]) return null;
        const lemmaMap = direction === "slo2pl" ? BRIDGE.formsByLemmaSlo2Pl : BRIDGE.formsByLemmaPl2Slo;
        const number = candidate.meta.number || "singular";
        const keys = [
            lemmaFormKey(candidate.meta.lemma, wantedCase, number),
            lemmaFormKey(candidate.meta.lemma, wantedCase, "singular"),
            lemmaFormKey(candidate.meta.lemma, wantedCase, "")
        ];
        for (const key of keys) {
            const list = lemmaMap.get(key);
            if (list && list.length) return list[0];
        }
        return null;
    }

    function inflectCandidate(candidate, sourceText, tokens, startIndex, direction) {
        if (!candidate || direction === "slo2pl") return candidate;
        const wanted = inferWantedCase(tokens || [], startIndex || 0, sourceText, direction);
        if (!wanted) return candidate;
        if (candidate.meta && candidate.meta.grammaticalCase === wanted) return candidate;
        const form = lookupLemmaForm(candidate, wanted, direction);
        return form || candidate;
    }

    async function fetchJsonMaybe(url) {
        try {
            const res = await fetch(url + (url.includes("?") ? "&" : "?") + "v=" + Date.now(), { cache: "reload" });
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            console.warn("Nie można pobrać:", url, e);
            return null;
        }
    }

    function absorbRows(rows, fileInfo) {
        if (!Array.isArray(rows)) return;
        for (const item of rows) {
            if (!item || typeof item !== "object") continue;
            if (!item.polish || !item.slovian) continue;
            const data = { typeCase: item["type and case"] || item.type || "", context: item.context || "", source: fileInfo.source, priority: fileInfo.priority };
            addToMap(BRIDGE.pl2slo, item.polish, item.slovian, data);
            addToMap(BRIDGE.slo2pl, item.slovian, item.polish, data);
            if (String(data.typeCase).includes("phrase") || String(data.typeCase).includes("rěčen")) {
                addSentencePair(item.polish, item.slovian, { priority: fileInfo.priority + 100 });
            }
        }
    }


    function sortBridgeMaps() {
        const sortMap = function (map) {
            map.forEach(function (list) {
                if (Array.isArray(list) && list.length > 1) list.sort(compareCandidateStatic);
            });
        };
        sortMap(BRIDGE.pl2slo);
        sortMap(BRIDGE.slo2pl);
        sortMap(BRIDGE.formsByLemmaPl2Slo);
        sortMap(BRIDGE.formsByLemmaSlo2Pl);
    }

    async function loadBridgeData() {
        if (BRIDGE.loaded) return true;
        if (BRIDGE.loading) return BRIDGE.loading;
        BRIDGE.loading = (async function () {
            for (const fileInfo of EXAMPLE_SENTENCE_FILES) {
                const rows = await fetchJsonMaybe(fileInfo.url);
                if (Array.isArray(rows)) {
                    for (const row of rows) {
                        if (row && row.polish && row.slovian) addSentencePair(row.polish, row.slovian, fileInfo);
                    }
                }
            }
            for (const fileInfo of DATA_FILES) absorbRows(await fetchJsonMaybe(fileInfo.url), fileInfo);
            try {
                if (typeof plToSlo !== "undefined") {
                    Object.keys(plToSlo || {}).forEach(pl => addToMap(BRIDGE.pl2slo, pl, plToSlo[pl], { typeCase: "", source: "script.js", priority: 50 }));
                }
                if (typeof sloToPl !== "undefined") {
                    Object.keys(sloToPl || {}).forEach(slo => addToMap(BRIDGE.slo2pl, slo, sloToPl[slo], { typeCase: "", source: "script.js", priority: 50 }));
                }
            } catch (e) {}
            sortBridgeMaps();
            BRIDGE.loaded = true;
            console.log("Slovo bridge data loaded:", BRIDGE.stats);
            return true;
        })();
        return BRIDGE.loading;
    }

    async function loadSlovoMLBridge() {
        if (slovoMLBridgeModel && BRIDGE.loaded) return true;
        if (slovoMLBridgeLoading) return slovoMLBridgeLoading;
        slovoMLBridgeLoading = (async function () {
            const status = document.getElementById("dbStatus");
            await loadBridgeData();
            try {
                if (typeof SlovoTranslator !== "undefined") {
                    slovoMLBridgeModel = await SlovoTranslator.loadFromUrl("model/slovo-model.json");
                    if (status) status.innerText = "ML + Declension Engine Ready.";
                    return true;
                }
            } catch (e) {
                console.warn("Model ML nie został załadowany, działa JSON:", e);
            }
            if (status) status.innerText = "JSON Declension Engine Ready.";
            return true;
        })();
        return slovoMLBridgeLoading;
    }

    function mapForDirection(direction) {
        return direction === "slo2pl" ? BRIDGE.slo2pl : BRIDGE.pl2slo;
    }

    function sentenceMapForDirection(direction) {
        return direction === "slo2pl" ? BRIDGE.sentSlo2Pl : BRIDGE.sentPl2Slo;
    }

    function alignTerminalPunctuation(target, source) {
        const sourcePunct = getTerminalPunct(source);
        let out = String(target ?? "").trim();
        return sourcePunct ? stripTerminalPunct(out) + sourcePunct : stripTerminalPunct(out);
    }

    function lookupSentence(text, direction) {
        const hit = sentenceMapForDirection(direction).get(normalizeSentenceKey(text));
        return hit ? alignTerminalPunctuation(hit.target, text) : null;
    }

    function lookupWordCandidate(word, tokens, index, direction) {
        const list = mapForDirection(direction).get(normalizeKey(word));
        const chosen = chooseCandidate(list, word, tokens, index, direction);
        return chosen ? inflectCandidate(chosen, word, tokens, index, direction) : null;
    }

    function tryBuildPhrase(tokens, startIndex, direction) {
        const map = mapForDirection(direction);
        let phrase = "";
        let usedWords = 0;
        let best = null;

        for (let i = startIndex; i < tokens.length; i++) {
            const token = tokens[i];
            if (isWord(token)) {
                phrase += token;
                usedWords++;
                const list = map.get(normalizeKey(phrase.trim()));
                if (list && list.length) {
                    const cand = chooseCandidate(list, phrase.trim(), tokens, startIndex, direction);
                    if (cand && (usedWords > 1 || cand.meta.wordClass === "phrase")) {
                        best = { candidate: cand, source: phrase.trim(), endIndex: i + 1, words: usedWords };
                    }
                }
                if (usedWords >= MAX_PHRASE_WORDS) break;
                continue;
            }
            if (isSpace(token)) { phrase += " "; continue; }
            break;
        }

        if (!best) return null;
        // Nie używaj zwykłych dwuwyrazowych wpisów zamiast jawnego szyku części mowy.
        const meta = best.candidate.meta || {};
        if (best.words > 1 && meta.wordClass !== "phrase") return null;
        return best;
    }

    function translateByIndexedData(text, direction) {
        const original = String(text ?? "");
        if (!original.trim()) return "";

        const sentenceHit = lookupSentence(original, direction);
        if (sentenceHit) return sentenceHit;

        const protectedText = protectSpecialText(original);
        const tokens = protectedText.text.match(TOKEN_RE) || [protectedText.text];
        const out = [];
        let changed = false;

        for (let i = 0; i < tokens.length; i++) {
            const token = tokens[i];
            if (!isWord(token)) { out.push(token); continue; }

            // 1. Prawdziwa fraza/sentence z bazy ma pierwszeństwo.
            const phrase = tryBuildPhrase(tokens, i, direction);
            if (phrase && phrase.candidate && phrase.candidate.meta.wordClass === "phrase") {
                out.push(applyCaseLike(phrase.source, phrase.candidate.target));
                i = phrase.endIndex - 1;
                changed = true;
                continue;
            }

            // 2. Grupuj sąsiadujące wyrazy: rzeczownik/przymiotnik/liczebnik.
            const group = [];
            let j = i;
            while (j < tokens.length) {
                if (!isWord(tokens[j])) break;
                const cand = lookupWordCandidate(tokens[j], tokens, j, direction);
                const type = cand && cand.meta && cand.meta.wordClass;
                if (!(type === "noun" || type === "adjective" || type === "numeral")) break;
                group.push({ source: tokens[j], target: cand.target, type, index: group.length });
                let k = j + 1;
                while (k < tokens.length && isSpace(tokens[k])) k++;
                if (k < tokens.length && isWord(tokens[k])) j = k;
                else { j = k; break; }
            }

            if (direction === "pl2slo" && group.length > 1 && group.some(g => g.type === "noun") && group.some(g => g.type !== "noun")) {
                const firstCaseSource = group[0].source;
                const sorted = group.slice().sort((a, b) => {
                    const d = (ORDER[a.type] || 99) - (ORDER[b.type] || 99);
                    return d || a.index - b.index;
                });
                const words = sorted.map((g, idx) =>
    idx === 0
        ? applyCaseLike(firstCaseSource, g.target)
        : g.target.toLocaleLowerCase("pl")
);

out.push(words.join(" "));

/*
 * Jeżeli po przestawionej grupie stoi kolejne słowo,
 * trzeba ręcznie oddać spację, bo podczas zbierania grupy
 * spacje między wyrazami zostały pominięte.
 *
 * Bez tego wychodziło:
 * Dobry pisestь
 *
 * zamiast:
 * Dobry pis estь
 */
if (j < tokens.length && isWord(tokens[j])) {
    out.push(" ");
}

i = j - 1;
changed = true;
continue;
            }

            // 3. Pojedynczy wyraz.
            const single = lookupWordCandidate(token, tokens, i, direction);
            if (single && single.target) {
                out.push(applyCaseLike(token, single.target));
                changed = true;
                continue;
            }

            out.push(token);
        }

        const restored = protectedText.restore(out.join(""));
        return changed ? fixOutputSpacing(restored) : original;
    }

    function modelFallback(text, direction) {
        if (!slovoMLBridgeModel) return null;
        const wc = wordCount(text);
        if (wc <= 1 && !TRUST_MODEL_SINGLE_WORD && !USE_GUESS_FALLBACK) return null;
        try {
            if (direction === "slo2pl") {
                const result = slovoMLBridgeModel.translateSlovianToPolish(text, { fallback: "copy" });
                return sameNormalized(result, text) ? null : result;
            }
            const result = slovoMLBridgeModel.translatePolishToSlovian(text, { fallback: USE_GUESS_FALLBACK ? "guess" : "copy" });
            return sameNormalized(result, text) ? null : result;
        } catch (e) { return null; }
    }

    function translateDirection(text, direction) {
        const original = String(text ?? "");
        if (!original.trim()) return "";
        const indexed = translateByIndexedData(original, direction);
        if (!sameNormalized(indexed, original)) return fixOutputSpacing(indexed);
        const model = modelFallback(original, direction);
        return model ? fixOutputSpacing(alignTerminalPunctuation(model, original)) : original;
    }

    function translatePlToSloML(text) { return translateDirection(text, "pl2slo"); }
    function translateSloToPlML(text) { return translateDirection(text, "slo2pl"); }

    const oldLoadDictionaries = typeof loadDictionaries === "function" ? loadDictionaries : null;
    if (oldLoadDictionaries) {
        const patchedLoadDictionaries = async function () {
            await oldLoadDictionaries();
            await loadSlovoMLBridge();
        };
        try { loadDictionaries = patchedLoadDictionaries; } catch (e) {}
        window.loadDictionaries = patchedLoadDictionaries;
    } else {
        loadSlovoMLBridge();
    }

    const oldTranslate = typeof translate === "function" ? translate : null;
    if (oldTranslate) {
        const patchedTranslate = async function () {
            const input = document.getElementById("userInput");
            const out = document.getElementById("resultOutput");
            const srcSelect = document.getElementById("srcLang");
            const tgtSelect = document.getElementById("tgtLang");
            if (!input || !out || !srcSelect || !tgtSelect) return;

            const rawText = input.value;
            const src = srcSelect.value;
            const tgt = tgtSelect.value;
            if (!rawText.trim()) { out.innerText = ""; if (typeof hideCorrectionSuggestion === "function") hideCorrectionSuggestion(); return; }

            await loadSlovoMLBridge();

            try {
                let workingText = rawText;
                if (src !== "slo" && typeof prepareInputForTranslation === "function") {
                    const prepared = await Promise.race([
                        prepareInputForTranslation(rawText, src, tgt),
                        new Promise(resolve => setTimeout(() => resolve({ text: rawText }), 600))
                    ]);
                    workingText = prepared && prepared.text ? prepared.text : rawText;
                } else if (src === "slo" && typeof hideCorrectionSuggestion === "function") {
                    hideCorrectionSuggestion();
                }

                let finalResult = "";
                if (src === "slo" && tgt === "pl") {
                    finalResult = translateSloToPlML(rawText);
                } else if (src === "pl" && tgt === "slo") {
                    finalResult = translatePlToSloML(workingText);
                } else if (src === "slo") {
                    const bridge = translateSloToPlML(rawText);
                    finalResult = typeof google === "function" ? await google(bridge, "pl", tgt) : bridge;
                } else if (tgt === "slo") {
                    const bridge = typeof google === "function" ? await google(workingText, src, "pl") : workingText;
                    finalResult = translatePlToSloML(bridge);
                } else {
                    finalResult = typeof google === "function" ? await google(workingText, src, tgt) : workingText;
                }

                out.innerText = finalResult || "";
            } catch (e) {
                console.error("Błąd bridge; powrót do starego tłumacza:", e);
                return oldTranslate();
            }
        };
        try { translate = patchedTranslate; } catch (e) {}
        window.translate = patchedTranslate;
    }

    // Naprawiamy przycisk wklejania nawet wtedy, gdy stary script.js nie wywoła tłumaczenia po zmianie value.
    window.pasteText = async function () {
        try {
            const text = await navigator.clipboard.readText();
            const input = document.getElementById("userInput");
            if (input) {
                input.value = text;
                input.dispatchEvent(new Event("input", { bubbles: true }));
            }
            if (typeof window.translate === "function") await window.translate();
        } catch (e) {
            console.log("Clipboard error", e);
        }
    };

    window.loadSlovoMLBridge = loadSlovoMLBridge;
    window.translatePlToSloML = translatePlToSloML;
    window.translateSloToPlML = translateSloToPlML;
    window.__slovoBridge = BRIDGE;
})();
