# 1. 导入我们要用的工具
import re  # re 是正则表达式工具，用来找规律
import pandas as pd  # pandas 是数据表格工具，起个外号叫 pd

# 2. 读取昨天生成的文本文件
with open("output.txt", "r", encoding="utf-8") as f:
    text = f.read()

# 3. 定义“筛子”（正则表达式）
# 下面的规则意思是：找“数字 + 可能有的小数点 + 数字 + 单位(亿元/万元/%)”
# \d 代表数字，+代表连续多个，\. 代表小数点，?代表可有可无
# (亿元|万元|%) 代表这三个单位里匹配任意一个
pattern = r'(\d+(?:\.\d+)?)\s*(亿元|万元|%)'

# 4. 用筛子在全文里找所有符合条件的内容
# findall 会把找到的所有东西变成一个列表
matches = re.findall(pattern, text)

# 5. 把找到的数据转换成表格（DataFrame）
# 我们给表格起两列名字：一个是“数值”，一个是“单位”
df = pd.DataFrame(matches, columns=["数值", "单位"])

# 6. 打印看看结果
print("提取到的数据总共有：", len(df), "条")
print("--- 下面是前 10 条数据 ---")
print(df.head(10)) # head(10) 意思是只看前10行，免得太长刷屏

# 7. 保存成 CSV 文件（相当于 Excel 表格）
# index=False 意思是不要自动生成序号，encoding="utf-8-sig" 是为了让Excel打开不乱码
df.to_csv("extracted_data.csv", index=False, encoding="utf-8-sig")
print("\n成功！请去左侧文件夹查看 extracted_data.csv 文件。")