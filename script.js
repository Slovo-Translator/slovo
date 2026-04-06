let plToSlo = {}, sloToPl = {};
let wordTypes = {};
const languageData = [
    { code: 'slo', slo: 'Slověnьsky', pl: 'Słowiański', en: 'Slovian (Slavic)' },
    { code: 'pl', pl: 'Polski', slo: "Pol'ьsky", en: 'Polish' },
    { code: 'en', pl: 'Angielski', slo: "Angol'ьsky", en: 'English' },
    { code: 'de', pl: 'Niemiecki', slo: 'Nemьčьsky', en: 'German' },
    { code: 'cs', pl: 'Czeski', slo: 'Češьsky', en: 'Czech' },
    { code: 'sk', pl: 'Słowacki', slo: 'Slovačьsky', en: 'Slovak' },
    { code: 'ru', pl: 'Rosyjski', slo: 'Rusьsky', en: 'Russian' },
    { code: 'fr', pl: 'Francuski', slo: 'Franьsky', en: 'French' },
    { code: 'es', pl: 'Hiszpański', slo: 'Španьsky', en: 'Spanish' },
    { code: 'it', pl: 'Włoski', slo: 'Volšьsky', en: 'Italian' },
    { code: 'uk', pl: 'Ukraiński', slo: 'Ukrajinьsky', en: 'Ukrainian' }
];

const uiTranslations = {
    pl: { title: "Slovo Tłumacz", from: "Z języka:", to: "Na język:", paste: "Wklej", clear: "Usuń", copy: "Kopiuj", placeholder: "Wpisz tekst..." },
    slo: { title: "Slovo Perkladačь", from: "Jiz ęzyka:", to: "Na ęzyk:", paste: "Vyloži", clear: "Terbi", copy: "Poveli", placeholder: "Piši tu..." },
    en: { title: "Slovo Translator", from: "From language:", to: "To language:", paste: "Paste", clear: "Clear", copy: "Copy", placeholder: "Type here..." }
};

// --- Populate Language Lists ---
function populateLanguageLists(uiLang, userLocale) {
    const s1 = document.getElementById('srcLang'), s2 = document.getElementById('tgtLang');
    if (!s1 || !s2) return;
    [s1, s2].forEach(s => s.options.length = 0);

    let dn;
    try { dn = new Intl.DisplayNames([userLocale], { type: 'language' }); } catch(e){}

    languageData.forEach(l => {
        let name = l[uiLang] || l.en || l.slo;
        if(dn && l.code !== 'slo'){
            try{ name = dn.of(l.code); } catch(e){ name = l[uiLang] || l.en || l.code; }
        }
        name = name.charAt(0).toUpperCase() + name.slice(1);
        [s1, s2].forEach(sel => sel.add(new Option(name, l.code)));
    });
}

// --- Case Functions ---
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

// --- Dict Replace ---
function dictReplace(text, dict){
    if(!text) return "";
    const urlRegex = /(https?:\/\/[^\s]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
    let placeholders = [];
    let tempText = text.replace(urlRegex,(match)=>{placeholders.push(match); return `__URL_PH_${placeholders.length-1}__`;});
    tempText = tempText.replace(/[a-ząćęłńóśźżěьъ']+/gi,(word)=>{
        const lowWord = word.toLowerCase();
        if(dict[lowWord]) return applyCase(dict[lowWord], getCase(word));
        return word;
    });
    return tempText.replace(/__URL_PH_(\d+)__/g,(match,id)=>placeholders[id]);
}

// --- Smart Reorder ---
function reorderSmart(text){
    if(!text) return "";
    const tokens = text.split(/(\s+|[.,!?;:()=+\-%*/]+)/g).filter(t=>t!=="");
    const result = [];

    for(let i=0;i<tokens.length;i++){
        let token = tokens[i];
        let lowToken = token.toLowerCase();

        if(/^[\s.,!?;:()=+\-%*/]+$/.test(token)){ result.push(token); continue; }

        if(wordTypes[lowToken]){
            let group = [], currentIdx=i;
            let firstWordCase = getCase(tokens[i]);

            while(currentIdx<tokens.length){
                let currentToken = tokens[currentIdx];
                if(/^[\s]+$/.test(currentToken)){ currentIdx++; continue; }
                let type = wordTypes[currentToken.toLowerCase()];
                if(type==="noun"||type==="adjective"||type==="numeral"){
                    group.push({val: currentToken,type:type});
                    i=currentIdx; currentIdx++;
                } else break;
            }

            if(group.length>1){
                const order = {numeral:1, adjective:2, noun:3};
                group.sort((a,b)=>(order[a.type]||99)-(order[b.type]||99));
                group.forEach((word,index)=>{
                    let formattedWord = word.val.toLowerCase();
                    if(index===0) formattedWord=applyCase(word.val,firstWordCase);
                    else if(firstWordCase==="upper") formattedWord=word.val.toUpperCase();
                    result.push(formattedWord);
                    if(index<group.length-1) result.push(" ");
                });
                continue;
            } else if(group.length===1){ result.push(token); continue; }
        }
        result.push(token);
    }
    return result.join("");
}

// --- Hybrid PL->SLO Translation with Ollama ---
async function hybridTranslatePLtoSLO(text){
    let translated = dictReplace(text, plToSlo);
    translated = reorderSmart(translated);

    try{
        const res = await fetch("http://localhost:11434/api/generate",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({
                model:"qwen",
                prompt:`Przetłumacz na starosłowiański zachowując przypadki, szyk zdania i sens. Tekst: "${text}"`,
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
        else if(src==='slo'&&tgt==='pl') finalResult = dictReplace(text,sloToPl);
        else if(src==='slo'){ 
            const bridge=dictReplace(text,sloToPl);
            finalResult = await google(bridge,'pl',tgt);
        } else if(tgt==='slo'){
            const bridge = await google(text, src,'pl');
            finalResult = reorderSmart(dictReplace(bridge,plToSlo));
        } else finalResult = await google(text,src,tgt);

        out.innerText=finalResult;
    }catch(e){ out.innerText="Error..."; }
}

// --- Google Fallback ---
async function google(text,src,tgt){
    try{
        const url=`https://translate.googleapis.com/translate_a/single?client=gtx&sl=${src}&tl=${tgt}&dt=t&q=${encodeURIComponent(text)}`;
        const res = await fetch(url);
        const data = await res.json();
        return data[0].map(x=>x[0]).join('');
    }catch(e){ return text; }
}

// --- Load Dictionaries ---
async function loadDictionaries(){
    const status=document.getElementById('dbStatus');
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
        if(status) status.innerText="Engine Ready.";
    }catch(e){ if(status) status.innerText="Dict Error.";}
}

// --- UI Helpers ---
function applyUI(lang){
    const ui=uiTranslations[lang]||uiTranslations.en;
    const ids=['ui-title','ui-label-from','ui-label-to','ui-paste','ui-clear','ui-copy'];
    ids.forEach(id=>{
        const el=document.getElementById(id);
        if(el) el.innerText=ui[id.replace('ui-','')]||"";
    });
    const input=document.getElementById('userInput');
    if(input) input.placeholder=ui.placeholder;
}

function swapLanguages(){
    const src=document.getElementById('srcLang'), tgt=document.getElementById('tgtLang');
    [src.value,tgt.value]=[tgt.value,src.value];
    localStorage.setItem('srcLang', src.value);
    localStorage.setItem('tgtLang', tgt.value);
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

// --- Debounce ---
function debounce(func, wait){
    let timeout;
    return function(){
        clearTimeout(timeout);
        timeout=setTimeout(()=>func.apply(this,arguments),wait);
    }
}

// --- Init ---
async function init(){
    const sysLocale=navigator.language||'en';
    const sysLang=sysLocale.split('-')[0];
    const uiKey=uiTranslations[sysLang]?sysLang:'en';
    applyUI(uiKey);
    populateLanguageLists(uiKey, sysLocale);

    const savedSrc=localStorage.getItem('srcLang')||(languageData.some(l=>l.code===sysLang)?sysLang:'pl');
    const savedTgt=localStorage.getItem('tgtLang')||'slo';
    const srcSelect=document.getElementById('srcLang');
    const tgtSelect=document.getElementById('tgtLang');

    if(srcSelect){
        srcSelect.value=savedSrc;
        srcSelect.addEventListener('change',(e)=>{
            localStorage.setItem('srcLang', e.target.value);
            translate();
        });
    }
    if(tgtSelect){
        tgtSelect.value=savedTgt;
        tgtSelect.addEventListener('change',(e)=>{
            localStorage.setItem('tgtLang', e.target.value);
            translate();
        });
    }

    await loadDictionaries();

    const userInput=document.getElementById('userInput');
    if(userInput) userInput.addEventListener('input', debounce(translate,300));
}

window.onload = init;
