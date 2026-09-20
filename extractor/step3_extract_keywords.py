import re
import pandas as pd

# 读取真实的年报文本
with open("../data/output.txt","r",encoding="utf-8") as f:
    text = f.read()

# 3. 定义更加精准且宽容的“筛子”
# .*? 允许中间有换行
# (亿元|万元|元|%)? 单位变成可选，没有也不影响抓数字
pattern = r'(营业收入|净利润|归母净利润|总资产).*?([\d,]+(?:\.\d+)?)\s*(亿元|万元|元|%)?'

# 4. 找数据，加上 re.S 支持跨行匹配
matches = re.findall(pattern, text, re.S)

# 5. 转换成表格
df = pd.DataFrame(matches, columns=["财务指标", "数值", "单位"])

# 6. 如果单位没有抓到，补个说明方便肉眼检查
df["单位"] = df["单位"].replace("", "元(默认)")
# 新增代码1：把完全一样的数据行去重（解决重复问题）
df = df.drop_duplicates()

# 新增代码2：过滤掉数值太短的行（比如只有"1"、"1.47"的误抓数据）
# 我们要求“数值”这一列的字符长度必须大于3位
df = df[df["数值"].str.len() > 3]
# 7. 打印结果
print("提取到的指标数据有：", len(df), "条")
print("--- 下面是前 10 条 ---")
print(df.head(10))

# 8. 保存
df.to_csv("financial_data.csv", index=False, encoding="utf-8-sig")
print("\n已保存为 financial_data.csv")