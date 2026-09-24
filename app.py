from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import json
import time
import threading
import os
import logging
from fbchat import Client, Log

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
ADMIN_PASSWORD = "247898@"
CONFIG_FILE = 'config.json'

# --- বট ক্লাস ---
class SmartBot(Client):
    def __init__(self, config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        first_account = self.config['accounts'][0]
        super().__init__(first_account['email'], first_account['password'])
        
        self.admin_uid = self.config['admin_uid']
        self.settings = self.config['settings']

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        # এডমিন কমান্ড হ্যান্ডেল করা (যদি সরাসরি মেসেজ পাঠায়)
        if str(author_id) == str(self.admin_uid):
            text = message_object.text.lower()
            if text == "mute_all":
                self.config['settings']['mute_all'] = True
                save_config(self.config)
                self.send(message_object, text="সবাই মুট করা হয়েছে!")
            elif text == "unmute_all":
                self.config['settings']['mute_all'] = False
                save_config(self.config)
                self.send(message_object, text="সবাই আনমুট করা হয়েছে!")

    def onCall(self, call_id, author_id, thread_id, is_video, **kwargs):
        if self.settings.get('auto_pick_call'):
            logging.info("Incoming Call. Picking up...")
            time.sleep(1)
            self.answer(call_id, is_video=is_video)

    def run_bot(self):
        try:
            # লগইন স্ট্যাটাস আপডেট
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['bot_status']['is_logged_in'] = True
            config['bot_status']['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            logging.info("Bot Started Listening...")
            self.listen() # বট চালু করা
        except Exception as e:
            logging.error(f"Bot Error: {e}")

# --- হেল্পার ফাংশন ---
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- HTML টেমপ্লেট (এডমিন প্যানেল UI) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <title>Fb Bot Admin Panel</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; padding: 50px; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
        h2 { color: #333; }
        .status-box { background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .btn { padding: 10px 20px; margin: 5px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px; text-decoration: none; display: inline-block; }
        .btn-danger { background: #dc3545; }
        input { padding: 10px; width: 80%; margin-top: 10px; }
    </style>
</head>
<body>

<div class="container">
    <h2>Facebook Group Call Bot Admin Panel</h2>
    
    <!-- লগইন স্ট্যাটাস -->
    <div class="status-box">
        <h3>Bot Status</h3>
        <p><strong>Last Updated:</strong> {{ config.bot_status.last_updated }}</p>
        <p><strong>Login Status:</strong> 
            {% if config.bot_status.is_logged_in %}
                <span style="color: green; font-weight: bold;">✅ Logged In & Running</span>
            {% else %}
                <span style="color: red; font-weight: bold;">❌ Not Logged In / Offline</span>
            {% endif %}
        </p>
    </div>

    <!-- কন্ট্রোল বাটন -->
    <h3>Controls</h3>
    <a href="/toggle_mute" class="btn btn-danger">Mute All Users</a>
    <a href="/unmute_all" class="btn">Unmute All Users</a>
    <br><br>
    
    <!-- কনফিগ দেখানো -->
    <h3>Current Config (Admin UID)</h3>
    <p>{{ config.admin_uid }}</p>

    <hr>
    <p><a href="/">Home</a></p>
</div>

</body>
</html>
"""

# --- রুটস (Routes) ---

@app.route('/')
def index():
    config = load_config()
    return render_template_string(HTML_TEMPLATE, config=config)

@app.route('/toggle_mute')
def toggle_mute():
    config = load_config()
    # মুট লজিক: সবাইকে মুট করতে চাইলে একটি ফ্ল্যাগ সেট করা হচ্ছে। 
    # রিয়েল বাসে এখানে API কল করে গ্রুপের মেম্বারদের ID বের করে মুট করতে হয়।
    config['settings']['mute_all'] = not config['settings'].get('mute_all', False)
    save_config(config)
    return redirect(url_for('index'))

@app.route('/unmute_all')
def unmute_all():
    config = load_config()
    config['settings']['mute_all'] = False
    save_config(config)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        return redirect(url_for('index'))
    else:
        config = load_config()
        return render_template_string(HTML_TEMPLATE, config=config, error="Invalid Password")

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

# --- মেইন এক্সিকিউশন ---
if __name__ == '__main__':
    # ১. বট থ্রেড চালু করা (ব্যাকগ্রাউন্ডে)
    bot_thread = threading.Thread(target=SmartBot(CONFIG_FILE).run_bot, daemon=True)
    bot_thread.start()
    
    # ২. Flask অ্যাপ চালু করা (এডমিন প্যানেলের জন্য)
    # Render/Vercel এর জন্য PORT পরিবর্তনযোগ্য করতে হবে
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
