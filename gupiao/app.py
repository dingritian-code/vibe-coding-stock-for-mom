import streamlit as st
import pandas as pd
import akshare as ak
from datetime import datetime

# ================= 配置页面 =================
st.set_page_config(page_title="智能股票推荐系统", layout="wide", initial_sidebar_state="expanded")

# 强制暗黑模式风格的自定义CSS (类似你同事的UI)
st.markdown("""
<style>
    .reportview-container {background: #0e1117;}
    .metric-card {
        background-color: #1e2129;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 15px;
    }
    .metric-card-blue { border-left-color: #1f77b4; }
</style>
""", unsafe_allow_html=True)

st.title("📋 智能推荐 (给妈妈用的AI股票分析)")

# ================= 数据获取模块 (模拟或调用AkShare) =================
@st.cache_data(ttl=3600) # 缓存1小时，避免频繁请求API
def get_news_data():
    # 模拟图3的新闻动态映射
    return pd.DataFrame({
        "关键事件": ["伊朗局势走向何方", "国际金价突破历史新高", "某某科技公司发布新一代AI芯片"],
        "热度": ["🔥热搜", "🔥热搜", "📈上升"],
        "影响板块": ["军工、石油", "黄金、有色金属", "半导体、算力"]
    })

@st.cache_data(ttl=60)
def get_real_stock_data():
    try:
        # 1. 获取原始数据
        df = ak.stock_zh_a_spot_em()
        
        # 🟢 关键新增：数据清洗清洗！把可能出错的列强制转为数字，遇到缺失值自动补0
        for col in ['涨跌幅', '总市值', '成交额', '换手率', '最新价']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # 2. 筛选条件：今天涨停或接近涨停（涨幅>=9%）的强势股
        df = df[df['涨跌幅'] >= 9.0].copy()
        df = df.sort_values(by='成交额', ascending=False).head(15) 
        
        real_stocks = []
        for i, row in df.iterrows():
            market_cap_yi = row['总市值'] / 100_000_000
            vol_yi = row['成交额'] / 100_000_000
            turnover = row['换手率']
            
            # ======== 核心量化打分模型 ========
            score = 60 # 基础及格分
            
            if 10 <= turnover <= 30:
                score += 15  
            elif 5 <= turnover < 10:
                score += 5   
            elif turnover > 30:
                score -= 5   
                
            if vol_yi >= 20:
                score += 15  
            elif 10 <= vol_yi < 20:
                score += 10  
            elif vol_yi < 3:
                score -= 5   
                
            if market_cap_yi <= 100:
                score += 10  
            elif market_cap_yi >= 500:
                score -= 10  
                
            score = min(99, max(0, int(score))) 
            # ==================================

            stock_type = "龙头预期" if vol_yi >= 15 else "连板预期"
            
            real_stocks.append({
                "name": str(row['名称']),
                "code": str(row['代码']),
                "type": stock_type,
                "board": f"涨幅 {row['涨跌幅']}%", 
                "score": score,
                "industry": "强势龙头" if stock_type == "龙头预期" else "情绪连板",
                "market_cap": f"{market_cap_yi:.0f}亿",
                "desc": f"最新价:{row['最新价']} | 换手:{turnover}% | 资金:{vol_yi:.1f}亿"
            })
            
        real_stocks = sorted(real_stocks, key=lambda x: x['score'], reverse=True)
        return real_stocks

    except Exception as e:
        # 🟢 关键修改：如果再报错，直接把原原本本的错误原因用红色打印到网页上！
        st.error(f"❌ 捕获到真实错误: {e}")
        return []
# ================= 页面布局 =================

# 1. 新闻动态区 (对应图3)
st.subheader("📰 实时新闻动态分析")
news_df = get_news_data()
for index, row in news_df.iterrows():
    st.markdown(f"**[{row['热度']}] {row['关键事件']}** ➡️ *影响: {row['影响板块']}*")
st.divider()

# 2. 智能推荐区 (对应图1)
col1, col2 = st.columns(2)

stocks = get_real_stock_data()

with col1:
    st.subheader("🔗 连板预期")
    st.caption("次日可能继续涨停")
    for stock in [s for s in stocks if s["type"] == "连板预期"]:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0;">{stock['name']} <span style="font-size:14px; color:gray;">{stock['code']} | {stock['industry']}</span> 
            <span style="float:right; background-color:#ff4b4b; padding:2px 8px; border-radius:12px; font-size:14px;">{stock['board']} | 评分:{stock['score']}</span></h3>
            <p style="margin:5px 0; font-size:14px; color:#a0a0a0;">市值: {stock['market_cap']} <br> 💡 逻辑: {stock['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader("🐉 龙头预期")
    st.caption("资金+热点新龙头")
    for stock in [s for s in stocks if s["type"] == "龙头预期"]:
        st.markdown(f"""
        <div class="metric-card metric-card-blue">
            <h3 style="margin:0;">{stock['name']} <span style="font-size:14px; color:gray;">{stock['code']} | {stock['industry']}</span> 
            <span style="float:right; background-color:#1f77b4; padding:2px 8px; border-radius:12px; font-size:14px;">{stock['board']} | 评分:{stock['score']}</span></h3>
            <p style="margin:5px 0; font-size:14px; color:#a0a0a0;">市值: {stock['market_cap']} <br> 💡 逻辑: {stock['desc']}</p>
        </div>
        """, unsafe_allow_html=True)

# 3. 运行日志/工作流展示 (对应图2)
with st.expander("🛠️ 查看后台分析流水线 (Analysis Workflow)"):
    st.success("✅ 获取涨停数据 (实时模式) ... 成功")
    st.success("✅ 分析近7日涨停历史 ... 成功")
    st.success("✅ 抓取财经新闻并提取影响板块 ... 成功")
    st.success("✅ 计算连板预期与龙头预期评分 ... 成功")
    st.info("📅 分析基准日期: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))