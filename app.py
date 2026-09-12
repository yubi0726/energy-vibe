import streamlit as st
import pandas as pd
from src.calculations import (
    clean_data, 
    filter_by_time_range, 
    calculate_peak_load, 
    calculate_total_consumption,
    find_peak_info,
    check_peak_threshold,
    calculate_estimated_cost,
    generate_interactive_chart,
    generate_html_report
)

st.set_page_config(page_title="산업단지 전력사용 분석기", layout="wide")

st.title('⚡ 산업단지 전력사용 및 요금 분석기')

# 사이드바 설정
st.sidebar.header('1. 분석 옵션')

file = st.file_uploader('CSV 파일 업로드', type=['csv'])

if file is not None:
    try:
        raw_df = pd.read_csv(file)
        
        # 컬럼 이름 검증
        if 'timestamp' not in raw_df.columns or 'load_kw' not in raw_df.columns:
            st.error("❌ 올바르지 않은 CSV 형식입니다. 'timestamp'와 'load_kw' 컬럼이 반드시 포함되어야 합니다.")
            st.stop()
            
        df = clean_data(raw_df)

        # 시간대 필터 슬라이더
        start_hour, end_hour = st.sidebar.slider(
            '분석 시간대 선택 (시)',
            min_value=0, max_value=23, value=(0, 23)
        )

        # 목표 피크 전력 입력
        target_threshold = st.sidebar.number_input(
            '목표 피크 전력 임계값 (kW)', 
            min_value=0.0, 
            value=450.0, 
            step=10.0
        )

        # 요금 단가 설정
        st.sidebar.header('2. 요금 단가 설정')
        base_rate = st.sidebar.number_input('기본요금 단가 (원/kW)', value=8320, step=100)
        kwh_rate = st.sidebar.number_input('사용량 단가 (원/kWh)', value=120.5, step=1.0)

        filtered_df = filter_by_time_range(df, start_hour, end_hour)

        # 주요 지표 및 피크 정보 계산
        peak = calculate_peak_load(filtered_df)
        total = calculate_total_consumption(filtered_df)
        peak_info = find_peak_info(filtered_df)
        cost_info = calculate_estimated_cost(filtered_df, base_rate, kwh_rate)

        # 피크 경고 메시지 표시
        if check_peak_threshold(peak, target_threshold):
            st.error(f"⚠️ 경고: 선택 구간 피크전력({peak:.1f} kW)이 목표 임계값({target_threshold:.1f} kW)을 초과했습니다!")
        else:
            st.success(f"✅ 안정: 선택 구간 피크전력이 목표 임계값({target_threshold:.1f} kW) 이하입니다.")

        # 주요 지표 출력 (4 컬럼 레이아웃)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric('최대수요전력', f"{peak:.1f} kW")
        col2.metric('피크 발생 시각', str(peak_info['peak_time']) if peak_info['peak_time'] else '-')
        col3.metric('총 전력 사용량', f"{total:,.1f} kWh")
        col4.metric('추정 총 전력요금', f"{int(cost_info['total_cost']):,} 원")

        # 탭을 이용한 정보 구성 (4개 탭)
        tab1, tab2, tab3, tab4 = st.tabs(["📈 전력 사용량 추이", "💰 요금 분석 명세", "📥 데이터 및 보고서 다운로드", "❓ 사용 도움말"])

        with tab1:
            st.subheader('시간대별 전력 사용량 인터랙티브 차트')
            fig = generate_interactive_chart(filtered_df, target_threshold)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
    st.subheader("💰 KEPCO 산업용 계절·시간대별 요금 분석")
    
    # 1. KEPCO 3단계 요금 계산 함수 호출
    kepco_result = calculate_kepco_cost(df_filtered, base_rate=base_rate, rates={'off_peak': 65.2, 'mid_peak': 109.0, 'on_peak': 191.1})
    cat_usage = kepco_result['usage_by_cat']
    
    # 2. 부하 구간별 지표 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🌙 경부하 (22시~08시)", f"{cat_usage.get('off_peak', 0):,.1f} kWh")
    with col2:
        st.metric("☀️ 중간부하 (기타 시간)", f"{cat_usage.get('mid_peak', 0):,.1f} kWh")
    with col3:
        st.metric("🔥 최대부하 (피크 시간)", f"{cat_usage.get('on_peak', 0):,.1f} kWh")
        
    st.divider()
    
    # 3. 부하 구분별 비중 파이 차트 시각화
    import plotly.express as px
    
    pie_data = {
        '부하구분': ['경부하', '중간부하', '최대부하'],
        '사용량(kWh)': [
            cat_usage.get('off_peak', 0),
            cat_usage.get('mid_peak', 0),
            cat_usage.get('on_peak', 0)
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
            st.subheader('📥 보고서 및 정제 데이터 다운로드')
            html_report = generate_html_report(peak, str(peak_info['peak_time']), total, cost_info, target_threshold)
            
            col_down1, col_down2 = st.columns(2)
            with col_down1:
                st.download_button(
                    label="📄 HTML 분석 보고서 다운로드",
                    data=html_report,
                    file_name="energy_analysis_report.html",
                    mime="text/html"
                )
            with col_down2:
                csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📊 필터링된 CSV 데이터 다운로드",
                    data=csv_data,
                    file_name="filtered_energy_data.csv",
                    mime="text/csv"
                )

            st.divider()
            st.subheader('상세 데이터 보기')
            st.dataframe(filtered_df)

        with tab4:
            st.subheader('💡 사용 가이드')
            st.markdown("""
            1. **데이터 준비:** `timestamp` 및 `load_kw` 헤더를 포함하는 CSV 파일을 준비해 업로드합니다.
            2. **시간대 필터링:** 사이드바의 슬라이더를 이용해 주간/야간 등 원하는 분석 구간을 선택합니다.
            3. **피크 전력 관리:** 사업장의 목표 계약 전력(kW)을 설정하면 초과 여부를 자동 감지해 알려줍니다.
            4. **보고서 출력:** 3번 탭에서 분석 결과를 HTML 및 CSV 형태로 즉시 다운로드할 수 있습니다.
            """)
    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")