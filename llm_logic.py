import json
import os

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_grammar_map():
    """Tworzy mapę końcówek na podstawie Twojego pliku vuzor.json."""
    vuzor = load_data('vuzor.json')
    g_map = {}
    for entry in vuzor:
        tag = entry.get('type and case', '').lower()
        # Wyciągamy informację o przypadku i liczbie
        case = "gen" if "genitive" in tag else "nom" if "nominative" in tag else "acc" if "accusative" in tag else "loc" if "locative" in tag else "dat" if "dative" in tag else "ins" if "instrumental" in tag else "nom"
        num = "pl" if "plural" in tag else "sg"
        gender = "fem" if "feminine" in tag else "neut" if "neuter" in tag else "masc"
        
        type_key = f"noun_{gender}"
        if type_key not in g_map: g_map[type_key] = {}
        
        # Zapisujemy końcówkę (ostatnie litery słowa słowiańskiego)
        s_word = entry.get('slovian', '')
        if s_word:
            end = s_word[-1] if s_word[-1] in 'ъaьoeyęǫ' else s_word[-2:]
            g_map[type_key][f"{num}_{case}"] = end
    return g_map

def learn():
    """Uczy się rdzeni i przypisuje je do polskich słów."""
    examples = load_data('example_sentences.json')
    osnova = load_data('osnova.json')
    g_map = get_grammar_map()
    
    # Tworzymy słownik rdzeni
    for ex in examples:
        p_word = ex.get('polish', '').lower()
        s_word = ex.get('slovian', '')
        if not p_word or not s_word: continue
        
        # Proste odcięcie rdzenia
        stem = s_word[:-1] if s_word[-1] in 'ъaьoey' else s_word
        
        # Szukamy czy już mamy to słowo
        match = next((i for i in osnova if i['polish'] == p_word), None)
        if not match:
            osnova.append({
                "polish": p_word,
                "slovian": s_word,
                "stem": stem,
                "type": "noun_masc" if s_word.endswith('ъ') else "noun_fem" if s_word.endswith('a') else "noun_neut"
            })
            
    save_data(osnova, 'osnova.json')

def translate_word_smart(polish_input):
    """
    To jest funkcja, która powinna być w Twoim głównym translatorze.
    Rozpoznaje polskie końcówki i dobiera słowiańskie.
    """
    osnova = load_data('osnova.json')
    g_map = get_grammar_map()
    
    # 1. Znajdź bazę (np. dla 'domów' znajdź 'dom')
    # Tutaj potrzebna byłaby lista polskich odmian, ale na razie szukamy rdzenia
    for item in osnova:
        if polish_input.startswith(item['polish'][:3]): # Prosty match rdzenia
            stem = item['stem']
            w_type = item['type']
            
            # 2. Rozpoznaj przypadek po polskiej końcówce
            p_end = polish_input[-2:]
            case_key = "sg_nom"
            if p_end == "ów": case_key = "pl_gen"
            elif p_end == "ami": case_key = "pl_ins"
            elif p_end == "ie": case_key = "sg_loc"
            
            # 3. Złóż słowo
            suffix = g_map.get(w_type, {}).get(case_key, "")
            return stem + suffix
            
    return polish_input

if __name__ == "__main__":
    learn()
