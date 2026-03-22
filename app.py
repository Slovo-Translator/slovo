from flask import Flask, render_template_string, request
from logic import translator

app = Flask(__name__)

# Szablon HTML w jednej zmiennej dla łatwego kopiowania
UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Slovian Translator AI</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px; }
        .box { width: 600px; background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
        textarea { width: 100%; height: 100px; background: #0d1117; color: #58a6ff; border: 1px solid #30363d; border-radius: 5px; padding: 10px; box-sizing: border-box; }
        .btn { background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 10px; width: 100%; font-weight: bold; }
        .result { margin-top: 20px; padding: 15px; background: #0d1117; border-left: 4px solid #238636; font-size: 1.2em; color: #d2a8ff; }
        h2 { color: #58a6ff; text-align: center; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Slovian-NSS Translator</h2>
        <form method="POST">
            <textarea name="text" placeholder="Wpisz tekst po polsku..."></textarea>
            <button type="submit" class="btn">TŁUMACZ / REKONSTRUUJ</button>
        </form>
        {% if result %}
        <div class="result">
            <strong>Prasłowiański:</strong><br> {{ result }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        user_input = request.form.get('text', '')
        result = translator.full_translate(user_input)
    return render_template_string(UI_TEMPLATE, result=result)

if __name__ == '__main__':
    app.run(debug=True)
