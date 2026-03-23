import json
import os
import re

class SlovianLogic:
    def __init__(self):
        self.osnova = self._load_data('osnova.json')         # klucz: polskie słowo → prasłowiańska forma / vuzor
        self.vuzor  = self._load_data('vuzor.json')

    def _load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_praslowianska_forma(self, polskie_slowo):
        """Zwraca prasłowiańską formę dla danego polskiego słowa (lub None)"""
        clean = polskie_slowo.lower().strip(".,!?:;()[]{}")
        if not clean:
            return None

        entry = self.osnova.get(clean)
        if entry:
            if isinstance(entry, str):
                return entry
            if isinstance(entry, dict) and "osnova" in entry and "vuzor" in entry:
                root = entry["osnova"]
                vid  = entry["vuzor"]
                forma = self.vuzor.get(vid, {}).get("m1", "")   # domyślnie m1 – możesz później dodać rozpoznawanie rodzaju/liczby
                return root + forma

        # bardzo prosty fallback – tylko fonetyczna rekonstrukcja
        return self._fonetyczna_rekonstrukcja(clean)

    def _fonetyczna_rekonstrukcja(self, word):
        res = word
        rules = [
            (r'ą',  'ǫ'),   (r'ę',  'ę'),
            (r'rz', 'rь'),  (r'sz', 'š'),  (r'cz', 'č'),
            (r'ż',  'ž'),   (r'ć',  'cь'), (r'ś',  'sь'),
            (r'ź',  'zь'),  (r'dz', 'dz'),
            (r'ió', 'je'),  (r'ia', 'ě'),  (r'ie', 'ě'),
        ]
        for pat, rep in rules:
            res = re.sub(pat, rep, res, flags=re.IGNORECASE)

        # dodaj ъ po spółgłosce na końcu (bardzo uproszczone)
        if res and res[-1] not in 'aeiouyęǫěьъ':
            res += 'ъ'

        return res

    def translate_word(self, word, source_lang="pl"):
        """Tłumaczenie jednego słowa – zawsze przez polski"""
        if source_lang != "pl":
            # Tutaj w przyszłości: wywołanie prawdziwego tłumacza pl ←→ inny język
            # Na razie udajemy, że już mamy polskie słowo
            polskie = word   # ← zastąp prawdziwym tłumaczeniem
        else:
            polskie = word

        prasl = self.get_praslowianska_forma(polskie)
        return prasl if prasl else word

    def process_text(self, text, source_lang="pl"):
        """Przetwarza cały tekst"""
        # Zachowujemy interpunkcję i spacje
        tokens = re.findall(r"\w+|[^\w\s]", text)
        result = []

        for token in tokens:
            if token.isalnum() or (len(token) > 1 and token.isalpha()):
                translated = self.translate_word(token, source_lang)
                result.append(translated)
            else:
                result.append(token)

        # Łączenie z poprawnymi spacjami
        out = []
        for i, t in enumerate(result):
            if i > 0 and not re.match(r"[.,!?;:'»»””]", t) and not re.match(r"^[.,!?;:'««““]", result[i-1]):
                out.append(" ")
            out.append(t)

        return "".join(out).strip()


# Użycie
translator = SlovianLogic()
