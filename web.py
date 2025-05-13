from flask import Flask, render_template_string
from main import send_telegram_message

app = Flask(__name__)

# HTML without signal display
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Signal Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
            background: #f4f4f4;
        }
        h1 {
            color: #333;
        }
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
    <h1>Signal Dashboard</h1>

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
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_hello', methods=['GET'])
def send_hello():
    try:
        send_telegram_message("Hello from Signal Dashboard")
        return "Message sent to Telegram!"
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
