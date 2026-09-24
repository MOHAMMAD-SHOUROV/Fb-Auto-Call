# -------------------- app.py --------------------
import json, time, threading, os, logging
from flask import (
    Flask, render_template_string, request, redirect, url_for
)
# fbchat‑এর নতুন সংস্করণে কেবল Client আছে, Log নেই
from fbchat import Client

# -------------- কনফিগ ও লগিং --------------------
CONFIG_FILE = 'config.json'
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --------------------- বট ক্লাস --------------------
class SmartBot(Client):
    def __init__(self, cfg):
        self.cfg = cfg
        first_acc = cfg['accounts'][0]
        # প্রথম অ্যাকাউন্ট দিয়ে লগইন
        super().__init__(first_acc['email'], first_acc['password'])
        self.admin_uid = cfg['admin_uid']
        self.settings = cfg['settings']

    # ১. মেসেজ হ্যান্ডেল (Admin‑এর মেসেজ)
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        # কেবল Admin‑এর ID‑এ সাড়া দেবে
        if str(author_id) == str(self.admin_uid):
            text = message_object.text.lower()
            if text == "mute_all":
                self.cfg['settings']['mute_all'] = True
                save_config(self.cfg)
                # Admin‑কে ফিডব্যাক
                self.send(message_object, thread_id, thread_type=thread_type)
            elif text == "unmute_all":
                self.cfg['settings']['mute_all'] = False
                save_config(self.cfg)
                self.send(message_object, thread_id, thread_type=thread_type)

    # ২. কল পিক করা
    def onCall(self, call_id, author_id, thread_id, is_video, **kwargs):
        if self.settings.get('auto_pick_call'):
            logging.info("Incoming call – picking up.")
            time.sleep(1)  # সামান্য বিলম্ব
            self.answer(call_id, is_video=is_video)

    # ৩. বট চালু
    def run_bot(self):
        try:
            self.cfg['bot_status']['is_logged_in'] = True
            self.cfg['bot_status']['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_config(self.cfg)

            logging.info("Bot started – listening for calls/messages.")
            self.listen()
        except Exception as e:
            logging.error(f"Bot crashed: {e}")

# --------------------- হেল্পার ফাংশন ----------------
def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

# -------------------- HTML টেমপ্লেট ----------------
HTML_TPL = """
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<title>Fb Bot Admin Panel</title>
<style>
    body{font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0;}
    .container{max-width:700px;margin:2rem auto;background:#fff;padding:2rem;border-radius:8px;box-shadow:0 0 10px rgba(0,0,0,.1);}
    h2{color:#333;}
    .status{margin:1rem 0;padding:1rem;background:#e8f5e9;border-radius:4px;}
    .btn{padding:.5rem 1rem;margin: .3rem;border:none;border-radius:4px;color:#fff;background:#007bff;cursor:pointer;}
    .btn-danger{background:#dc3545;}
    input{padding:.5rem;width:90%;margin-top:.5rem;}
</style>
</head>
<body>
<div class="container">
    <h2>Facebook Group Call Bot Admin Panel</h2>
    {% if error %}<p style="color:red;">{{error}}</p>{% endif %}

    <div class="status">
        <h3>Bot Status</h3>
        <p><strong>Last Updated:</strong> {{ cfg.bot_status.last_updated }}</p>
        <p><strong>Login Status:</strong>
            {% if cfg.bot_status.is_logged_in %}
                <span style="color:green;">✅ Logged In & Running</span>
            {% else %}
                <span style="color:red;">❌ Offline</span>
            {% endif %}
        </p>
    </div>

    <h3>Admin UID:</h3>
    <p>{{ cfg.admin_uid }}</p>

    <h3>Controls</h3>
    <a href="{{ url_for('toggle_mute') }}" class="btn btn-danger">Toggle Mute All</a>
    <a href="{{ url_for('unmute_all') }}" class="btn">Unmute All</a>

    <hr>
    <form method="post" action="{{ url_for('login') }}">
        <label>Admin Password:</label><br>
        <input type="password" name="password" required><br>
        <button type="submit" class="btn">Login</button>
    </form>
</div>
</body>
</html>
"""

# --------------------- Flask Routes ------------------
@app.route('/', methods=['GET'])
def index():
    cfg = load_config()
    return render_template_string(HTML_TPL, cfg=cfg, error=None)

@app.route('/toggle_mute')
def toggle_mute():
    cfg = load_config()
    cfg['settings']['mute_all'] = not cfg['settings'].get('mute_all', False)
    save_config(cfg)
    return redirect(url_for('index'))

@app.route('/unmute_all')
def unmute_all():
    cfg = load_config()
    cfg['settings']['mute_all'] = False
    save_config(cfg)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    pwd = request.form.get('password')
    cfg = load_config()
    if pwd == cfg.get('admin_password'):
        return render_template_string(HTML_TPL, cfg=cfg, error=None)
    else:
        return render_template_string(HTML_TPL, cfg=cfg, error="অবৈধ পাসওয়ার্ড")

# --------------------- মেইন -----------------------
if __name__ == '__main__':
    # ১. বট থ্রেড চালু
    cfg = load_config()
    bot = SmartBot(cfg)
    threading.Thread(target=bot.run_bot, daemon=True).start()

    # ২. Flask চালু
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
