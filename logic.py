import json
import os
import re

class SlovianLogic:
    def __init__(self):
        self.osnova = self._load_data('osnova.json')
        self.vuzor = self._load_data('vuzor.json')
        
        # Zaawansowane reguły fonetyczne (rekonstrukcja prę-słowiańska)
        self.phonetic_rules = [
            (r'ą', 'ǫ'), (r'ę', 'ę'), (r'rz', 'rь'), (r'sz', 'š'),
            (r'cz', 'č'), (r'ż', 'ž'), (r'ć', 'cь'), (r'ś', 'sь'),
            (r'ź', 'zь'), (r'dz', 'dz'), (r'io', 'je'), (r'ia', 'ě')
        ]

    def _load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def apply_vuzor(self, entry, form="m1"):
        """Łączy rdzeń z odpowiednią końcówką z vuzor.json"""
        root = entry.get("osnova", "")
        v_id = entry.get("vuzor", "")
        
        # Pobieranie końcówki z vuzor.json
        suffix = self.vuzor.get(v_id, {}).get(form, "")
        return root + suffix

    def reconstruct(self, word):
        """Algorytmiczne 'zgadywanie' formy dla słów spoza bazy"""
        res = word.lower()
        for pattern, repl in self.phonetic_rules:
            res = re.sub(pattern, repl, res)
        
        # Reguła końcowego jera (ъ) dla rzeczowników twardych
        if res[-1] not in "aeiouyǫęьъě":
            res += "ъ"
        return res

    def translate_word(self, word):
        clean = word.lower().strip(".,!?:;()")
        if not clean: return word

        # 1. Sprawdzenie bezpośrednie
        if clean in self.osnova:
            entry = self.osnova[clean]
            if isinstance(entry, dict) and "osnova" in entry:
                return self.apply_vuzor(entry)
            return entry

        # 2. Próba znalezienia rdzenia po początku słowa (prosty stemming)
        for pl_key, data in self.osnova.items():
            if clean.startswith(pl_key[:4]) and isinstance(data, dict):
                return self.apply_vuzor(data)

        # 3. Fallback: Rekonstrukcja fonetyczna
        return self.reconstruct(clean)

    def process_text(self, text):
        # Rozbijanie na słowa z zachowaniem znaków interpunkcyjnych
        tokens = re.findall(r"[\w]+|[^\s\w]", text)
        result = []
        for t in tokens:
            if t.isalnum():
                result.append(self.translate_word(t))
            else:
                result.append(t)
        return "".join([" " + x if not re.match(r"[.,!?:;]", x) else x for x in result]).strip()

translator = SlovianLogic()
