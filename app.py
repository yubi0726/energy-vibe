import streamlit as st
import pandas as pd
import plotly.express as px
from src.calculations import (
    clean_data,
    filter_by_time_range,
    calculate_peak_load,
    calculate_total_consumption,
    find_peak_info,
    check_peak_threshold,
    calculate_kepco_cost,
    generate_interactive_chart,
    generate_html_report
)

# 1. 페이지 설정 및 폰트 깨짐 방지 CSS
st.set_page_config(page_title="산업단지 전력사용 분석기", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ 산업단지 전력사용 분석기")

# 2. 사이드바 - 옵션 입력
st.sidebar.header("1. 분석 옵션")
start_hour, end_hour = st.sidebar.slider(
    "분석 시간대 선택 (시)",
    min_value=0, max_value=23, value=(0, 23)
)

threshold_kw = st.sidebar.number_input(
    "목표 피크 전력 임계값 (kW)",
    min_value=0.0, max_value=10000.0, value=450.0, step=10.0
)

st.sidebar.header("2. 요금 단가 설정")
base_rate = st.sidebar.number_input(
    "기본요금 단가 (원/kW)",
    min_value=0.0, value=8320.0, step=100.0
)

# 3. 데이터 로드 (기본 샘플 데이터)
@st.cache_data
def load_data():
    return pd.read_csv("data/sample_load.csv")

try:
    df_raw = load_data()
    df_clean = clean_data(df_raw)
    df_filtered = filter_by_time_range(df_clean, start_hour, end_hour)

    # 지표 계산
    peak_kw = calculate_peak_load(df_filtered)
    peak_info = find_peak_info(df_filtered)
    total_kwh = calculate_total_consumption(df_filtered)
    kepco_cost = calculate_kepco_cost(df_filtered, base_rate=base_rate)
    is_exceeded = check_peak_threshold(peak_kw, threshold_kw)

    # 경고 메시지
    if is_exceeded:
        st.error(f"⚠️ 경고: 선택 구간 피크전력({peak_kw:.1f} kW)이 목표 임계값({threshold_kw:.1f} kW)을 초과했습니다!")
    else:
        st.success(f"✅ 안정: 선택 구간 피크전력({peak_kw:.1f} kW)이 목표 범위 내에 있습니다.")

    # 상단 메트릭 카트
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("최대수요전력", f"{peak_kw:.1f} kW")
    col2.metric("피크 발생 시각", peak_info['peak_time'] if peak_info['peak_time'] else "-")
    col3.metric("총 전력 사용량", f"{total_kwh:,.1f} kWh")
    col4.metric("추정 총 전력요금", f"{int(kepco_cost['total_cost']):,} 원")

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📈 전력 사용량 추이", "💰 요금 분석 명세", "💾 데이터 및 보고서 다운로드", "❓ 사용 도움말"])

    with tab1:
        st.subheader("시간대별 전력 사용량 인터랙티브 차트")
        fig = generate_interactive_chart(df_filtered, threshold_kw)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("💰 KEPCO 산업용 계절·시간대별 요금 분석")
        cat_usage = kepco_cost['usage_by_cat']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🌙 경부하 (22시~08시)", f"{cat_usage.get('off_peak', 0.0):,.1f} kWh")
        c2.metric("☀️ 중간부하 (기타 시간)", f"{cat_usage.get('mid_peak', 0.0):,.1f} kWh")
        c3.metric("🔥 최대부하 (피크 시간)", f"{cat_usage.get('on_peak', 0.0):,.1f} kWh")
        
        st.divider()
        
        pie_data = {
            '부하구분': ['경부하', '중간부하', '최대부하'],
            '사용량(kWh)': [
                cat_usage.get('off_peak', 0.0),
                cat_usage.get('mid_peak', 0.0),
                cat_usage.get('on_peak', 0.0)
            ]
        }
        fig_pie = px.pie(
            pie_data, 
            names='부하구분', 
            values='사용량(kWh)',
            title='시간대별 전력 사용량 비중',
            color='부하구분',
            color_discrete_map={'경부하': '#2ecc71', '중간부하': '#f1c40f', '최대부하': '#e74c3c'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.subheader("리포트 및 데이터 다운로드")
        html_report = generate_html_report(
            peak=peak_kw,
            peak_time=peak_info['peak_time'],
            total=total_kwh,
            cost_info=kepco_cost,
            threshold=threshold_kw
        )
        st.download_button(
            label="📄 HTML 진단 보고서 다운로드",
            data=html_report,
            file_name="energy_analysis_report.html",
            mime="text/html"
        )

    with tab4:
        st.markdown("""
        ### 사용 도움말
        1. 왼쪽 사이드바에서 **분석 시간대**와 **목표 피크**를 조절할 수 있습니다.
        2. KEPCO 산업용 요금 체계(경부하/중간부하/최대부하)에 맞춰 정밀 계산됩니다.
        """)

except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")