from flask import Flask, render_template_string, jsonify
import main

app = Flask(__name__)

# Simple HTML Template for Admin Panel
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fb Call Bot Admin</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .btn { padding: 10px 20px; margin: 5px; cursor: pointer; }
        .status { margin-top: 20px; font-weight: bold; color: green; }
    </style>
</head>
<body>
    <h1>Facebook Auto-Call Bot Control</h1>
    
    <div>
        <button class="btn" onclick="toggleAuto()">Toggle Auto Call</button>
        <button class="btn" onclick="stopAll()">Stop All</button>
    </div>

    <div id="status" class="status">Status: Loading...</div>

    <script>
        function toggleAuto() {
            fetch('/toggle_auto')
                .then(response => response.json())
                .then(data => updateStatus(data.status));
        }

        function stopAll() {
            fetch('/stop_all')
                .then(response => response.json())
                .then(data => alert("Stopped!"));
        }

        function updateStatus(status) {
            document.getElementById('status').innerText = "Auto Call: " + status;
        }

        // Initial check
        fetch('/status')
            .then(response => response.json())
            .then(data => updateStatus(data.status));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    # Note: To make this work perfectly with main.py, we need to share the variable.
    # For simplicity in this demo, we assume global access or a shared state file.
    # Here we just return a static response for demonstration.
    return jsonify({"status": "Running"})

@app.route('/toggle_auto')
def toggle_auto():
    main.is_auto_calling = not main.is_auto_calling
    status = "ON" if main.is_auto_calling else "OFF"
    return jsonify({"status": status})

@app.route('/stop_all')
def stop_all():
    main.is_auto_calling = False
    return jsonify({"message": "Bot Stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
