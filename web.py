from flask import Flask, render_template_string
from main import get_signals

from flask import jsonify


app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Signal Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; background: #f4f4f4; }
        h1 { color: #333; }
        ul { list-style: none; padding: 0; }
        li { background: #fff; margin: 10px 0; padding: 10px; border-left: 5px solid #6a1b9a; }
    </style>
</head>
<body>
    <h1>Live Signals</h1>
    <ul>
        {% for signal in signals %}
            <li>{{ signal }}</li>
        {% endfor %}
    </ul>
</body>
</html>
"""

@app.route('/')
def home():
    signals = get_signals()
    return render_template_string(HTML_TEMPLATE, signals=signals)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
