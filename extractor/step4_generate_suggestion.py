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

from prompts.suggestion_prompt import SUGGESTION_PROMPT


# =========================================================
# 2. DeepSeek API
# =========================================================

API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not API_KEY:
    print("错误：没有检测到 DEEPSEEK_API_KEY")
    print("请先在 Git Bash 中设置 API Key。")
    print("例如：")
    print("export DEEPSEEK_API_KEY='你的新API_Key'")
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
    "classification_results.json"
)

输出文件 = os.path.join(
    项目根目录,
    "logs",
    "final_review_results.json"
)


# =========================================================
# 4. 字段统一
#
# 兼容 Step 3 旧格式：
# is_error
# error_type
# reason
# report_value
# correct_value
# difference
# correction
#
# 以及中文格式。
# =========================================================

def 统一字段(data):

    if not isinstance(data, dict):
        return data

    result = {}

    # 是否存在错误
    if "是否存在错误" in data:
        是否存在错误 = data["是否存在错误"]

    elif "is_error" in data:
        是否存在错误 = data["is_error"]

    else:
        是否存在错误 = None

    if isinstance(是否存在错误, bool):
        是否存在错误 = "是" if 是否存在错误 else "否"

    result["是否存在错误"] = 是否存在错误

    # 错误类型
    if "错误类型" in data:
        result["错误类型"] = data["错误类型"]

    elif "error_type" in data:
        result["错误类型"] = data["error_type"]

    else:
        result["错误类型"] = None

    # 错误原因
    if "错误原因" in data:
        result["错误原因"] = data["错误原因"]

    elif "reason" in data:
        result["错误原因"] = data["reason"]

    else:
        result["错误原因"] = None

    # 报告值
    if "报告值" in data:
        result["报告值"] = data["报告值"]

    elif "report_value" in data:
        result["报告值"] = data["report_value"]

    else:
        result["报告值"] = None

    # 正确值
    if "正确值" in data:
        result["正确值"] = data["正确值"]

    elif "correct_value" in data:
        result["正确值"] = data["correct_value"]

    else:
        result["正确值"] = None

    # 差值
    if "差值" in data:
        result["差值"] = data["差值"]

    elif "difference" in data:
        result["差值"] = data["difference"]

    else:
        result["差值"] = None

    # 修改建议
    if "修改建议" in data:
        result["修改建议"] = data["修改建议"]

    elif "correction" in data:
        result["修改建议"] = data["correction"]

    else:
        result["修改建议"] = None

    return result


# =========================================================
# 5. 清理 DeepSeek 返回的 JSON
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

    # 找到 JSON 开头
    起始位置列表 = []

    for 字符 in ["{", "["]:
        位置 = content.find(字符)

        if 位置 != -1:
            起始位置列表.append(位置)

    if 起始位置列表:
        content = content[min(起始位置列表):]

    # 找到 JSON 结尾
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
# 6. 生成单条最终审校意见
# =========================================================

def 生成审校意见(分类结果):

    try:

        # 先统一成中文输入格式
        中文数据 = 统一字段(分类结果)

        数据文本 = json.dumps(
            中文数据,
            ensure_ascii=False,
            indent=2
        )

        # 不使用 .format()
        prompt = SUGGESTION_PROMPT.replace(
            "{data}",
            数据文本
        )

        # 调用 DeepSeek
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

        # 清理返回内容
        content = 清理JSON文本(content)

        # 解析 JSON
        result = json.loads(content)

        # 最终再统一一次字段
        result = 统一字段(result)

        # 补充审校结论
        if result["是否存在错误"] == "是":

            result["审校结论"] = "发现该项数据存在错误。"

        elif result["是否存在错误"] == "否":

            result["审校结论"] = "该项数据核验正确，无需修改。"

        return {
            "是否存在错误": result.get("是否存在错误"),
            "错误类型": result.get("错误类型"),
            "审校结论": result.get("审校结论"),
            "错误原因": result.get("错误原因"),
            "报告值": result.get("报告值"),
            "正确值": result.get("正确值"),
            "差值": result.get("差值"),
            "修改建议": result.get("修改建议")
        }

    except json.JSONDecodeError as e:

        print("JSON解析失败：", e)

        print("\n模型原始返回：")

        print(
            content
            if "content" in locals()
            else "无"
        )

        return None

    except Exception as e:

        print("生成审校意见失败：", e)

        return None


# =========================================================
# 7. 主程序
# =========================================================

def 主程序():

    print("================================")
    print("A模块：最终审校意见生成")
    print("================================")

    # -----------------------------------------------------
    # 检查输入文件
    # -----------------------------------------------------

    if not os.path.exists(输入文件):

        print("错误：找不到输入文件：")
        print(输入文件)

        sys.exit(1)

    # -----------------------------------------------------
    # 读取 Step 3 结果
    # -----------------------------------------------------

    try:

        with open(
            输入文件,
            "r",
            encoding="utf-8"
        ) as f:

            分类结果 = json.load(f)

    except Exception as e:

        print("读取 classification_results.json 失败：")
        print(e)

        sys.exit(1)

    # -----------------------------------------------------
    # 检查格式
    # -----------------------------------------------------

    if not isinstance(分类结果, list):

        print(
            "错误：classification_results.json "
            "必须是 JSON 数组。"
        )

        sys.exit(1)

    print(
        f"\n读取到 {len(分类结果)} 条分类结果"
    )

    # -----------------------------------------------------
    # 开始逐条处理
    # -----------------------------------------------------

    最终结果 = []

    for i, item in enumerate(
        分类结果,
        start=1
    ):

        print(
            f"\n正在生成第 {i}/{len(分类结果)} 条审校意见"
        )

        result = 生成审校意见(item)

        if result is not None:

            最终结果.append(result)

            print("\n审校意见：")

            print(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2
                )
            )

        else:

            print("本条生成失败。")

    # -----------------------------------------------------
    # 保存最终结果
    # -----------------------------------------------------

    try:

        with open(
            输出文件,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                最终结果,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        print("保存最终结果失败：")
        print(e)

        sys.exit(1)

    # -----------------------------------------------------
    # 完成
    # -----------------------------------------------------

    print("\n================================")
    print("最终审校意见生成完成")
    print(f"成功生成：{len(最终结果)} 条")
    print("结果文件：")
    print(输出文件)
    print("================================")


# =========================================================
# 8. 程序入口
# =========================================================

if __name__ == "__main__":
    主程序()