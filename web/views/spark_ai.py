from utils.spark_ai_util import ask_ai_spark
from django.http import HttpRequest
from django.http.response import StreamingHttpResponse
import json


def ask_ai(request: HttpRequest):
    data = json.loads(request.body)
    question = data.get('question', '')
    if not question:
        return StreamingHttpResponse('', content_type='text/event-stream')

    def event_stream():
        for chunk in ask_ai_spark(question):
            yield chunk

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
