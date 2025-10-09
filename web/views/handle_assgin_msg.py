from uuid import uuid4

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django_redis import get_redis_connection
from redis import Redis
import json


class AssginMsgHandler(WebsocketConsumer):

    def send_message(self, event):
        # event={'type': 'handle', 'message': {'type': 'websocket.receive', 'text': '11'}}
        text = event['message']
        self.send(text)

    def websocket_connect(self, message):
        print(f'websocket_connect {message=}')
        user_id = None
        session = self.scope['session']
        if session and session.get('userinfo', '') and (user_id := session.get('userinfo').get('userid')):
            async_to_sync(self.channel_layer.group_add)(f'user_{user_id}', self.channel_name)
            self.accept()
            # 获取离线消息
            cache: Redis = get_redis_connection('offline_msgs')
            data = {k.decode('utf-8'): v.decode('utf-8') for k, v in cache.hgetall(f'msg_{user_id}').items()}
            offline_msgs = list(data.items())
            async_to_sync(self.channel_layer.group_send)(f'user_{user_id}', {
                'type': 'send.message',
                'message': json.dumps(offline_msgs)
            })
        else:
            self.close()

        """
        客户端发起连接
        1 连接加入群组  一人一个群组 ？
        2 检查该用户是否有待接收的消息，如果有则发送
        """

    def websocket_receive(self, message):
        print(f'websocket_connect {message=}')
        user_id = None
        session = self.scope['session']
        if session and session.get('userinfo', '') and (user_id := session.get('userinfo').get('userid')):
            cache: Redis = get_redis_connection('offline_msgs')
            cache.hdel(f'msg_{user_id}', message.get('text'))
            # TODO 重新发送
            data = {k.decode('utf-8'): v.decode('utf-8') for k, v in cache.hgetall(f'msg_{user_id}').items()}
            offline_msgs = list(data.items())
            async_to_sync(self.channel_layer.group_send)(f'user_{user_id}', {
                'type': 'send.message',
                'message': json.dumps(offline_msgs)
            })

    def websocket_disconnect(self, message):
        print(f'websocket_connect {message=}')
        user_id = None
        session = self.scope['session']
        if session and session.get('userinfo', '') and (user_id := session.get('userinfo').get('userid')):
            async_to_sync(self.channel_layer.group_discard)(f'user_{user_id}', self.channel_name)
