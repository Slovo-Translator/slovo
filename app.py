from flask import Flask, render_template, request, jsonify
from logic import translator_logic

app = Flask(__name__)

# Mockup prostego szablonu HTML wewnątrz kodu dla kompletności pliku
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Slovian Translator Pro</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 50px; }
        .container { max-width: 800px; margin: auto; background: #2d2d2d; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        textarea { width: 100%; height: 150px; border-radius: 10px; border: none; padding: 15px; font-size: 16px; margin-bottom: 20px; }
        .result { background: #3d3d3d; padding: 20px; border-radius: 10px; min-height: 50px; font-size: 24px; color: #00d4ff; border-left: 5px solid #00d4ff; }
        button { background: #00d4ff; color: black; border: none; padding: 10px 30px; border-radius: 5px; font-weight: bold; cursor: pointer; }
        button:hover { background: #0099cc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Slovian Translator v2.0</h1>
        <form method="POST">
            <textarea name="user_text" placeholder="Wpisz tekst po polsku...">{original}</textarea>
            <br>
            <button type="submit">Rekonstruuj na Prasłowiański</button>
        </form>
        <div class="result">
            <strong>Wynik:</strong><br>
            {result}
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    original = ""
    if request.method == 'POST':
        original = request.form.get('user_text', '')
        result = translator_logic.translate_text(original)
    
    return HTML_TEMPLATE.format(original=original, result=result)

if __name__ == '__main__':
    # Uruchomienie serwera
    app.run(debug=True, port=5000)
