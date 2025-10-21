import asyncio
import os

import redis
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from . import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentao.settings')

django_application = get_asgi_application()

from redis import asyncio as aioredis
from channels.layers import get_channel_layer
from django.conf import settings
import json


class RedisListenerManager:
    _task = None
    _started = False

    async def create_task_once(self):
        if not self._started:  # 只启用一个协程监听队列
            self._started = True
            self._task = asyncio.create_task(self._redis_listener())

    async def _redis_listener(self):
        """Redis消息监听器"""
        while True:
            try:
                async with aioredis.from_url(settings.CACHES['offline_msgs']['LOCATION']) as cache:
                    pubsub = cache.pubsub()
                    await pubsub.psubscribe('websocket_events')
                    channel_layer = get_channel_layer()
                    print("Redis listener connected and listening...")
                    async for msg in pubsub.listen():
                        if msg['type'] == 'pmessage':
                            print(f'Received Redis message: {msg}')
                            asyncio.create_task(self.send_msg(msg, channel_layer, cache))
            except Exception as e:
                print(f"Redis listener error: {e}, reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def send_msg(self, msg, channel_layer, cache):
        try:
            msg_channel = msg.get('channel', b'').decode('utf-8')
            msg_data = json.loads(msg.get('data', b'')) if isinstance(json.loads(msg.get('data', b'')),
                                                                      dict) else None
            if msg_channel == 'websocket_events' \
                    and msg_data and msg_data.get('type', '') == 'notice' \
                    and msg_data.get('user_id', ''):
                # 消息发送
                user_id = msg_data.get('user_id')
                cache_data = await cache.hgetall(f'msg_{user_id}')
                data = {k.decode('utf-8'): v.decode('utf-8') for k, v in cache_data.items()}
                offline_msgs = list(data.items())
                await channel_layer.group_send(
                    f'user_{user_id}', {
                        'type': 'send.message',
                        'message': json.dumps(offline_msgs)
                    }
                )
        except Exception as e:
            print(f"Error processing message: {e}")


# 创建管理器实例
listener_manager = RedisListenerManager()


# 自定义ASGI应用包装器
class ApplicationWrapper:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 在第一个请求时启动Redis监听器
        await listener_manager.create_task_once()
        await self.app(scope, receive, send)


# 创建基础ASGI应用
base_application = ProtocolTypeRouter({
    "http": django_application,
    "websocket": SessionMiddlewareStack(
        URLRouter(routing.websocket_urlpatterns)
    ),
})

# 包装应用
application = ApplicationWrapper(base_application)
