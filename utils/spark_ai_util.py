# encoding:UTF-8
import json
import requests
from django.conf import settings

# 获取地址：https://console.xfyun.cn/services/bmx1

api_key = f"Bearer {settings.SPARK_API_PASSWORD}"
url = "https://spark-api-open.xf-yun.com/v1/chat/completions"


# 请求模型，并将结果输出
def ask_ai_spark(val_message):
    message = [{'role': 'user', 'content': val_message}]
    # 初始化请求体
    headers = {
        'Authorization': api_key,
        'content-type': "application/json"
    }
    body = {
        "model": "4.0Ultra",
        "user": "user_id",
        "messages": message,
        # 下面是可选参数
        "stream": True,
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_mode": "deep"
                }
            }
        ]
    }
    isFirstContent = True  # 首帧标识

    response = requests.post(url=url, json=body, headers=headers, stream=True)
    # print(response)
    for chunks in response.iter_lines():
        # 打印返回的每帧内容
        if chunks and '[DONE]' not in str(chunks):
            data_org = chunks[6:]

            chunk = json.loads(data_org)
            text = chunk['choices'][0]['delta']

            # 判断最终结果状态并输出
            if 'content' in text and '' != text['content']:
                content = text["content"]
                if isFirstContent:
                    isFirstContent = False
                yield content


# 主程序入口
if __name__ == '__main__':
    question = '你好'
    for i in ask_ai_spark(question):
        print(i)
