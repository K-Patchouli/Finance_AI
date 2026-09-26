import json
import re
from pathlib import Path


# ============================================================
# 1. 路径
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHECK_FILE = PROJECT_ROOT / "logs" / "check_results.json"
AI_RESULT_FILE = PROJECT_ROOT / "logs" / "final_review_results.json"
OUTPUT_FILE = PROJECT_ROOT / "logs" / "final_review_results_normalized.json"


# ============================================================
# 2. 通用取值函数
# ============================================================

def get_first(data, keys, default=None):
    """
    从多个可能字段中，取第一个存在且非空的值。
    """
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data and data[key] not in [None, ""]:
            return data[key]

    return default


# ============================================================
# 3. 提取证据页码
# ============================================================

def extract_page_number(evidence_source):
    """
    从证据来源文本中自动提取页码。

    支持：
    第10页
    第 10 页
    第10-11页
    页码：17
    p.17
    page 17
    """

    if evidence_source in [None, ""]:
        return ""

    text = str(evidence_source).strip()

    # 形式：第10页 / 第 10 页
    match = re.search(
        r"第\s*(\d+(?:-\d+)?)\s*页",
        text,
        flags=re.I
    )

    if match:
        return match.group(1)

    # 形式：页码：17 / 页码 17
    match = re.search(
        r"页码\s*[:：]?\s*(\d+(?:-\d+)?)",
        text,
        flags=re.I
    )

    if match:
        return match.group(1)

    # 形式：p.17 / P17
    match = re.search(
        r"\bp\.?\s*(\d+(?:-\d+)?)\b",
        text,
        flags=re.I
    )

    if match:
        return match.group(1)

    # 形式：page 17
    match = re.search(
        r"\bpage\s+(\d+(?:-\d+)?)\b",
        text,
        flags=re.I
    )

    if match:
        return match.group(1)

    return ""


# ============================================================
# 4. 标准化年份
# ============================================================

def normalize_year(value):
    """
    将年份统一成字符串，保留：
    2025
    2025年一季度
    2025上半年
    """

    if value in [None, ""]:
        return ""

    return str(value).strip()


# ============================================================
# 5. 单条结果标准化
# ============================================================

def normalize_one(original, ai_result):

    # --------------------------------------------------------
    # 基础信息
    # --------------------------------------------------------

    company = get_first(
        original,
        ["公司", "company"],
        get_first(ai_result, ["公司", "company"], "")
    )

    metric = get_first(
        original,
        ["指标", "metric"],
        get_first(ai_result, ["指标", "metric"], "")
    )

    report_year = get_first(
        original,
        ["年份", "报告年份", "year"],
        get_first(ai_result, ["年份", "报告年份", "year"], "")
    )

    # --------------------------------------------------------
    # 正确年份
    #
    # 注意：
    # 这里只读取明确存在的“正确年份”，
    # 不通过错误原因文字自行猜测。
    # --------------------------------------------------------

    correct_year = get_first(
        original,
        ["正确年份", "correct_year"],
        get_first(ai_result, ["正确年份", "correct_year"], "")
    )

    # --------------------------------------------------------
    # 报告原文
    # --------------------------------------------------------

    report_text = get_first(
        original,
        ["报告原文", "report_text", "source_text"],
        get_first(ai_result, ["报告原文"], "暂无")
    )

    # --------------------------------------------------------
    # 报告值
    # --------------------------------------------------------

    report_value = get_first(
        original,
        ["报告值", "report_value"],
        get_first(ai_result, ["报告值"], None)
    )

    # --------------------------------------------------------
    # 报告单位
    # --------------------------------------------------------

    report_unit = get_first(
        original,
        ["报告单位", "report_unit"],
        get_first(ai_result, ["报告单位"], "")
    )

    # --------------------------------------------------------
    # 正确值
    # --------------------------------------------------------

    correct_value = get_first(
        original,
        ["正确值", "原始值", "correct_value"],
        get_first(ai_result, ["正确值"], None)
    )

    # --------------------------------------------------------
    # 正确单位
    # --------------------------------------------------------

    correct_unit = get_first(
        original,
        ["正确单位", "原始单位", "correct_unit"],
        get_first(ai_result, ["正确单位"], "")
    )

    # --------------------------------------------------------
    # 核验状态
    # --------------------------------------------------------

    status = get_first(
        original,
        ["状态", "status"],
        ""
    )

    # --------------------------------------------------------
    # AI审校结果
    # --------------------------------------------------------

    has_error = get_first(
        ai_result,
        ["是否存在错误", "is_error"],
        "否"
    )

    error_type = get_first(
        ai_result,
        ["错误类型", "error_type"],
        "无错误"
    )

    reason = get_first(
        ai_result,
        ["错误原因", "reason"],
        None
    )

    correction = get_first(
        ai_result,
        ["修改建议", "correction"],
        "无需修改"
    )

    difference = get_first(
        original,
        ["差值", "difference"],
        get_first(ai_result, ["差值", "difference"], None)
    )

    # --------------------------------------------------------
    # 证据来源
    # --------------------------------------------------------

    evidence_source = get_first(
        original,
        ["证据来源", "来源", "原始来源", "source"],
        get_first(ai_result, ["证据来源"], "暂无")
    )

    # --------------------------------------------------------
    # 证据页码
    #
    # 优先使用已有结构化页码；
    # 如果没有，则从“证据来源”自动提取。
    # --------------------------------------------------------

    evidence_page = get_first(
        original,
        ["证据页码", "页码", "page", "page_number"],
        get_first(ai_result, ["证据页码", "页码", "page", "page_number"], "")
    )

    if evidence_page in [None, ""]:
        evidence_page = extract_page_number(evidence_source)

    # --------------------------------------------------------
    # 最终统一结构
    # --------------------------------------------------------

    result = {
        "公司": company,
        "指标": metric,

        # 报告年份
        "年份": normalize_year(report_year),

        # 新增：正确年份
        "正确年份": normalize_year(correct_year),

        # 报告数据
        "报告原文": report_text,
        "报告值": report_value,
        "报告单位": report_unit,

        # 正确数据
        "正确值": correct_value,
        "正确单位": correct_unit,

        # 核验
        "状态": status,

        # AI审校
        "是否存在错误": has_error,
        "错误类型": error_type,
        "错误原因": reason,
        "修改建议": correction,

        # 数值差异
        "差值": difference,

        # 证据
        "证据来源": evidence_source,
        "证据页码": evidence_page
    }

    return result


# ============================================================
# 6. 主程序
# ============================================================

def main():

    print("=" * 60)
    print("A模块：统一最终审校输出格式")
    print("=" * 60)

    # --------------------------------------------------------
    # 文件检查
    # --------------------------------------------------------

    if not CHECK_FILE.exists():
        raise FileNotFoundError(
            f"找不到核验结果：{CHECK_FILE}"
        )

    if not AI_RESULT_FILE.exists():
        raise FileNotFoundError(
            f"找不到AI审校结果：{AI_RESULT_FILE}"
        )

    # --------------------------------------------------------
    # 读取 B 核验结果
    # --------------------------------------------------------

    with open(
        CHECK_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        original_results = json.load(f)

    # --------------------------------------------------------
    # 读取 A AI结果
    # --------------------------------------------------------

    with open(
        AI_RESULT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        ai_results = json.load(f)

    # --------------------------------------------------------
    # 类型检查
    # --------------------------------------------------------

    if not isinstance(original_results, list):
        raise ValueError(
            "check_results.json 必须是 JSON 数组。"
        )

    if not isinstance(ai_results, list):
        raise ValueError(
            "final_review_results.json 必须是 JSON 数组。"
        )

    print(
        f"原始核验结果：{len(original_results)} 条"
    )

    print(
        f"AI审校结果：{len(ai_results)} 条"
    )

    # --------------------------------------------------------
    # 数量提示
    # --------------------------------------------------------

    if len(original_results) != len(ai_results):
        print("\n警告：两边结果数量不一致。")
        print(
            f"原始结果 = {len(original_results)}"
        )
        print(
            f"AI结果 = {len(ai_results)}"
        )
        print(
            "当前按照相同顺序进行合并。"
        )

    # --------------------------------------------------------
    # 合并
    # --------------------------------------------------------

    final_results = []

    total = max(
        len(original_results),
        len(ai_results)
    )

    for i in range(total):

        if i < len(original_results):
            original = original_results[i]
        else:
            original = {}

        if i < len(ai_results):
            ai_result = ai_results[i]
        else:
            ai_result = {}

        normalized = normalize_one(
            original,
            ai_result
        )

        final_results.append(normalized)

    # --------------------------------------------------------
    # 保存
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            final_results,
            f,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # 输出结果
    # --------------------------------------------------------

    print("\n处理完成。")

    print(
        f"输出文件：{OUTPUT_FILE}"
    )

    print(
        f"最终结果：{len(final_results)} 条"
    )

    print("\n最终字段：")

    print(
        "公司、指标、年份、正确年份、报告原文、"
        "报告值、报告单位、正确值、正确单位、状态、"
        "是否存在错误、错误类型、错误原因、修改建议、"
        "差值、证据来源、证据页码"
    )

    # --------------------------------------------------------
    # 简单检查
    # --------------------------------------------------------

    page_count = 0
    correct_year_count = 0

    for item in final_results:

        if item.get("证据页码") not in [None, ""]:
            page_count += 1

        if item.get("正确年份") not in [None, ""]:
            correct_year_count += 1

    print(
        f"\n已识别证据页码：{page_count} 条"
    )

    print(
        f"已保留正确年份：{correct_year_count} 条"
    )


if __name__ == "__main__":
    main()