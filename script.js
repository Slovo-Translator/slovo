let wordTypes = {};

const engine = {
  entries: [],
  exactPL: new Map(),
  exactSLO: new Map(),
  lemmaPL: new Map(),
  lemmaSLO: new Map(),
  phrasePL: new Map(),
  phraseSLO: new Map(),
  rulesPLtoSLO: [],
  rulesSLOtoPL: [],
  ready: false
};

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
  slo: {
    title: "Slovo Perkladačь",
    from: "Jiz ęzyka:",
    to: "Na ęzyk:",
    paste: "Vyloži",
    clear: "Terbi",
    copy: "Poveli",
    placeholder: "Piši tu...",
    didYouMean: "Ili vy mьnite:"
  },
  pl: {
    title: "Slovo Tłumacz",
    from: "Z języka:",
    to: "Na język:",
    paste: "Wklej",
    clear: "Usuń",
    copy: "Kopiuj",
    placeholder: "Wpisz tekst...",
    didYouMean: "Czy chodziło Ci o:"
  },
  en: {
    title: "Slovo Translator",
    from: "From language:",
    to: "To language:",
    paste: "Paste",
    clear: "Clear",
    copy: "Copy",
    placeholder: "Type here...",
    didYouMean: "Did you mean:"
  }
};

const CASE_HINTS_PL = {
  gen: new Set(['do', 'bez', 'dla', 'od', 'u', 'spośród', 'spod', 'zza', 'koło', 'obok', 'blisko']),
  dat: new Set(['ku', 'dzięki', 'przeciw', 'wbrew']),
  ins: new Set(['z', 'ze', 'nad', 'pod', 'przed', 'między', 'pomiędzy']),
  loc: new Set(['o', 'w', 'we', 'na', 'przy', 'po']),
  acc: new Set(['za', 'przez'])
};

const HARD_BOUNDARY = /^[,.;!?()[\]{}:"„”]+$/;

function pushMapArray(map, key, value) {
  if (!key) return;
  if (!map.has(key)) map.set(key, []);
  map.get(key).push(value);
}

function norm(text) {
  return String(text || '')
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ');
}

function isWord(token) {
  return /^\p{L}+(?:['’\-]\p{L}+)*$/u.test(token || '');
}

function tokenize(text) {
  return String(text || '').match(/\p{L}+(?:['’\-]\p{L}+)*|\d+(?:[.,]\d+)?|\s+|[^\s]/gu) || [];
}

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

function applyCaseToPhrase(phrase, caseType) {
  if (!phrase) return "";
  if (caseType === "upper") return phrase.toUpperCase();
  if (caseType === "title") return phrase.charAt(0).toUpperCase() + phrase.slice(1);
  return phrase;
}

function parseMeta(typeCaseRaw = "") {
  const raw = String(typeCaseRaw || "");
  const low = raw.toLowerCase();
  const lemmaMatch = raw.match(/:\s*"([^"]+)"/);

  let pos = null;
  if (
    low.includes("phrase") ||
    low.includes("rěčen") ||
    low.includes("rečen") ||
    low.includes("sentence")
  ) pos = "phrase";
  else if (low.includes("noun") || low.includes("jimenьnik")) pos = "noun";
  else if (
    low.includes("adjective") ||
    low.includes("prilog") ||
    low.includes("prid")
  ) pos = "adjective";
  else if (low.includes("verb") || low.includes("glagol")) pos = "verb";
  else if (low.includes("adverb") || low.includes("narěč")) pos = "adverb";
  else if (low.includes("pronoun") || low.includes("mestoimen")) pos = "pronoun";
  else if (low.includes("preposition") || low.includes("prědlog")) pos = "preposition";
  else if (low.includes("numeral") || low.includes("ličьnik")) pos = "numeral";

  let grammaticalCase = null;
  if (
    low.includes("nominative") ||
    low.includes("jimenovьnik") ||
    low.includes("jimenitelj")
  ) grammaticalCase = "nom";
  else if (
    low.includes("accusative") ||
    low.includes("vinьnik") ||
    low.includes("vinitelj")
  ) grammaticalCase = "acc";
  else if (
    low.includes("genitive") ||
    low.includes("rodilьnik") ||
    low.includes("roditelj")
  ) grammaticalCase = "gen";
  else if (
    low.includes("locative") ||
    low.includes("městьnik") ||
    low.includes("mестьnik")
  ) grammaticalCase = "loc";
  else if (
    low.includes("dative") ||
    low.includes("měrьnik") ||
    low.includes("měritelj")
  ) grammaticalCase = "dat";
  else if (
    low.includes("instrumental") ||
    low.includes("orǫdьnik") ||
    low.includes("tvoritelj")
  ) grammaticalCase = "ins";
  else if (
    low.includes("vocative") ||
    low.includes("zovanьnik") ||
    low.includes("zovatelj")
  ) grammaticalCase = "voc";

  let number = null;
  if (low.includes("singular") || low.includes("poedinьna")) number = "sg";
  else if (low.includes("plural") || low.includes("munoga")) number = "pl";

  let gender = null;
  if (low.includes("masculine") || low.includes("mǫžьsky") || low.includes("muzsky")) gender = "m";
  else if (low.includes("feminine") || low.includes("ženьsky") || low.includes("zensky")) gender = "f";
  else if (low.includes("neuter") || low.includes("nijaky")) gender = "n";

  let animacy = null;
  if (low.includes("(animate)") || low.includes("(život") || low.includes("(zivot")) animacy = "anim";
  else if (low.includes("(inanimate)") || low.includes("(neživot") || low.includes("(nezivot")) animacy = "inan";

  return {
    pos,
    case: grammaticalCase,
    number,
    gender,
    animacy,
    lemma: lemmaMatch ? norm(lemmaMatch[1]) : null,
    raw
  };
}

function buildEntry(item, sourceName) {
  if (!item || !item.polish || !item.slovian) return null;

  const polish = String(item.polish).trim();
  const slovian = String(item.slovian).trim();
  if (!polish || !slovian) return null;

  const meta = parseMeta(
    item["type and case"] || (sourceName === "example_sentences" ? "phrase - rěčenьje" : "")
  );

  return {
    source: sourceName,
    polish,
    slovian,
    npl: norm(polish),
    nslo: norm(slovian),
    context: String(item.context || "").trim(),
    meta,
    raw: item
  };
}

function addEntryToEngine(entry) {
  engine.entries.push(entry);

  pushMapArray(engine.exactPL, entry.npl, entry);
  pushMapArray(engine.exactSLO, entry.nslo, entry);

  if (entry.meta.pos && entry.meta.pos !== "phrase") {
    wordTypes[entry.nslo] = entry.meta.pos;
  }

  const isPhrase =
    entry.meta.pos === "phrase" ||
    /\s/.test(entry.npl) ||
    /\s/.test(entry.nslo);

  if (isPhrase) {
    pushMapArray(engine.phrasePL, entry.npl, entry);
    pushMapArray(engine.phraseSLO, entry.nslo, entry);
  }

  const looksLikeLemma =
    entry.meta.pos &&
    entry.meta.pos !== "phrase" &&
    (!entry.meta.case || entry.meta.case === "nom");

  if (looksLikeLemma) {
    pushMapArray(engine.lemmaPL, entry.npl, entry);
    pushMapArray(engine.lemmaSLO, entry.nslo, entry);
  }
}

function deriveTransform(fromForm, toForm) {
  const a = norm(fromForm);
  const b = norm(toForm);

  let left = 0;
  while (left < a.length && left < b.length && a[left] === b[left]) left++;

  let rightA = a.length - 1;
  let rightB = b.length - 1;
  while (rightA >= left && rightB >= left && a[rightA] === b[rightB]) {
    rightA--;
    rightB--;
  }

  return {
    fromSuffix: a.slice(left),
    toSuffix: b.slice(left),
    commonPrefixLength: left
  };
}

function reverseApplyRule(form, lemmaSuffix, formSuffix) {
  const word = norm(form);
  if (!word.endsWith(formSuffix)) return null;
  return word.slice(0, word.length - formSuffix.length) + lemmaSuffix;
}

function forwardApplyRule(lemma, lemmaSuffix, formSuffix) {
  const base = norm(lemma);
  if (!base.endsWith(lemmaSuffix)) return null;
  return base.slice(0, base.length - lemmaSuffix.length) + formSuffix;
}

function chooseBaseRow(rows) {
  return (
    rows.find(r => r.meta.case === "nom" && r.meta.number === "sg") ||
    rows.find(r => r.meta.case === "nom" && r.meta.number === "pl") ||
    rows[0] ||
    null
  );
}

function buildInflectionRules(vuzorEntries) {
  const groups = new Map();

  for (const entry of vuzorEntries) {
    const key = [
      entry.meta.pos || "",
      entry.meta.lemma || entry.nslo,
      entry.context || "",
      entry.meta.gender || "",
      entry.meta.animacy || ""
    ].join("|");
    pushMapArray(groups, key, entry);
  }

  const seenPL = new Set();
  const seenSLO = new Set();

  for (const rows of groups.values()) {
    const base = chooseBaseRow(rows);
    if (!base) continue;

    for (const row of rows) {
      if (!row.meta.pos || !row.meta.case || !row.meta.number) continue;

      const pl = deriveTransform(base.polish, row.polish);
      const slo = deriveTransform(base.slovian, row.slovian);

      const plRule = {
        pos: row.meta.pos,
        case: row.meta.case,
        number: row.meta.number,
        gender: row.meta.gender,
        animacy: row.meta.animacy,
        lemmaSuffixPL: pl.fromSuffix,
        formSuffixPL: pl.toSuffix,
        lemmaSuffixSLO: slo.fromSuffix,
        formSuffixSLO: slo.toSuffix,
        baseLemmaPL: base.npl,
        baseLemmaSLO: base.nslo,
        scoreBase: pl.commonPrefixLength + slo.commonPrefixLength
      };

      const plKey = [
        plRule.pos,
        plRule.case,
        plRule.number,
        plRule.gender || "",
        plRule.animacy || "",
        plRule.lemmaSuffixPL,
        plRule.formSuffixPL,
        plRule.lemmaSuffixSLO,
        plRule.formSuffixSLO
      ].join("|");

      if (!seenPL.has(plKey)) {
        seenPL.add(plKey);
        engine.rulesPLtoSLO.push(plRule);
      }

      const sloRule = {
        pos: row.meta.pos,
        case: row.meta.case,
        number: row.meta.number,
        gender: row.meta.gender,
        animacy: row.meta.animacy,
        lemmaSuffixSLO: slo.fromSuffix,
        formSuffixSLO: slo.toSuffix,
        lemmaSuffixPL: pl.fromSuffix,
        formSuffixPL: pl.toSuffix,
        baseLemmaSLO: base.nslo,
        baseLemmaPL: base.npl,
        scoreBase: pl.commonPrefixLength + slo.commonPrefixLength
      };

      const sloKey = [
        sloRule.pos,
        sloRule.case,
        sloRule.number,
        sloRule.gender || "",
        sloRule.animacy || "",
        sloRule.lemmaSuffixSLO,
        sloRule.formSuffixSLO,
        sloRule.lemmaSuffixPL,
        sloRule.formSuffixPL
      ].join("|");

      if (!seenSLO.has(sloKey)) {
        seenSLO.add(sloKey);
        engine.rulesSLOtoPL.push(sloRule);
      }
    }
  }
}

function collectPrepositionHintsPL(tokens, index) {
  const hints = new Set();
  let wordsSeen = 0;

  for (let i = index - 1; i >= 0; i--) {
    const token = tokens[i];

    if (/^\s+$/.test(token)) continue;
    if (HARD_BOUNDARY.test(token)) break;
    if (!isWord(token)) break;

    const w = norm(token);
    for (const [gramCase, preps] of Object.entries(CASE_HINTS_PL)) {
      if (preps.has(w)) hints.add(gramCase);
    }

    wordsSeen++;
    if (wordsSeen >= 4) break;
  }

  return hints;
}

function getNearbyWords(tokens, index) {
  const words = [];
  for (let i = Math.max(0, index - 3); i <= Math.min(tokens.length - 1, index + 3); i++) {
    if (i !== index && isWord(tokens[i])) words.push(norm(tokens[i]));
  }
  return words;
}

function getPolishEndingHints(word) {
  const w = norm(word);
  const caseHints = new Set();
  const numberHints = new Set();

  if (/ami$/.test(w)) {
    caseHints.add("ins");
    numberHints.add("pl");
  }

  if (/(ach|ech|ich|ych)$/.test(w)) {
    caseHints.add("loc");
    numberHints.add("pl");
  }

  if (/om$/.test(w)) {
    caseHints.add("dat");
    numberHints.add("pl");
  }

  if (/(ów|ew)$/.test(w)) {
    caseHints.add("gen");
    numberHints.add("pl");
  }

  if (/ę$/.test(w)) {
    caseHints.add("acc");
    numberHints.add("sg");
  }

  if (/ą$/.test(w)) {
    caseHints.add("ins");
    caseHints.add("acc");
    numberHints.add("sg");
  }

  if (/ego$/.test(w)) {
    caseHints.add("gen");
    caseHints.add("acc");
    numberHints.add("sg");
  }

  if (/emu$/.test(w)) {
    caseHints.add("dat");
    numberHints.add("sg");
  }

  if (/(ym|im)$/.test(w)) {
    caseHints.add("ins");
    caseHints.add("loc");
  }

  if (/ej$/.test(w)) {
    caseHints.add("gen");
    caseHints.add("dat");
    caseHints.add("loc");
    numberHints.add("sg");
  }

  if (/owi$/.test(w)) {
    caseHints.add("dat");
    numberHints.add("sg");
  }

  if (/u$/.test(w)) {
    caseHints.add("gen");
    caseHints.add("dat");
    caseHints.add("loc");
  }

  if (/(i|y)$/.test(w) && w.length > 2) {
    numberHints.add("pl");
  }

  return { caseHints, numberHints };
}

function getMorphHintsPL(tokens, index) {
  const prepHints = collectPrepositionHintsPL(tokens, index);
  const endHints = getPolishEndingHints(tokens[index] || "");
  const caseHints = new Set([...prepHints, ...endHints.caseHints]);
  const numberHints = new Set([...endHints.numberHints]);

  return { caseHints, numberHints };
}

function chooseBestCandidate(candidates, direction, ctx = {}) {
  if (!candidates || !candidates.length) return null;

  let best = candidates[0];
  let bestScore = -Infinity;

  for (const candidate of candidates) {
    let score = 0;

    if (candidate.source === "vuzor") score += 7;
    if (candidate.source === "example_sentences") score += 3;

    if (candidate.meta && candidate.meta.case && ctx.caseHints && ctx.caseHints.has(candidate.meta.case)) {
      score += 8;
    }

    if (candidate.meta && candidate.meta.number && ctx.numberHints && ctx.numberHints.has(candidate.meta.number)) {
      score += 4;
    }

    if (candidate.meta && candidate.meta.pos && ctx.expectedPos && candidate.meta.pos === ctx.expectedPos) {
      score += 2;
    }

    if (candidate.meta && candidate.meta.case === "nom" && (!ctx.caseHints || ctx.caseHints.size === 0)) {
      score += 1;
    }

    if (candidate.context && ctx.nearbyWords && ctx.nearbyWords.length) {
      const cctx = norm(candidate.context);
      if (ctx.nearbyWords.some(w => cctx.includes(w))) score += 2;
    }

    if (direction === "pl2slo" && candidate.slovian) score += Math.min(candidate.slovian.length / 120, 0.5);
    if (direction === "slo2pl" && candidate.polish) score += Math.min(candidate.polish.length / 120, 0.5);

    if (score > bestScore) {
      bestScore = score;
      best = candidate;
    }
  }

  return best;
}

function inferPLtoSLO(word, ctx = {}) {
  const w = norm(word);
  let best = null;
  let bestScore = -Infinity;

  for (const rule of engine.rulesPLtoSLO) {
    const lemmaPL = reverseApplyRule(w, rule.lemmaSuffixPL, rule.formSuffixPL);
    if (!lemmaPL) continue;

    const lemmaCandidates = engine.lemmaPL.get(lemmaPL);
    if (!lemmaCandidates || !lemmaCandidates.length) continue;

    for (const lemmaEntry of lemmaCandidates) {
      if (lemmaEntry.meta.pos && rule.pos && lemmaEntry.meta.pos !== rule.pos) continue;

      const formed = forwardApplyRule(
        lemmaEntry.nslo,
        rule.lemmaSuffixSLO,
        rule.formSuffixSLO
      );

      if (!formed) continue;

      let score = rule.scoreBase;
      score += rule.formSuffixPL.length * 2;
      score += rule.lemmaSuffixPL.length;
      if (ctx.caseHints && rule.case && ctx.caseHints.has(rule.case)) score += 8;
      if (ctx.numberHints && rule.number && ctx.numberHints.has(rule.number)) score += 4;
      if (lemmaEntry.source === "osnova") score += 2;
      if (lemmaEntry.meta.gender && rule.gender && lemmaEntry.meta.gender === rule.gender) score += 2;

      if (score > bestScore) {
        bestScore = score;
        best = formed;
      }
    }
  }

  return best;
}

function inferSLOtoPL(word) {
  const w = norm(word);
  let best = null;
  let bestScore = -Infinity;

  for (const rule of engine.rulesSLOtoPL) {
    const lemmaSLO = reverseApplyRule(w, rule.lemmaSuffixSLO, rule.formSuffixSLO);
    if (!lemmaSLO) continue;

    const lemmaCandidates = engine.lemmaSLO.get(lemmaSLO);
    if (!lemmaCandidates || !lemmaCandidates.length) continue;

    for (const lemmaEntry of lemmaCandidates) {
      if (lemmaEntry.meta.pos && rule.pos && lemmaEntry.meta.pos !== rule.pos) continue;

      const formed = forwardApplyRule(
        lemmaEntry.npl,
        rule.lemmaSuffixPL,
        rule.formSuffixPL
      );

      if (!formed) continue;

      let score = rule.scoreBase;
      score += rule.formSuffixSLO.length * 2;
      score += rule.lemmaSuffixSLO.length;
      if (lemmaEntry.source === "osnova") score += 2;

      if (score > bestScore) {
        bestScore = score;
        best = formed;
      }
    }
  }

  return best;
}

function getLikelyPOSForPL(word) {
  const exact = engine.exactPL.get(norm(word)) || [];
  const lemma = engine.lemmaPL.get(norm(word)) || [];
  const all = [...exact, ...lemma];

  const counts = {};
  for (const item of all) {
    const p = item.meta.pos;
    if (!p) continue;
    counts[p] = (counts[p] || 0) + 1;
  }

  let best = null;
  let score = -1;
  for (const [k, v] of Object.entries(counts)) {
    if (v > score) {
      score = v;
      best = k;
    }
  }
  return best;
}

function translateWordPL(word, ctx = {}) {
  const key = norm(word);
  const exact = engine.exactPL.get(key);

  if (exact && exact.length) {
    const best = chooseBestCandidate(exact, "pl2slo", ctx);
    if (best && best.slovian) return applyCase(best.slovian, getCase(word));
  }

  const inferred = inferPLtoSLO(word, ctx);
  if (inferred) return applyCase(inferred, getCase(word));

  return word;
}

function translateWordSLO(word, ctx = {}) {
  const key = norm(word);
  const exact = engine.exactSLO.get(key);

  if (exact && exact.length) {
    const best = chooseBestCandidate(exact, "slo2pl", ctx);
    if (best && best.polish) return applyCase(best.polish, getCase(word));
  }

  const inferred = inferSLOtoPL(word);
  if (inferred) return applyCase(inferred, getCase(word));

  return word;
}

function findLongestPhrase(tokens, startIndex, direction) {
  const phraseMap = direction === "pl2slo" ? engine.phrasePL : engine.phraseSLO;
  if (!isWord(tokens[startIndex])) return null;

  const collectedWords = [];
  let best = null;
  let i = startIndex;

  while (i < tokens.length && collectedWords.length < 10) {
    const token = tokens[i];

    if (/^\s+$/.test(token)) {
      i++;
      continue;
    }

    if (!isWord(token)) break;
    collectedWords.push(token);

    const key = norm(collectedWords.join(" "));
    if (phraseMap.has(key)) {
      const entries = phraseMap.get(key);
      const chosen = chooseBestCandidate(entries, direction, {});
      best = {
        value: direction === "pl2slo" ? chosen.slovian : chosen.polish,
        endIndex: i + 1,
        caseType: getCase(tokens[startIndex])
      };
    }

    i++;
    if (i < tokens.length && !/^\s+$/.test(tokens[i]) && !isWord(tokens[i])) break;
  }

  return best;
}

function reorderSmart(text) {
  if (!text) return "";
  const tokens = text.split(/(\s+|[.,!?;:()=+\-%*/]+)/g).filter(t => t);
  const result = [];

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    const lowToken = token.toLowerCase();

    if (/^[\s.,!?;:()=+\-%*/]+$/.test(token)) {
      result.push(token);
      continue;
    }

    if (wordTypes[lowToken]) {
      const group = [];
      let currentIdx = i;
      const firstWordCase = getCase(tokens[i]);

      while (currentIdx < tokens.length) {
        const currentToken = tokens[currentIdx];

        if (/^[\s]+$/.test(currentToken)) {
          currentIdx++;
          continue;
        }

        const type = wordTypes[currentToken.toLowerCase()];
        if (type === "noun" || type === "adjective" || type === "numeral" || type === "pronoun") {
          group.push({ val: currentToken, type });
          i = currentIdx;
          currentIdx++;
        } else {
          break;
        }
      }

      if (group.length > 1) {
        const order = { numeral: 1, pronoun: 2, adjective: 3, noun: 4 };
        group.sort((a, b) => (order[a.type] || 99) - (order[b.type] || 99));

        group.forEach((word, idx) => {
          let formatted = word.val;
          if (idx === 0) {
            formatted = applyCase(word.val, firstWordCase);
          } else if (firstWordCase === "upper") {
            formatted = word.val.toUpperCase();
          } else {
            formatted = word.val.toLowerCase();
          }

          result.push(formatted);
          if (idx < group.length - 1) result.push(" ");
        });

        continue;
      }
    }

    result.push(token);
  }

  return result.join("");
}

function translateWithEngine(text, direction) {
  const fullKey = norm(text);
  const fullPhrase = direction === "pl2slo"
    ? engine.phrasePL.get(fullKey)
    : engine.phraseSLO.get(fullKey);

  if (fullPhrase && fullPhrase.length) {
    const chosen = chooseBestCandidate(fullPhrase, direction, {});
    return direction === "pl2slo" ? chosen.slovian : chosen.polish;
  }

  const tokens = tokenize(text);
  const out = [];

  for (let i = 0; i < tokens.length;) {
    const token = tokens[i];

    if (/^\s+$/.test(token) || !isWord(token)) {
      out.push(token);
      i++;
      continue;
    }

    const phrase = findLongestPhrase(tokens, i, direction);
    if (phrase) {
      out.push(applyCaseToPhrase(phrase.value, phrase.caseType));
      i = phrase.endIndex;
      continue;
    }

    if (direction === "pl2slo") {
      const hints = getMorphHintsPL(tokens, i);
      const ctx = {
        caseHints: hints.caseHints,
        numberHints: hints.numberHints,
        nearbyWords: getNearbyWords(tokens, i),
        expectedPos: getLikelyPOSForPL(token)
      };
      out.push(translateWordPL(token, ctx));
    } else {
      const ctx = {
        caseHints: new Set(),
        numberHints: new Set(),
        nearbyWords: getNearbyWords(tokens, i),
        expectedPos: null
      };
      out.push(translateWordSLO(token, ctx));
    }

    i++;
  }

  return out.join("");
}

function populateLanguageLists(uiLang, userLocale) {
  const s1 = document.getElementById("srcLang");
  const s2 = document.getElementById("tgtLang");
  if (!s1 || !s2) return;

  let dn;
  try {
    dn = new Intl.DisplayNames([userLocale], { type: "language" });
  } catch (e) {}

  [s1, s2].forEach(s => {
    s.options.length = 0;
    languageData.forEach(l => {
      let name = "";
      if (l.code === "slo") {
        name = l[uiLang] || l.en;
      } else {
        name = dn ? dn.of(l.code) : (l[uiLang] || l.en);
      }

      if (l.code === "sr") name = (uiLang === "pl") ? "Serbski (cyrylica)" : "Serbian (Cyrillic)";
      if (l.code === "sr-Latn") name = (uiLang === "pl") ? "Serbski (łacina)" : "Serbian (Latin)";
      s.add(new Option(name.charAt(0).toUpperCase() + name.slice(1), l.code));
    });
  });
}

async function google(text, s, t) {
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${s}&tl=${t}&dt=t&dt=qca&q=${encodeURIComponent(text)}`;
    const res = await fetch(url);
    const data = await res.json();

    const suggestionBox = document.getElementById("suggestionBox");
    if (suggestionBox) {
      if (data[7] && data[7][1]) {
        const cleanSuggest = data[7][1].replace(/<b>|<\/b>|<i>|<\/i>/g, "");
        const currentUi = document.documentElement.lang || "en";
        const label = uiTranslations[currentUi]?.didYouMean || uiTranslations.en.didYouMean;
        suggestionBox.innerHTML =
          `${label} <span class="suggest-link" onclick="applySuggestion('${cleanSuggest.replace(/'/g, "\\'")}')">${cleanSuggest}</span>`;
        suggestionBox.style.display = "block";
      } else {
        suggestionBox.style.display = "none";
      }
    }

    return data[0].map(x => x[0]).join("");
  } catch (e) {
    return text;
  }
}

function applySuggestion(text) {
  const input = document.getElementById("userInput");
  if (input) {
    input.value = text;
    translate();
  }
}

async function fetchJSONOptional(fileName) {
  try {
    const res = await fetch(fileName);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}

async function loadDictionaries() {
  const status = document.getElementById("dbStatus");

  engine.entries = [];
  engine.exactPL.clear();
  engine.exactSLO.clear();
  engine.lemmaPL.clear();
  engine.lemmaSLO.clear();
  engine.phrasePL.clear();
  engine.phraseSLO.clear();
  engine.rulesPLtoSLO = [];
  engine.rulesSLOtoPL = [];
  wordTypes = {};

  try {
    const fileSpecs = [
      { name: "osnova.json", source: "osnova", required: true },
      { name: "vuzor.json", source: "vuzor", required: true },
      { name: "example_sentences.json", source: "example_sentences", required: false }
    ];

    const vuzorEntries = [];

    for (const spec of fileSpecs) {
      const data = await fetchJSONOptional(spec.name);

      if (!data) {
        if (spec.required) throw new Error(`Missing required file: ${spec.name}`);
        continue;
      }

      if (!Array.isArray(data)) continue;

      for (const item of data) {
        const entry = buildEntry(item, spec.source);
        if (!entry) continue;
        addEntryToEngine(entry);
        if (spec.source === "vuzor") vuzorEntries.push(entry);
      }
    }

    buildInflectionRules(vuzorEntries);
    engine.ready = true;
    if (status) status.innerText = "Engine Ready.";
  } catch (e) {
    engine.ready = false;
    if (status) status.innerText = "Dict Error.";
    console.error("Dictionary load error:", e);
  }
}

async function translate() {
  const input = document.getElementById("userInput");
  const out = document.getElementById("resultOutput");
  if (!input || !out) return;

  const text = input.value || "";
  const src = document.getElementById("srcLang").value;
  const tgt = document.getElementById("tgtLang").value;

  if (!text.trim()) {
    out.innerText = "";
    return;
  }

  try {
    let finalResult = "";

    if (src === tgt) {
      finalResult = text;
    } else if (tgt === "slo") {
      const bridge = (src === "pl") ? text : await google(text, src, "pl");
      const translated = translateWithEngine(bridge, "pl2slo");
      finalResult = reorderSmart(translated);
    } else if (src === "slo") {
      const bridge = translateWithEngine(text, "slo2pl");
      finalResult = (tgt === "pl") ? bridge : await google(bridge, "pl", tgt);
    } else {
      finalResult = await google(text, src, tgt);
    }

    out.innerText = finalResult;
  } catch (e) {
    out.innerText = "Error...";
    console.error("Translate error:", e);
  }
}

async function init() {
  const sysLocale = navigator.language || "en";
  const sysLang = sysLocale.split("-")[0];
  const uiKey = uiTranslations[sysLang] ? sysLang : "en";
  document.documentElement.lang = uiKey;

  applyUI(uiKey);
  populateLanguageLists(uiKey, sysLocale);

  const srcS = document.getElementById("srcLang");
  const tgtS = document.getElementById("tgtLang");

  srcS.value = localStorage.getItem("srcLang") || "pl";
  tgtS.value = localStorage.getItem("tgtLang") || "slo";

  [srcS, tgtS].forEach(s => s.addEventListener("change", () => {
    localStorage.setItem("srcLang", srcS.value);
    localStorage.setItem("tgtLang", tgtS.value);
    translate();
  }));

  await loadDictionaries();
  document.getElementById("userInput")?.addEventListener("input", debounce(translate, 250));
}

function applyUI(lang) {
  const ui = uiTranslations[lang] || uiTranslations.en;
  ["title", "label-from", "label-to", "paste", "clear", "copy"].forEach(id => {
    const el = document.getElementById("ui-" + id);
    if (el) el.innerText = ui[id.replace("label-", "")] || "";
  });

  const input = document.getElementById("userInput");
  if (input) input.placeholder = ui.placeholder;
}

function swapLanguages() {
  const s = document.getElementById("srcLang");
  const t = document.getElementById("tgtLang");
  const i = document.getElementById("userInput");
  const o = document.getElementById("resultOutput");

  [s.value, t.value] = [t.value, s.value];
  localStorage.setItem("srcLang", s.value);
  localStorage.setItem("tgtLang", t.value);

  if (o.innerText.trim()) i.value = o.innerText;
  translate();
}

function clearText() {
  document.getElementById("userInput").value = "";
  document.getElementById("resultOutput").innerText = "";
  const sb = document.getElementById("suggestionBox");
  if (sb) sb.style.display = "none";
}

function copyText() {
  navigator.clipboard.writeText(document.getElementById("resultOutput").innerText);
}

async function pasteText() {
  try {
    document.getElementById("userInput").value = await navigator.clipboard.readText();
    translate();
  } catch (e) {}
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

window.onload = init;
