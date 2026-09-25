import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# 1. 设置网页配置
st.set_page_config(page_title="金融报告智能审校", page_icon="📊", layout="wide")

# 2. 引入自定义 CSS 改变字体（必须放在 set_page_config 之后）
st.markdown("""
    <style>
    /* 1. 使用国内镜像源加载 Inter 字体 */
    @import url('https://fonts.loli.net/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* 2. 只针对文本元素修改，绝对不碰图标！ */
    .stApp, p, h1, h2, h3, h4, span, div {
        font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    
    /* 3. 让标题更紧凑，高级感+1 */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    /* 4. 强制让数据卡片（Metric）的数字使用等宽字体，金融感拉满 */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        font-family: 'Inter', 'Roboto Mono', monospace !important;
        font-weight: 600 !important;
        font-variant-numeric: tabular-nums;
    }
    
    /* 5. 给 Metric 卡片加上金融科技风格的阴影和圆角 */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #eaeaea;
    }
    
    /* 6. 让分割线更柔和 */
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 0;
        border-top: 1px solid #eaeaea;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 标题和说明
st.title("金融研究报告智能审校系统")
st.write("上传一份文字型上市公司年报 PDF，系统将自动提取核心财务指标并进行规则核验。")
st.markdown("---")

# ================= 页面布局：分为左右两列 =================
col1, col2 = st.columns([1, 2])

# --- 左侧：文件上传区 ---
with col1:
    st.subheader("📁 文件上传")
    uploaded_file = st.file_uploader("请选择PDF文件", type=["pdf"])
    st.info("💡 提示：目前系统仅支持文字版PDF，如财报有表格错位，提取结果可能会有偏差。")

# --- 右侧：核验结果区 ---
with col2:
    st.subheader("🔍 核验结果")
    
    if uploaded_file is None:
        st.info("请先在左侧上传需要审核的 PDF 文件。")
    else:
        with st.spinner("正在解析PDF、提取数据并执行核验..."):
            # ---------------- 流水线1：解析PDF ----------------
            text = ""
            with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # ---------------- 流水线2：提取数据 ----------------
            pattern = r'(营业收入|净利润|归母净利润|总资产).*?([\d,]+(?:\.\d+)?)\s*(亿元|万元|元|%)?'
            matches = re.findall(pattern, text, re.S)
            
            if len(matches) == 0:
                st.warning("未能从PDF中提取到任何财务指标，请检查PDF是否为文字版。")
            else:
                df = pd.DataFrame(matches, columns=["财务指标", "数值", "单位"])
                df["单位"] = df["单位"].replace("", "元(默认)")
                df = df.drop_duplicates()
                df = df[df["数值"].str.len() > 3]
                
                # ---------------- 流水线3：数据核验 ----------------
                df["数值_纯数字"] = df["数值"].astype(str).str.replace(",", "", regex=False).astype(float)
                standard_answers = {"营业收入": 53909252220.51, "总资产": 319918844905.58}
                tolerance = 1000.0
                
                error_list = []
                for index, row in df.iterrows():
                    metric = row["财务指标"]
                    reported_value = row["数值_纯数字"]
                    if metric in standard_answers:
                        standard_value = standard_answers[metric]
                        if abs(reported_value - standard_value) > tolerance:
                            error_list.append({
                                "指标": metric,
                                "报告值": reported_value,
                                "标准值": standard_value
                            })
                
                # ---------------- 流水线4：前端精美展示 ----------------
                rev_row = df[df["财务指标"] == "营业收入"]
                asset_row = df[df["财务指标"] == "总资产"]
                
                m1, m2 = st.columns(2)
                if not rev_row.empty:
                    rev_billion = rev_row.iloc[0]["数值_纯数字"] / 100000000 
                    m1.metric("营业收入（亿元）", f"{rev_billion:,.2f}")
                if not asset_row.empty:
                    asset_billion = asset_row.iloc[0]["数值_纯数字"] / 100000000
                    m2.metric("总资产（亿元）", f"{asset_billion:,.2f}")

                st.markdown("### 📢 异常报警")
                if len(error_list) > 0:
                    for err in error_list:
                        st.error(f"🚨 **发现错误！** 指标：{err['指标']} | 报告写的是：{err['报告值']:,.2f} | 正确应为：{err['标准值']:,.2f}")
                else:
                    st.success("✅ 所有核心指标核验通过，未发现明显数据异常。")

                st.markdown("### 📋 提取到的全部原始数据")
                st.dataframe(df[["财务指标", "数值", "单位"]], use_container_width=True)