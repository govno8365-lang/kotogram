import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kotogram import Kotogram
from kotogram.ext.filters import Filters


class TestKotogram(unittest.TestCase):
    """Тесты для Kotogram PRO"""
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.bot = Kotogram("test_token")
    
    def test_init(self):
        """Тест инициализации бота"""
        self.assertEqual(self.bot.token, "test_token")
        self.assertTrue(self.bot._running)
        self.assertIsNotNone(self.bot.client)
    
    def test_base_url(self):
        """Тест правильного URL"""
        self.assertEqual(
            self.bot.base_url, 
            "https://api.telegram.org/bottest_token"
        )
    
    @patch.object(Kotogram, '_send', new_callable=AsyncMock)
    async def test_send_message(self, mock_send):
        """Тест отправки сообщения"""
        mock_send.return_value = {"ok": True}
        result = await self.bot.send_message(123456, "Hello")
        self.assertEqual(result, {"ok": True})
        mock_send.assert_called_once()
    
    @patch.object(Kotogram, '_send', new_callable=AsyncMock)
    async def test_answer_callback(self, mock_send):
        """Тест ответа на callback"""
        mock_send.return_value = {"ok": True}
        result = await self.bot.answer_callback("callback_id", "OK")
        self.assertEqual(result, {"ok": True})
    
    def test_kot_stats(self):
        """Тест статистики"""
        self.bot._stats["messages"] = 10
        self.bot._stats["commands"] = 5
        self.bot._stats["callbacks"] = 2
        self.bot._stats["errors"] = 0
        
        self.assertEqual(self.bot._stats["messages"], 10)
        self.assertEqual(self.bot._stats["commands"], 5)
    
    def test_kot_log(self):
        """Тест логирования"""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        async def run_test():
            await self.bot.kot_log(123456, "test message", tmp_path)
        
        import asyncio
        asyncio.run(run_test())
        
        with open(tmp_path, "r") as f:
            content = f.read()
            self.assertIn("123456: test message", content)
        
        os.unlink(tmp_path)
    
    def test_filters(self):
        """Тест фильтров"""
        import asyncio
        
        async def test_filter():
            # Текстовое сообщение
            text_msg = {"text": "hello", "chat": {"id": 1}}
            # Команда
            cmd_msg = {"text": "/start", "chat": {"id": 1}}
            # Фото
            photo_msg = {"photo": [{"file_id": "123"}], "chat": {"id": 1}}
            
            text_filter = Filters.TEXT
            cmd_filter = Filters.COMMAND
            photo_filter = Filters.PHOTO
            
            self.assertTrue(await text_filter(text_msg))
            self.assertFalse(await text_filter(cmd_msg))
            self.assertTrue(await cmd_filter(cmd_msg))
            self.assertTrue(await photo_filter(photo_msg))
        
        asyncio.run(test_filter())
    
    def test_rate_limiter(self):
        """Тест ограничителя частоты"""
        from kotogram.utils.ratelimiter import RateLimiter
        
        limiter = RateLimiter(rate=2, per=10)
        
        self.assertTrue(limiter.can_call(1))
        self.assertTrue(limiter.can_call(1))
        self.assertFalse(limiter.can_call(1))  # Третий раз уже нельзя


class TestHandlers(unittest.TestCase):
    """Тесты для хендлеров"""
    
    def setUp(self):
        self.bot = Kotogram("test_token")
    
    def test_command_handler_register(self):
        """Тест регистрации команды"""
        
        @self.bot.commands.register("test")
        async def test_cmd(bot, chat_id, text):
            pass
        
        self.assertEqual(len(self.bot.commands.handlers), 1)
        self.assertEqual(self.bot.commands.handlers[0]["name"], "test")
    
    def test_message_handler_register(self):
        """Тест регистрации обработчика сообщений"""
        
        @self.bot.messages.register(Filters.TEXT)
        async def test_msg(bot, chat_id, text):
            pass
        
        self.assertEqual(len(self.bot.messages.handlers), 1)


if __name__ == "__main__":
    unittest.main()
