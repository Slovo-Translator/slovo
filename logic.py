import json
import re

class SlovianLogic:
    def __init__(self):
        self.osnova = self._load_json('osnova.json')
        self.vuzor = self._load_json('vuzor.json')
        
        # Reguły transformacji fonetycznej (tzw. Sound Changes)
        # Służą jako "fallback" dla algorytmu ML
        self.phonetic_rules = {
            'ą': 'ǫ', 'ę': 'ę', 'rz': 'rь', 'sz': 'š', 'cz': 'č', 
            'ż': 'ž', 'ć': 'cь', 'ś': 'sь', 'ź': 'zь', 'y': 'y'
        }

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd ładowania {path}: {e}")
            return {}

    def get_inflection(self, root_info, form_type="m1"):
        """
        Pobiera odpowiednią końcówkę z vuzor.json na podstawie wzorca.
        """
        pattern_name = root_info.get("vuzor")  # np. "v1"
        if pattern_name in self.vuzor:
            # Szukamy konkretnej formy (np. mianownik, 1 os. l.p.)
            return self.vuzor[pattern_name].get(form_type, "")
        return ""

    def reconstruct_phonetically(self, word):
        """Algorytm heurystyczny dla słów spoza bazy"""
        word = word.lower()
        for pl, psl in self.phonetic_rules.items():
            word = word.replace(pl, psl)
        return word

    def translate_word(self, word):
        word_clean = word.lower().strip(",.!?:")
        
        # 1. Szukanie bezpośrednie w osnova
        if word_clean in self.osnova:
            entry = self.osnova[word_clean]
            if isinstance(entry, dict) and "osnova" in entry:
                # Jeśli mamy zdefiniowany rdzeń i wzorzec (vuzor)
                root = entry["osnova"]
                suffix = self.get_inflection(entry, "m1") # domyślnie mianownik
                return root + suffix
            return entry # Jeśli to prosty string
            
        # 2. Próba znalezienia rdzenia (jeśli słowo jest odmienione w PL)
        for pl_word, data in self.osnova.items():
            if word_clean.startswith(pl_word[:3]): # Bardzo uproszczony stemming
                 if isinstance(data, dict):
                     return data.get("osnova", word_clean)
        
        # 3. Fallback: Fonetyczna rekonstrukcja (Machine Learning Baseline)
        return self.reconstruct_phonetically(word_clean)

    def translate_text(self, text):
        words = text.split()
        return " ".join([self.translate_word(w) for w in words])

translator_logic = SlovianLogic()
