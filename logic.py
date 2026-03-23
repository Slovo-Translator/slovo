import json
import os
import re

class SlovianLogic:
    def __init__(self):
        self.osnova = self._load_data('osnova.json')
        self.vuzor  = self._load_data('vuzor.json')

    def _load_data(self, filename):
        path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def translate(self, text):
        if not text.strip():
            return text

        tokens = re.findall(r'\w+|[^\w\s]', text)
        result = []

        for token in tokens:
            if token.isalnum():
                result.append(self._translate_word(token.lower()))
            else:
                result.append(token)

        return ''.join(result).strip()

    def _translate_word(self, word):
        entry = self.osnova.get(word)
        if entry:
            if isinstance(entry, str):
                return entry
            if isinstance(entry, dict) and 'osnova' in entry and 'vuzor' in entry:
                root = entry['osnova']
                vid = entry['vuzor']
                suffix = self.vuzor.get(vid, {}).get('m1', '')
                return root + suffix

        # bardzo prosta fonetyczna fallback
        res = word
        for pat, rep in [
            (r'ą', 'ǫ'), (r'ę', 'ę'), (r'rz', 'rь'), (r'sz', 'š'),
            (r'cz', 'č'), (r'ż', 'ž'), (r'ć', 'cь'), (r'ś', 'sь'),
        ]:
            res = re.sub(pat, rep, res)
        if res[-1] not in 'aeiouyęǫěьъ':
            res += 'ъ'
        return res
