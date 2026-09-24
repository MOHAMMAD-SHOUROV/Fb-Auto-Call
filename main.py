import fbchat
from fbchat.models import Message
import json
import time
import threading
from twilio.rest import Client
import pyttsx3
import requests
import os

# Load Config
with open('config.json', 'r') as f:
    config = json.load(f)

# Global Variables
is_auto_calling = True
client_instances = []
last_message_time = 0

# Initialize Twilio Client
twilio_client = Client(config['twilio_sid'], config['twilio_auth'])

# Initialize Text-to-Speech
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) # Default voice

def speak(text):
    """Convert text to speech"""
    print(f"Bot says: {text}")
    engine.say(text)
    engine.runAndWait()

def call_your_phone():
    """Function to make a call via Twilio"""
    global is_auto_calling
    
    while is_auto_calling:
        try:
            # Make the call
            call = twilio_client.calls.create(
                url=f'http://your-server-ip/dial', # Webhook URL for Twilio (defined in admin_panel.py logic)
                to=config['your_phone_number'],
                from_=config['twilio_from_number']
            )
            
            print(f"Call initiated: {call.sid}")
            
            # Wait for call to be answered/ended logic could be more complex here
            # For simplicity, we loop until stopped. 
            # In a real scenario, you'd listen to Twilio Webhooks to know when call ends.
            time.sleep(10) # Wait 10 seconds before retrying if not manually stopped
            
        except Exception as e:
            print(f"Call error: {e}")
            break

class MyBot(fbchat.Client):
    def onMessage(self, mid=None, message=None, thread_id=None, thread_type=fbchat.ThreadType.GROUP, **kwargs):
        global last_message_time
        
        # Check if it's the target group
        if str(thread_id) == config['target_group_id']:
            current_time = time.time()
            # Prevent spamming calls for same message rapidly (debounce)
            if current_time - last_message_time > 30: 
                print(f"New Message in Group: {message.text}")
                speak("Sir, new message from target group.")
                
                # Start calling thread if not already running (simple check)
                # In production, use a queue or better state management
                threading.Thread(target=call_your_phone).start()
                
                last_message_time = current_time

def start_bot():
    print("Starting Facebook Bot...")
    accounts = config['facebook_accounts']
    
    for i, acc in enumerate(accounts):
        try:
            # Login using email and password
            uid = MyBot.login(
                account_id=acc['email'],
                password=acc['password']
            )
            print(f"Logged in as Account {i+1}: {uid}")
            
            # Create a client instance for this account
            client = MyBot()
            client_instances.append(client)
            
            # Start listening in a separate thread
            def listen():
                try:
                    client.listen()
                except Exception as e:
                    print(f"Listen error for acc {i}: {e}")
            
            threading.Thread(target=listen).start()
            
        except Exception as e:
            print(f"Login failed for account {i+1}: {e}")

if __name__ == '__main__':
    # Start the bot
    start_bot()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Bot...")
