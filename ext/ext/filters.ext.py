class BaseFilter:
    async def __call__(self, message): return await self.filter(message)
    def __and__(self, other): return AndFilter(self, other)
    def __or__(self, other): return OrFilter(self, other)
    def __invert__(self): return InvertFilter(self)

class AndFilter(BaseFilter):
    def __init__(self, f1, f2): self.f1, self.f2 = f1, f2
    async def filter(self, m): return await self.f1(m) and await self.f2(m)

class OrFilter(BaseFilter):
    def __init__(self, f1, f2): self.f1, self.f2 = f1, f2
    async def filter(self, m): return await self.f1(m) or await self.f2(m)

class InvertFilter(BaseFilter):
    def __init__(self, f): self.f = f
    async def filter(self, m): return not await self.f(m)

class TextFilter(BaseFilter):
    async def filter(self, m): return bool(m and m.get("text") and not m["text"].startswith('/'))

class CommandFilter(BaseFilter):
    async def filter(self, m): return bool(m and m.get("text") and m["text"].startswith('/'))

class PhotoFilter(BaseFilter):
    async def filter(self, m): return bool(m and m.get("photo"))

class VideoFilter(BaseFilter):
    async def filter(self, m): return bool(m and m.get("video"))

class PollFilter(BaseFilter):
    async def filter(self, m): return bool(m and m.get("poll"))

class Filters:
    TEXT = TextFilter()
    COMMAND = CommandFilter()
    PHOTO = PhotoFilter()
    VIDEO = VideoFilter()
    POLL = PollFilter()
