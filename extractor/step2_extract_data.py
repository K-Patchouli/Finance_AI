import os
import sys
import json
import re
from openai import OpenAI

# 将项目根目录加入 Python 搜索路径
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from prompts.extract_prompt import EXTRACT_PROMPT


# =========================
# DeepSeek API 配置
# =========================
client = OpenAI(
    api_key="sk-85af704693254f27adc949726a1d9ec9",  # 在这里填写你的 DeepSeek API Key
    base_url="https://api.deepseek.com"
)


def extract_financial_data(text):
    """
    核心函数：
    输入报告文本，调用 DeepSeek 提取结构化金融数据，
    返回 Python 对象（通常为 list 或 dict）。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": EXTRACT_PROMPT.format(text=text)
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        if not content:
            print("抽取失败：模型返回为空")
            return []

        # 去除 Markdown 代码块
        content = content.strip()
        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )
        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        content = content.strip()

        # 找到 JSON 的起始位置
        starts = [
            i
            for i in [
                content.find("["),
                content.find("{")
            ]
            if i != -1
        ]

        if starts:
            content = content[min(starts):]

        # 尝试解析 JSON
        result = json.loads(content)

        return result

    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        print("模型原始返回内容：")
        print(content if "content" in locals() else "无")
        return []

    except Exception as e:
        print(f"抽取失败: {e}")
        return []


# =========================
# 主程序
# =========================
if __name__ == "__main__":

    input_file = "data/output.txt"
    output_file = "extracted_data.json"

    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"错误：找不到输入文件 {input_file}")
        sys.exit(1)

    # 读取文本
    with open(input_file, "r", encoding="utf-8") as f:
        full_text = f.read()

    # 按页面分割
    pages = full_text.split("==========")

    all_results = []

    for page_index, page in enumerate(pages, start=1):

        if not page.strip():
            continue

        print(f"正在抽取第 {page_index} 页...")

        results = extract_financial_data(page)

        if results:
            # 如果返回的是列表，直接合并
            if isinstance(results, list):
                all_results.extend(results)

            # 如果返回的是单个字典，加入列表
            elif isinstance(results, dict):
                all_results.append(results)

    # 保存结果
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            all_results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\n成功抽取 {len(all_results)} 条财务数据，"
        f"已保存到 {output_file}"
    )