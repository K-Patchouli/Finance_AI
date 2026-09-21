import os
from openai import OpenAI

client = OpenAI(
    api_key="sk-85af704693254f27adc949726a1d9ec9",
    base_url="https://api.deepseek.com"  # 如果用其他大模型，改这里
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好"}]
    )
    print("API 测试成功！模型回复：", response.choices[0].message.content)
except Exception as e:
    print("API 测试失败，错误信息：", e)