# 1. 导入工具包
import pdfplumber

# 2. 定义输入和输出的文件名
input_pdf = "data/annual_report.pdf"
output_txt = "data/output.txt"

# 3. 打开PDF
with pdfplumber.open(input_pdf) as pdf:
    # 获取总页数
    total_pages = len(pdf.pages)
    
    # 4. 打开一个文本文件准备写入
    # 'w' 表示写入模式（会覆盖原文件），encoding='utf-8' 是为了防止中文乱码
    with open(output_txt, "w", encoding="utf-8") as f:
        
        # 5. 用 for 循环，一页一页地读取
        # enumerate 是个好工具，它能同时给我们页码(i)和这一页的对象(page)
        for i, page in enumerate(pdf.pages):
            # 提取当前页的文字
            text = page.extract_text()
            
            # 万一某页是空白页，text可能是 None，加个判断防止报错
            if text: 
                # 写入页码作为分隔符（i是从0开始的，所以写 i+1 符合常人习惯）
                f.write(f"========== 第 {i+1} 页 ==========\n")
                # 写入这一页的文字
                f.write(text)
                # 写两个换行，隔开下一页
                f.write("\n\n")

# 6. 循环结束后，打印提示
print(f"大功告成！一共成功提取了 {total_pages} 页的内容。")
print(f"请去左侧的文件夹里，找到并打开 {output_txt} 查看结果。")