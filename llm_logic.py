import json
import os

def load_json_file(filename):
    """Bezpieczne wczytywanie plików JSON."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"BŁĄD: Nie można odczytać pliku {filename}. Sprawdź składnię JSON.")
                return []
    return []

def save_json_file(data, filename):
    """Zapisywanie danych do JSON z zachowaniem porządku."""
    if filename == 'osnova.json':
        # Sortowanie alfabetyczne po polskim haśle
        data = sorted(data, key=lambda x: x.get('polish', '').lower())
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_stem(slovian_word):
    """
    Wyciąga rdzeń słowa prasłowiańskiego (slověnьsky ęzyk).
    Odcina typowe końcówki mianownika: ъ, a, o, e, ь.
    """
    endings = ['ъ', 'a', 'o', 'e', 'ь']
    for end in endings:
        if slovian_word.endswith(end):
            return slovian_word[:-len(end)]
    return slovian_word

def learn_from_example_sentences(example_file='example_sentences.json'):
    """
    Główny proces nauki: 
    Rozbija przykłady na rdzenie i przypisuje im kategorie z Twojej tabeli.
    """
    examples = load_json_file(example_file)
    if not examples:
        return

    osnova = load_json_file('osnova.json')
    
    # Mapa istniejących haseł, żeby nie dublować
    existing_map = {item.get('polish', '').lower(): item for item in osnova}

    for ex in examples:
        p_phrase = ex.get('polish', '').lower().strip()
        s_phrase = ex.get('slovian', '').strip()
        
        # Logika dla pojedynczych słów (jeśli przykład to słowo) 
        # lub próba wyciągnięcia kluczowych słów z frazy.
        if p_phrase and s_phrase:
            if p_phrase not in existing_map:
                # Tworzymy nowy wpis typu 'osnova'
                new_entry = {
                    "polish": p_phrase,
                    "slovian": s_phrase,
                    "stem": extract_stem(s_phrase),
                    "type": ex.get("type", "noun"),
                    "case_info": ex.get("case", "nominative"),
                    "context": ex.get("context", "")
                }
                osnova.append(new_entry)
                existing_map[p_phrase] = new_entry
                print(f"Silnik Slovo: Nauczyłem się rdzenia dla: {p_phrase}")

    save_json_file(osnova, 'osnova.json')

def translate_word(polish_word, target_case='nom', target_num='sg'):
    """
    Funkcja, którą powinien wywoływać Twój translator na stronie.
    Łączy rdzeń z osnova.json z wzorcem z vuzor.json.
    """
    osnova = load_json_file('osnova.json')
    vuzor = load_json_file('vuzor.json')
    
    # Szukaj słowa w bazie
    entry = next((i for i in osnova if i['polish'].lower() == polish_word.lower()), None)
    
    if not entry or 'stem' not in entry:
        return polish_word # Jeśli nie znamy rdzenia, zostawiamy polski (fallback)

    # Pobierz typ odmiany (np. noun_masc_hard)
    w_type = entry.get('type', 'noun_masc_hard')
    
    try:
        # Próba dopasowania końcówki z vuzor.json
        suffix = vuzor[w_type][target_num][target_case]
        return entry['stem'] + suffix
    except (KeyError, TypeError):
        # Jeśli nie ma wzorca, zwróć formę podstawową (slovian)
        return entry.get('slovian', polish_word)

if __name__ == "__main__":
    learn_from_example_sentences()
