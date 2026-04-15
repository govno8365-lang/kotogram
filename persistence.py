import json
import os

class KotPersistence:
    def __init__(self, filepath="kotogram_data.json"):
        self.filepath = filepath
        self.user_data = {}
        self.chat_data = {}
        self._load()
    
    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                data = json.load(f)
                self.user_data = data.get("user_data", {})
                self.chat_data = data.get("chat_data", {})
    
    def save(self):
        with open(self.filepath, "w") as f:
            json.dump({"user_data": self.user_data, "chat_data": self.chat_data}, f)
    
    def get_user(self, user_id):
        return self.user_data.get(str(user_id), {})
    
    def set_user(self, user_id, data):
        self.user_data[str(user_id)] = data
        self.save()
    
    def get_chat(self, chat_id):
        return self.chat_data.get(str(chat_id), {})
    
    def set_chat(self, chat_id, data):
        self.chat_data[str(chat_id)] = data
        self.save()
