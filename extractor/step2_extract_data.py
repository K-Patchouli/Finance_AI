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
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"抽取失败: {e}")
        return []


if __name__ == "__main__":
    with open("data/output.txt", "r", encoding="utf-8") as f:
        full_text = f.read()
    pages = full_text.split("==========")

    all_results = []
    for page in pages:
        if page.strip():
            print(f"正在抽取第 {len(all_results) + 1} 页...")
            results = extract_financial_data(page)
            if results:
                all_results.extend(results)
    with open("extracted_data.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n成功抽取 {len(all_results)} 条财务数据，已保存到 extracted_data.json")