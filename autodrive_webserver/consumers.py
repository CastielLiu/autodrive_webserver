# equal to views.py(视图函数) django

import sys
import json
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q, F

g_test_clients = []


# websocket消费者测试例
class TestConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        if self not in g_test_clients:
            g_test_clients.append(self)

        print("new ws_client connect. count: %d" % len(g_test_clients))

    def disconnect(self, close_code):
        if self in g_test_clients:
            g_test_clients.remove(self)
        print("ws_client disconnect. count: %d" % len(g_test_clients))

    def receive(self, text_data):
        print(text_data, type(text_data))
        text_data_dict = json.loads(text_data)
        message = text_data_dict['message']

        self.send(text_data=json.dumps({
            'message': message
        }))

