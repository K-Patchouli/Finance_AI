import os
import json
from openai import OpenAI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.extract_prompt import EXTRACT_PROMPT

client = OpenAI(
    api_key="sk-85af704693254f27adc949726a1d9ec9",
    base_url="https://api.deepseek.com"
)


def extract_financial_data(text):
    """
    核心函数：输入报告文本，输出结构化的金融数据 JSON
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": EXTRACT_PROMPT.format(text=text)}
            ],
            response_format={"type": "json_object"}  # 强制返回JSON
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"抽取失败: {e}")
        return []


if __name__ == "__main__":
    # 测试用的一段模拟报告文本
    test_text = "根据2024年年度报告，公司实现营业收入128.6亿元，同比增长15.3%。归属于上市公司股东的净利润为25.4亿元。"

    print("正在调用大模型抽取...")
    results = extract_financial_data(test_text)

    print("\n抽取结果：")
    print(json.dumps(results, ensure_ascii=False, indent=2))