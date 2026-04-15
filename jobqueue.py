from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class JobQueue:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def run_repeating(self, callback, interval: int, chat_id: int = None):
        self.scheduler.add_job(callback, 'interval', seconds=interval, args=[chat_id])
    
    def run_once(self, callback, delay: int, chat_id: int = None):
        self.scheduler.add_job(callback, 'date', run_date=datetime.now(), args=[chat_id])
    
    def run_daily(self, callback, hour: int, minute: int, chat_id: int = None):
        self.scheduler.add_job(callback, 'cron', hour=hour, minute=minute, args=[chat_id])
    
    def start(self):
        self.scheduler.start()
