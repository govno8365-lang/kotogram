from .filters import Filters

class CommandHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = []
    
    def register(self, name: str):
        def decorator(func):
            self.handlers.append({"name": name, "func": func})
            return func
        return decorator
    
    async def process(self, message):
        text = message.get("text", "")
        if text.startswith("/"):
            cmd = text.split()[0][1:]
            for h in self.handlers:
                if h["name"] == cmd:
                    chat_id = message["chat"]["id"]
                    await h["func"](self.bot, chat_id, text)
                    self.bot._stats["commands"] += 1
                    return True
        return False

class MessageHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = []
    
    def register(self, filter_obj=None):
        def decorator(func):
            self.handlers.append({"filter": filter_obj or Filters.TEXT, "func": func})
            return func
        return decorator
    
    async def process(self, message):
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        for h in self.handlers:
            if await h["filter"](message):
                await h["func"](self.bot, chat_id, text)
                self.bot._stats["messages"] += 1
                return True
        return False

class CallbackHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = []
    
    def register(self, pattern: str = None):
        def decorator(func):
            self.handlers.append({"pattern": pattern, "func": func})
            return func
        return decorator
    
    async def process(self, callback):
        data = callback.get("data")
        callback_id = callback["id"]
        for h in self.handlers:
            if h["pattern"] is None or h["pattern"] == data:
                await h["func"](self.bot, callback_id, data)
                self.bot._stats["callbacks"] += 1
                return True
        return False

class PollHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = []
    
    def register(self):
        def decorator(func):
            self.handlers.append({"func": func})
            return func
        return decorator
    
    async def process(self, poll):
        for h in self.handlers:
            await h["func"](self.bot, poll)
        return True

class ChatMemberHandler:
    def __init__(self, bot):
        self.bot = bot
        self.handlers = []
    
    def register(self):
        def decorator(func):
            self.handlers.append({"func": func})
            return func
        return decorator
    
    async def process(self, chat_member):
        for h in self.handlers:
            await h["func"](self.bot, chat_member)
        return True
