let plToSlo = {}, sloToPl = {};
let wordTypes = {};
let wordCases = {}; // tu będziemy trzymać odmiany

const languageData = [
    { code: 'slo', slo: 'Slověnьsky', pl: 'Słowiański', en: 'Slovian (Slavic)' },
    { code: 'pl', pl: 'Polski', slo: "Pol'ьsky", en: 'Polish' },
    { code: 'en', pl: 'Angielski', slo: "Angol'ьsky", en: 'English' }
];

// --- UI Translations ---
const uiTranslations = {
    pl: { title: "Slovo Tłumacz", from: "Z języka:", to: "Na język:", paste: "Wklej", clear: "Usuń", copy: "Kopiuj", placeholder: "Wpisz tekst..." },
    slo: { title: "Slovo Perkladačь", from: "Jiz ęzyka:", to: "Na ęzyk:", paste: "Vyloži", clear: "Terbi", copy: "Poveli", placeholder: "Piši tu..." },
    en: { title: "Slovo Translator", from: "From language:", to: "To language:", paste: "Paste", clear: "Clear", copy: "Copy", placeholder: "Type here..." }
};

// --- Populate Language Dropdowns ---
function populateLanguageLists(uiLang, userLocale) {
    const s1 = document.getElementById('srcLang'), s2 = document.getElementById('tgtLang');
    [s1, s2].forEach(s => s.options.length = 0);

    languageData.forEach(l => {
        let name = l[uiLang] || l.en || l.slo;
        [s1, s2].forEach(sel => sel.add(new Option(name, l.code)));
    });
}

// --- Case Handling ---
function getCase(word){
    if(!word) return "lower";
    if(word===word.toUpperCase() && word.length>1) return "upper";
    if(word[0]===word[0].toUpperCase()) return "title";
    return "lower";
}
function applyCase(word, caseType){
    if(!word) return "";
    switch(caseType){
        case "upper": return word.toUpperCase();
        case "title": return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
        default: return word.toLowerCase();
    }
}

// --- Full Word Flexion (Fleksja) ---
function flexWord(word){
    const lower = word.toLowerCase();
    if(wordCases[lower]) return wordCases[lower]; // jeśli już mamy
    // prosty placeholder: tworzymy odmiany przez 7 przypadków
    const cases=["nom","gen","dat","acc","inst","loc","voc"];
    let flex={};
    cases.forEach(c=>{
        flex[c] = applyCase(word, getCase(word)); // tu możesz dodać realne reguły odmiany
    });
    wordCases[lower]=flex;
    return flex;
}

// --- Dict Replace z fleksją ---
function dictReplaceWithFlex(text, dict){
    if(!text) return "";
    const tokens = text.split(/(\s+|[.,!?;:()=+\-%*/]+)/g).filter(t=>t!=="");
    return tokens.map(tok=>{
        const low = tok.toLowerCase();
        if(dict[low]){
            const flex = flexWord(dict[low]);
            return flex.nom; // domyślnie używamy mianownika
        }
        return tok;
    }).join("");
}

// --- Smart Reorder ---
function reorderSmart(text){
    if(!text) return "";
    const tokens = text.split(/(\s+|[.,!?;:()=+\-%*/]+)/g).filter(t=>t!=="");
    const result=[];
    for(let i=0;i<tokens.length;i++){
        let token = tokens[i];
        if(wordTypes[token.toLowerCase()]){
            let group=[], firstCase=getCase(token);
            while(i<tokens.length){
                let t=tokens[i];
                if(wordTypes[t.toLowerCase()]) group.push(t);
                else break;
                i++;
            }
            group.sort((a,b)=>{
                const order = {numeral:1, adjective:2, noun:3};
                return (order[wordTypes[a.toLowerCase()]]||99)-(order[wordTypes[b.toLowerCase()]]||99);
            });
            group.forEach((w,idx)=> result.push(idx===0?applyCase(w,firstCase):w));
            i--;
        } else result.push(token);
    }
    return result.join("");
}

// --- Hybrid PL→SLO Translation with Ollama + fleksja ---
async function hybridTranslatePLtoSLO(text){
    let translated = dictReplaceWithFlex(text, plToSlo);
    translated = reorderSmart(translated);

    try{
        const res = await fetch("http://localhost:11434/api/generate",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({
                model:"qwen",
                prompt:`Przetłumacz na starosłowiański zachowując wszystkie przypadki, fleksję, szyk zdania i sens. Tekst: "${text}"`,
                max_output_tokens:512
            })
        });
        if(res.ok){
            const data = await res.json();
            if(data && data.response) translated = reorderSmart(data.response);
        }
    }catch(e){ console.log("Ollama error:",e); }

    return translated;
}

// --- Main Translate ---
async function translate(){
    const input=document.getElementById('userInput');
    const out=document.getElementById('resultOutput');
    if(!input||!out) return;
    const text=input.value;
    const src=document.getElementById('srcLang').value;
    const tgt=document.getElementById('tgtLang').value;

    if(!text.trim()){ out.innerText=""; return; }
    try{
        let finalResult="";
        if(src==='pl'&&tgt==='slo') finalResult = await hybridTranslatePLtoSLO(text);
        else if(src==='slo'&&tgt==='pl') finalResult = dictReplaceWithFlex(text,sloToPl);
        else finalResult = text; // fallback: tu możesz dodać Google Translate
        out.innerText=finalResult;
    }catch(e){ out.innerText="Error..."; }
}

// --- Load Dictionaries ---
async function loadDictionaries(){
    try{
        const files=['osnova.json','vuzor.json'];
        for(const file of files){
            const res = await fetch(file);
            if(res.ok){
                const data=await res.json();
                data.forEach(item=>{
                    if(item.polish && item.slovian){
                        const pl=item.polish.toLowerCase().trim();
                        const slo=item.slovian.toLowerCase().trim();
                        plToSlo[pl]=item.slovian.trim();
                        sloToPl[slo]=item.polish.trim();
                        if(item["type and case"]){
                            const info=item["type and case"].toLowerCase();
                            if(info.includes("jimenьnik")||info.includes("noun")) wordTypes[slo]="noun";
                            if(info.includes("priloga")||info.includes("adjective")) wordTypes[slo]="adjective";
                            if(info.includes("ličьnik")||info.includes("numeral")) wordTypes[slo]="numeral";
                        }
                    }
                });
            }
        }
        document.getElementById('dbStatus').innerText="Engine Ready.";
    }catch(e){ document.getElementById('dbStatus').innerText="Dict Error.";}
}

// --- UI Helpers ---
function applyUI(lang){
    const ui=uiTranslations[lang]||uiTranslations.en;
    ['title','from','to','paste','clear','copy'].forEach(id=>{
        const el=document.getElementById('ui-'+id);
        if(el) el.innerText=ui[id]||"";
    });
    const input=document.getElementById('userInput');
    if(input) input.placeholder=ui.placeholder;
}
function swapLanguages(){
    const src=document.getElementById('srcLang'), tgt=document.getElementById('tgtLang');
    [src.value,tgt.value]=[tgt.value,src.value];
    translate();
}
function clearText(){
    document.getElementById('userInput').value="";
    document.getElementById('resultOutput').innerText="";
}
function copyText(){
    const text=document.getElementById('resultOutput').innerText;
    navigator.clipboard.writeText(text);
}
async function pasteText(){
    try{
        const text=await navigator.clipboard.readText();
        document.getElementById('userInput').value=text;
        translate();
    }catch(e){ console.log("Clipboard error");}
}
function debounce(func, wait){
    let timeout;
    return function(){ clearTimeout(timeout); timeout=setTimeout(()=>func.apply(this,arguments),wait); }
}

// --- Init ---
async function init(){
    const sysLocale=navigator.language||'en';
    const sysLang=sysLocale.split('-')[0];
    const uiKey=uiTranslations[sysLang]?sysLang:'en';
    applyUI(uiKey);
    populateLanguageLists(uiKey, sysLocale);

    const savedSrc='pl', savedTgt='slo';
    document.getElementById('srcLang').value=savedSrc;
    document.getElementById('tgtLang').value=savedTgt;

    document.getElementById('srcLang').addEventListener('change',translate);
    document.getElementById('tgtLang').addEventListener('change',translate);

    await loadDictionaries();

    const userInput=document.getElementById('userInput');
    if(userInput) userInput.addEventListener('input', debounce(translate,300));
}
window.onload=init;
