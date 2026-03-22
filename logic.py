import json
import os

class SlovianLogic:
    def __init__(self, osnova_path='osnova.json', vuzor_path='vuzor.json'):
        self.osnova = self._load_json(osnova_path)
        self.vuzor = self._load_json(vuzor_path)
        
        # Mapa fonetyczna dla słów spoza bazy (symulacja reguł językowych)
        self.rules = {
            'ą': 'ǫ', 'ę': 'ę', 'rz': 'rь', 'sz': 'š', 
            'cz': 'č', 'ż': 'ž', 'ć': 'cь', 'ś': 'sь'
        }

    def _load_json(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_suffix(self, vuzor_id, form="m1"):
        """Pobiera końcówkę (np. mianownik m1) z vuzor.json"""
        pattern = self.vuzor.get(vuzor_id, {})
        return pattern.get(form, "")

    def translate_word(self, word):
        # Czyszczenie słowa z interpunkcji
        clean_word = word.lower().strip(".,!?:;()")
        
        # 1. Sprawdzenie w osnova.json
        if clean_word in self.osnova:
            entry = self.osnova[clean_word]
            if isinstance(entry, dict):
                root = entry.get("osnova", "")
                v_id = entry.get("vuzor", "")
                suffix = self.get_suffix(v_id)
                return root + suffix
            return entry # Jeśli to zwykły string

        # 2. Jeśli nie ma w bazie - rekonstrukcja fonetyczna (Machine Learning Baseline)
        reconstructed = clean_word
        for pl, psl in self.rules.items():
            reconstructed = reconstructed.replace(pl, psl)
            
        # Dodanie twardego znaku na końcu, jeśli kończy się spółgłoską
        if reconstructed[-1] not in "aeiouyǫęьъ":
            reconstructed += "ъ"
            
        return reconstructed

    def translate_sentence(self, text):
        if not text: return ""
        words = text.split()
        return " ".join([self.translate_word(w) for w in words])

# Inicjalizacja do użycia w app.py
translator = SlovianLogic()
