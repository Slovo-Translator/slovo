from flask import Flask, render_template, request
from logic import SlovianLogic

app = Flask(__name__)
translator = SlovianLogic()

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    original = ""
    if request.method == 'POST':
        original = request.form.get('content', '').strip()
        if original:
            result = translator.translate(original)
    return render_template('index.html', original=original, result=result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
