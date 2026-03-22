def translate_word(self, word):
    original = word
    clean_lower = word.lower().strip(".,!?;:()")

    # Wyjątki / stałe tłumaczenia
    exceptions = {
        "jest": "estь",
        "w": "vu",
        "jestem": "esmь",
        "jestes": "esi",
        "są": "sǫtь",
        "matka": "mati",
        "matki": "matere",   # lub matь – zależnie od przypadku
        "ogrodzie": "obgordě",
        "ogrod": "obgordъ",
    }

    if clean_lower in exceptions:
        translated = exceptions[clean_lower]
    else:
        # zwykłe wyszukiwanie w osnova
        for entry in self.osnova:
            if entry.get("polish", "").lower() == clean_lower:
                translated = entry.get("slovian", clean_lower)
                break
        else:
            # fonetyczna rekonstrukcja jako ostatnia deska
            translated = clean_lower
            for pl, sl in self.rules.items():
                translated = translated.replace(pl, sl)
            if translated and translated[-1] not in "aeiouyęǫьъ":
                translated += "ъ"

    # Przywróć wielkość pierwszej litery jeśli była duża
    if original and original[0].isupper():
        translated = translated[0].upper() + translated[1:]

    return translated


def translate_sentence(self, text):
    if not text.strip():
        return ""

    # Rozbijamy zachowując znaki interpunkcyjne
    tokens = re.findall(r'\w+|[^\w\s]', text)
    result = []

    for token in tokens:
        if token.isspace() or re.match(r'^[^\w\s]+$', token):
            result.append(token)
        else:
            result.append(self.translate_word(token))

    return "".join(result).strip()
