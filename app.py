import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.calculations import (
    clean_data,
    filter_by_time_range,
    calculate_peak_load,
    calculate_total_consumption,
    find_peak_info,
    check_peak_threshold,
    calculate_kepco_cost,
    generate_interactive_chart,
    generate_html_report,
    generate_energy_insights
)

# 1. 페이지 설정 및 다크 테마 CSS 지정
st.set_page_config(page_title="산단 ENERGY CLOUD - 통합 관제 시스템", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif !important;
    }
    .stMetric {
        background-color: #1e222d;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #2e3545;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ 산단 ENERGY CLOUD 통합 에너지 관제 시스템")

# 2. 사이드바 - 제어 옵션
st.sidebar.header("📁 0. 데이터 및 계통 선택")
uploaded_file = st.sidebar.file_uploader("전력 사용량 CSV 업로드", type=["csv"])

@st.cache_data
def load_default_data():
    return pd.read_csv("data/sample_load.csv")

if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file)
        st.sidebar.success("✅ 사용자 데이터 연동 완료")
    except Exception:
        df_raw = load_default_data()
else:
    df_raw = load_default_data()

st.sidebar.header("1. 피크 컷 & ESS 운용 설정")
threshold_kw = st.sidebar.number_input("목표 피크 전력 (kW)", min_value=0.0, value=450.0, step=10.0)
ess_capacity = st.sidebar.slider("ESS 용량 설정 (kWh)", min_value=0, max_value=500, value=200)

st.sidebar.header("2. 한전 요금 단가")
base_rate = st.sidebar.number_input("기본요금 단가 (원/kW)", min_value=0.0, value=8320.0, step=100.0)

# 3. 기본 데이터 계산
df_clean = clean_data(df_raw)
peak_kw = calculate_peak_load(df_clean)
peak_info = find_peak_info(df_clean)
total_kwh = calculate_total_consumption(df_clean)
rates_dict = {'off_peak': 65.2, 'mid_peak': 109.0, 'on_peak': 191.1}
kepco_cost = calculate_kepco_cost(df_clean, base_rate=base_rate, rates=rates_dict)
is_exceeded = check_peak_threshold(peak_kw, threshold_kw)
insight_text = generate_energy_insights(peak_info['peak_time'], is_exceeded)

# 상단 대시보드 요약 지표
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("최대수요전력", f"{peak_kw:.1f} kW")
col2.metric("피크 발생시각", peak_info['peak_time'] if peak_info['peak_time'] else "-")
col3.metric("총 사용량", f"{total_kwh:,.1f} kWh")
col4.metric("추정 총 요금", f"{int(kepco_cost['total_cost']):,} 원")
col5.metric("DC Grid 전압 상태", "742.6 V (정상)")

st.info(f"💡 **AI 에너지 운영 진단:** {insight_text}")

# 4. 멀티 관제 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 전력 추이 & ESS", 
    "🌐 DC Grid & PV 관제", 
    "🔋 VPP 운영 스케줄링", 
    "💰 요금 분석 명세", 
    "📄 보고서 출력"
])

# Tab 1: 기본 전력 추이 및 ESS 피크 컷 시각화
with tab1:
    st.subheader("시간대별 전력 사용량 및 ESS 충/방전 시뮬레이션")
    fig = generate_interactive_chart(df_clean, threshold_kw)
    st.plotly_chart(fig, use_container_width=True)

# Tab 2: DC Grid 및 PV 인버터 감시 (관제센터 대시보드 스타일)
with tab2:
    st.subheader("🌐 DC Grid 전력 흐름 및 PV 인버터 제어")
    
    col_pv1, col_pv2 = st.columns([1, 2])
    with col_pv1:
        st.markdown("#### ⚡ DC-GRID 실시간 현황")
        st.write(f"- **KEPCO 수전:** 148.95 kW")
        st.write(f"- **태양광 발전량:** 222.00 kW")
        st.write(f"- **ESS 발전량:** 145.00 kW")
        st.write(f"- **Fresh ESS SOC:** 72.60 %")
        st.write(f"- **Reuse ESS SOC:** 62.90 %")
    
    with col_pv2:
        st.markdown("#### ☀️ PV 인버터 채널별 상태 감시 (PV1 ~ PV8)")
        pv_status = pd.DataFrame({
            '인버터 채널': [f'PV{i}' for i in range(1, 9)],
            '상태': ['정상']*7 + ['점검필요'],
            '출력(kW)': [5.62, 5.50, 5.48, 5.60, 5.55, 5.40, 5.52, 0.10],
            '인버터 효율(%)': [98.2, 98.0, 97.9, 98.1, 98.3, 97.8, 98.0, 45.2]
        })
        st.dataframe(pv_status, use_container_width=True)

# Tab 3: VPP(가상발전소) 운영 스케줄링 설정
with tab3:
    st.subheader("🔋 VPP 자원 연계 및 시간대별 운용 스케줄")
    
    hours = [f"{h:02d}:00" for h in range(24)]
    # 시뮬레이션용 스케줄 데이터
    solar_gen = [0,0,0,0,0,10,30,60,110,180,220,250,240,200,150,90,40,10,0,0,0,0,0,0]
    ess_charge = [-50,-50,-50,-50,-50,0,0,0,0,0,0,0,0,0,0,0,0,0,50,50,50,50,50,50]
    
    fig_vpp = go.Figure()
    fig_vpp.add_trace(go.Bar(x=hours, y=solar_gen, name='태양광 발전(kW)', marker_color='#2ecc71'))
    fig_vpp.add_trace(go.Bar(x=hours, y=ess_charge, name='ESS 충/방전(kW)', marker_color='#9b59b6'))
    
    fig_vpp.update_layout(
        title="24시간 VPP 유연자원 스케줄링 (경부하 충전 / 피크 방전)",
        barmode='relative',
        xaxis_title="시간",
        yaxis_title="전력량 (kW)"
    )
    st.plotly_chart(fig_vpp, use_container_width=True)

# Tab 4: KEPCO 요금 명세
with tab4:
    st.subheader("💰 KEPCO 3단계 차등 요금 명세")
    cat_usage = kepco_cost['usage_by_cat']
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🌙 경부하 (22시~08시)", f"{cat_usage.get('off_peak', 0.0):,.1f} kWh")
    c2.metric("☀️ 중간부하", f"{cat_usage.get('mid_peak', 0.0):,.1f} kWh")
    c3.metric("🔥 최대부하 (피크)", f"{cat_usage.get('on_peak', 0.0):,.1f} kWh")
    st.divider()
    
    pie_data = {
        '부하구분': ['경부하', '중간부하', '최대부하'],
        '사용량(kWh)': [cat_usage.get('off_peak', 0.0), cat_usage.get('mid_peak', 0.0), cat_usage.get('on_peak', 0.0)]
    }
    st.plotly_chart(px.pie(pie_data, names='부하구분', values='사용량(kWh)', title='시간대별 전력사용 비중'), use_container_width=True)

# Tab 5: 리포트 다운로드
with tab5:
    st.subheader("📄 진단 보고서 출력")
    html_report = generate_html_report(
        peak=peak_kw, peak_time=peak_info['peak_time'], total=total_kwh, cost_info=kepco_cost, threshold=threshold_kw
    )
    st.download_button("📥 HTML 통합 진단 리포트 다운로드", data=html_report, file_name="energy_report.html", mime="text/html")