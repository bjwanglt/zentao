from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync


class MsgConsummer(WebsocketConsumer):

    def websocket_connect(self, message):
        # 客户端向后端发送websocket连接的请求，自动触发
        print(f'websocket_connect {message=}')
        self.accept()  # 服务端允许和客户端创建连接
        # 保存连接对象
        async_to_sync(self.channel_layer.group_add)('9527', self.channel_name)

    def websocket_receive(self, message):
        # 浏览器基于websocket向后端发送数据 自动触发
        # 服务端也可以主动断开 self.close()
        print(f'websocket_receive {message=}')
        # 规定客户端发送 close 即表示断连
        if message and message['text'] == 'close':
            self.close()
            raise StopConsumer()  # 如果希望服务端主动断开连接时不触发 websocket_disconnect ，可以抛出该异常
        else:
            # self.send('OKOKOKOKOK')
            # 消息群发 handle是自定义方法，即通知组内所有客户端，执行该方法
            async_to_sync(self.channel_layer.group_send)('9527', dict(type='handle', message=message))

    def handle(self, event):
        # event={'type': 'handle', 'message': {'type': 'websocket.receive', 'text': '11'}}
        text = event['message']['text']
        self.send(text)

    def text_message(self, event):
        # event={'type': 'handle', 'message': {'type': 'websocket.receive', 'text': '11'}}
        text = event['message']
        self.send(text)

    def websocket_disconnect(self, message):
        # 客户端与服务端断开连接触发 (无论是客户端发起的断连还是服务端发起的断连)
        print(f'websocket_disconnect {message=}')
        # 移出组
        async_to_sync(self.channel_layer.group_discard)('9527', self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            '9527',  # 群组名
            {
                'type': 'text.message',  # 对应 Consumer 中的方法 text_message
                'message': '这是发送的文本'
            }
        )
        raise StopConsumer()
