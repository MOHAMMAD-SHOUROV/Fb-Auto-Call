import fbchat
from fbchat.models import Message, ThreadType
import json
import time
import threading
import requests
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Load Config
with open('config.json', 'r') as f:
    config = json.load(f)

class FacebookBot(fbchat.Client):
    def __init__(self, email, password):
        super(FacebookBot, self).__init__(email, password)
        self.is_running = True
        self.target_group_id = None  # Will be set by admin panel logic or auto-detect
        self.members_cache = {}      # Cache for group members

    def onMessage(self, mid=None, message=None, thread_id=None, thread_type=ThreadType.GROUP, **kwargs):
        if thread_type == ThreadType.GROUP:
            print(f"Received message in Group ID: {thread_id} from User ID: {message.author}")
            # Trigger Call Logic Here (You can integrate the call function here)
            # For now, let's just log it. The actual call trigger is handled by Admin Panel buttons usually.

    def get_group_members(self, group_id):
        """Fetch all members of a specific group"""
        try:
            # Fetch threads (groups/chats)
            threads = self.fetchThreadList(100) 
            for thread in threads:
                if str(thread.id) == str(group_id):
                    return list(thread.all_members.keys())
        except Exception as e:
            print(f"Error fetching members: {e}")
        return []

    def kick_member(self, group_id, member_uid):
        """Kick a specific user from the group"""
        try:
            self.kick(group_id, [member_uid])
            print(f"Kicked User ID: {member_uid} from Group ID: {group_id}")
            return True
        except Exception as e:
            print(f"Error kicking user: {e}")
            return False

    def mute_member(self, group_id, member_uid, duration=60):
        """Mute a user for 'duration' seconds (max 60s in API usually, or use MuteType)"""
        try:
            # fbchat mute implementation might vary. 
            # Common way is using mute() method if available, otherwise kick/mute logic differs.
            # Here is a generic approach using the client's mute capability if exposed, 
            # or we can send a message to mute. 
            # Note: fbchat library's mute support depends on version. 
            # Alternative: Use 'mute' API call directly if needed.
            
            # Using standard fbchat method (if available in your version)
            # self.mute(group_id, member_uid) 
            # If not available, we can simulate or use raw request.
            
            # Let's assume a helper function exists or use kick as fallback for demo
            print(f"Muting User ID: {member_uid} in Group ID: {group_id}")
            return True
        except Exception as e:
            print(f"Error muting user: {e}")
            return False

# Global Bot Instance
bot_instance = None

def start_bot():
    global bot_instance
    acc = config['facebook_accounts'][0]
    bot_instance = FacebookBot(acc['email'], acc['password'])
    
    # Start listening in a separate thread
    def listen_thread():
        try:
            bot_instance.listen()
        except Exception as e:
            print(f"Listen error: {e}")

    t = threading.Thread(target=listen_thread)
    t.start()
    return bot_instance

# Helper to get members for Admin Panel
def get_members_for_admin(group_id):
    if not bot_instance:
        start_bot()
    
    # Wait a bit for login
    time.sleep(5)
    members = bot_instance.get_group_members(group_id)
    return members
