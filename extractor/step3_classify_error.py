import os
import sys
import json
import re

from openai import OpenAI


# =========================================================
# 1. 项目路径
# =========================================================

当前文件夹 = os.path.dirname(os.path.abspath(__file__))
项目根目录 = os.path.dirname(当前文件夹)

sys.path.append(项目根目录)

from prompts.classify_prompt import CLASSIFY_PROMPT


# =========================================================
# 2. DeepSeek API
# =========================================================

API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not API_KEY:
    print("错误：没有检测到 DEEPSEEK_API_KEY")
    print("请先设置 DeepSeek API Key。")
    sys.exit(1)

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)


# =========================================================
# 3. 输入、输出文件
# =========================================================

输入文件 = os.path.join(
    项目根目录,
    "logs",
    "check_results.json"
)

输出文件 = os.path.join(
    项目根目录,
    "logs",
    "classification_results.json"
)


# =========================================================
# 4. 清理模型返回的 JSON
# =========================================================

def 清理JSON文本(content):

    if not content:
        return ""

    content = content.strip()

    # 去除 Markdown 代码块
    content = re.sub(
        r"^```json\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"^```\s*",
        "",
        content
    )

    content = re.sub(
        r"\s*```$",
        "",
        content
    )

    content = content.strip()

    # 找 JSON 起始位置
    起始位置 = []

    for 字符 in ["{", "["]:

        位置 = content.find(字符)

        if 位置 != -1:
            起始位置.append(位置)

    if 起始位置:
        content = content[min(起始位置):]

    # 截取 JSON 结尾
    if content.startswith("{"):

        结束位置 = content.rfind("}")

        if 结束位置 != -1:
            content = content[:结束位置 + 1]

    elif content.startswith("["):

        结束位置 = content.rfind("]")

        if 结束位置 != -1:
            content = content[:结束位置 + 1]

    return content.strip()


# =========================================================
# 5. 单条错误分类
# =========================================================

def 分类错误(核验数据):

    try:

        数据文本 = json.dumps(
            核验数据,
            ensure_ascii=False,
            indent=2
        )

        # 使用 replace，不使用 format
        # 防止 Prompt 中的 JSON {} 产生冲突
        prompt = CLASSIFY_PROMPT.replace(
            "{data}",
            数据文本
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        if not content:
            print("模型返回为空")
            return None

        content = 清理JSON文本(content)

        result = json.loads(content)

        return result

    except json.JSONDecodeError as e:

        print("JSON 解析失败：", e)

        print("模型原始返回：")

        print(
            content
            if "content" in locals()
            else "无"
        )

        return None

    except Exception as e:

        print("分类失败：", e)

        return None


# =========================================================
# 6. 主程序
# =========================================================

if __name__ == "__main__":

    print("================================")
    print("A模块：错误分类与原因解释")
    print("================================")

    if not os.path.exists(输入文件):

        print("错误：找不到输入文件：")
        print(输入文件)

        sys.exit(1)

    # 读取 B 模块核验结果
    with open(
        输入文件,
        "r",
        encoding="utf-8"
    ) as f:

        核验结果 = json.load(f)

    print(
        f"\n读取到 {len(核验结果)} 条核验结果"
    )

    分类结果 = []

    for i, item in enumerate(
        核验结果,
        start=1
    ):

        指标 = item.get(
            "指标",
            "未知指标"
        )

        print(
            f"\n正在分析第 {i}/{len(核验结果)} 条："
            f"{指标}"
        )

        result = 分类错误(item)

        if result is not None:

            # 保留 B 模块原始核验结果
            result["原始核验结果"] = item

            分类结果.append(result)

            print("\n分类结果：")

            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2
                )
            )

        else:

            print("本条分类失败。")

    # 保存结果
    with open(
        输出文件,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            分类结果,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n================================")
    print("错误分类完成")
    print(f"成功生成：{len(分类结果)} 条结果")
    print("结果文件：")
    print(输出文件)
    print("================================")