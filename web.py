from flask import Flask, render_template_string, request
from main import send_telegram_message, get_signals

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
        button {
            padding: 10px 20px;
            background-color: #6a1b9a;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #9c4d9d;
        }
    </style>
</head>
<body>
    <h1>Live Signals</h1>
    <ul>
        {% for signal in signals %}
            <li>{{ signal }}</li>
        {% endfor %}
    </ul>
    
    <button onclick="sendHello()">Send Hello to Telegram</button>

    <script>
        function sendHello() {
            fetch('/send_hello', {
                method: 'GET',
            })
            .then(response => response.text())
            .then(data => alert(data))
            .catch(error => alert('Error sending message: ' + error));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    try:
        signals = get_signals()  # Fetch live signals
        return render_template_string(HTML_TEMPLATE, signals=signals)
    except Exception as e:
        return f"Error fetching signals: {str(e)}", 500

@app.route('/send_hello', methods=['GET'])
def send_hello():
    try:
        send_telegram_message("Hello")  # Sends a "Hello" message to Telegram
        return "Message sent to Telegram!"
    except Exception as e:
        return f"Error: {str(e)}", 500  # Return error message if something goes wrong

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

