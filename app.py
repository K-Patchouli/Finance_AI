# 1. 导入工具包
import streamlit as st  # 这是做网页的工具
import pandas as pd     # 用来读取数据表格
import os               # 用来找文件路径

# 2. 设置网页的标题和说明
st.title("📊 金融研究报告智能审校系统")
st.write("欢迎使用！请上传需要审核的研究报告PDF文件。")

# 3. 创建一个“上传文件”的按钮，只允许传 PDF
uploaded_file = st.file_uploader("点击这里上传文件", type=["pdf"])


# 4. 如果用户上传了文件
if uploaded_file is not None:
    st.success(f"文件【{uploaded_file.name}】上传成功！")
    
    # （暂时不做复杂解析，先展示一下我们之前跑出的数据表格来测试）
    st.subheader("📋 历史核验结果展示")
    csv_path = os.path.join("logs", "financial_data.csv")
    
    # 如果之前生成了 CSV 文件，就把它显示在网页上
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df) # 在网页上画出一个表格
    else:
        st.warning("还没有核验数据，请先运行 step3 和 step4 生成数据。")