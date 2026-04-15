import asyncio
import httpx
from .ext.filters import Filters
from .ext.jobqueue import JobQueue
from .ext.handlers import CommandHandler, MessageHandler, CallbackHandler, PollHandler, ChatMemberHandler
from .utils.ratelimiter import RateLimiter
from .utils.persistence import KotPersistence

class Kotogram:
    def __init__(self, token: str, persistence: bool = False):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.client = httpx.AsyncClient()
        self.job_queue = JobQueue()
        self.rate_limiter = RateLimiter()
        self.persistence = KotPersistence() if persistence else None
        self._running = True
        self._stats = {"messages": 0, "commands": 0, "callbacks": 0, "errors": 0}
        self._middlewares = []
        
        self.commands = CommandHandler(self)
        self.messages = MessageHandler(self)
        self.callbacks = CallbackHandler(self)
        self.polls = PollHandler(self)
        self.chat_members = ChatMemberHandler(self)
        self.update_queue = asyncio.Queue()
    
    def use(self, middleware):
        self._middlewares.append(middleware)
        return self
    
    async def _run_middlewares(self, update):
        for mw in self._middlewares:
            update = await mw(update, self)
            if update is None:
                return None
        return update
    
    async def _send(self, method: str, data: dict = None):
        url = f"{self.base_url}/{method}"
        response = await self.client.post(url, json=data)
        return response.json()
    
    async def send_message(self, chat_id: int, text: str, **kwargs):
        data = {"chat_id": chat_id, "text": text, **kwargs}
        return await self._send("sendMessage", data)
    
    async def answer_callback(self, callback_id: str, text: str = None):
        return await self._send("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})
    
    async def kot_get_user_data(self, user_id: int):
        if self.persistence:
            return self.persistence.get_user(user_id)
        return {}
    
    async def kot_set_user_data(self, user_id: int, data: dict):
        if self.persistence:
            self.persistence.set_user(user_id, data)
    
    async def kot_stats(self, chat_id: int):
        stats_text = f"📊 Kotogram Stats\n\n"
        stats_text += f"📨 Messages: {self._stats['messages']}\n"
        stats_text += f"⚡ Commands: {self._stats['commands']}\n"
        stats_text += f"🔘 Callbacks: {self._stats['callbacks']}\n"
        stats_text += f"❌ Errors: {self._stats['errors']}\n"
        stats_text += f"\n🐱 Kotogram is running"
        await self.send_message(chat_id, stats_text)
    
    async def kot_send_typing(self, chat_id: int, func, *args, **kwargs):
        await self._send("sendChatAction", {"chat_id": chat_id, "action": "typing"})
        return await func(*args, **kwargs)
    
    async def kot_safe_send(self, chat_id: int, text: str, retries: int = 3):
        for i in range(retries):
            try:
                return await self.send_message(chat_id, text)
            except Exception as e:
                if i == retries - 1:
                    raise e
                await asyncio.sleep(1)
        return None
    
    def kot_random_reply(self, replies: list):
        import random
        def decorator(func):
            async def wrapper(bot, chat_id, text, *args, **kwargs):
                reply = random.choice(replies)
                await bot.send_message(chat_id, reply)
                if func:
                    return await func(bot, chat_id, text, *args, **kwargs)
                return None
            return wrapper
        return decorator
    
    async def kot_log(self, chat_id: int, text: str, log_file: str = "kotogram.log"):
        import datetime, os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {chat_id}: {text}\n")
        return {"ok": True, "file": log_file}
    
    async def kot_repeat(self, chat_id: int, text: str, delay: int = 5, times: int = 1):
        async def _repeat():
            for i in range(times):
                if not self._running:
                    break
                await asyncio.sleep(delay)
                await self.send_message(chat_id, text)
        asyncio.create_task(_repeat())
        return {"ok": True, "delay": delay, "times": times}
    
    async def kot_webhook(self, host="0.0.0.0", port=8443, path="/webhook", secret_token=None):
        from aiohttp import web
        async def handle(request):
            if secret_token and request.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret_token:
                return web.Response(status=403)
            data = await request.json()
            asyncio.create_task(self._process_update(data))
            return web.Response(text="OK")
        app = web.Application()
        app.router.add_post(path, handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        await asyncio.Event().wait()
    
    async def _process_update(self, update: dict):
        update = await self._run_middlewares(update)
        if update is None:
            return
        message = update.get("message")
        callback = update.get("callback_query")
        poll = update.get("poll")
        chat_member = update.get("chat_member")
        if message:
            await self.messages.process(message)
        elif callback:
            await self.callbacks.process(callback)
        elif poll:
            await self.polls.process(poll)
        elif chat_member:
            await self.chat_members.process(chat_member)
    
    async def _fast_worker(self, worker_id: int):
        while self._running:
            try:
                update = await asyncio.wait_for(self.update_queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            asyncio.create_task(self._process_update(update))
            self.update_queue.task_done()
    
    async def _fast_polling(self):
        offset = 0
        self.job_queue.start()
        workers = [asyncio.create_task(self._fast_worker(i)) for i in range(5)]
        while self._running:
            try:
                res = await asyncio.wait_for(
                    self._send("getUpdates", {"offset": offset, "timeout": 5}),
                    timeout=6
                )
                if res.get("ok"):
                    for upd in res.get("result", []):
                        offset = upd["update_id"] + 1
                        await self.update_queue.put(upd)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self._stats["errors"] = self._stats.get("errors", 0) + 1
            await asyncio.sleep(0.01)
        for w in workers:
            w.cancel()
    
    async def run_fast(self):
        try:
            await self._fast_polling()
        except KeyboardInterrupt:
            self._running = False
    
    def run(self):
        try:
            asyncio.run(self._fast_polling())
        except KeyboardInterrupt:
            print("\nKotogram stopped")
