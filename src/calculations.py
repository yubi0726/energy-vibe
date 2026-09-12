import pandas as pd
from typing import Dict, Any
import plotly.graph_objects as go

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 전처리: timestamp 파싱, 결측치 및 음수 전력 데이터 처리"""
    df = df.copy()
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if 'load_kw' in df.columns:
        df['load_kw'] = df['load_kw'].apply(lambda x: max(0.0, float(x)) if pd.notnull(x) else x)
        df['load_kw'] = df['load_kw'].ffill().bfill()
        
    return df

def filter_by_time_range(df: pd.DataFrame, start_hour: int, end_hour: int) -> pd.DataFrame:
    """특정 시간대 데이터 필터링"""
    if 'timestamp' not in df.columns or df.empty:
        return df
    
    hours = df['timestamp'].dt.hour
    return df[(hours >= start_hour) & (hours <= end_hour)]

def calculate_peak_load(df: pd.DataFrame) -> float:
    """최대수요전력(kW) 계산"""
    if df.empty or 'load_kw' not in df.columns:
        return 0.0
    return float(df['load_kw'].max())

def calculate_total_consumption(df: pd.DataFrame) -> float:
    """총 사용량(kWh) 계산"""
    if df.empty or 'load_kw' not in df.columns:
        return 0.0
    return float(df['load_kw'].sum())

def find_peak_info(df: pd.DataFrame) -> Dict[str, Any]:
    """최대수요전력 발생 시각과 값 추출"""
    if df.empty or 'load_kw' not in df.columns:
        return {'peak_kw': 0.0, 'peak_time': None}
    
    max_idx = df['load_kw'].idxmax()
    peak_row = df.loc[max_idx]
    return {
        'peak_kw': float(peak_row['load_kw']),
        'peak_time': str(peak_row['timestamp'])
    }

def check_peak_threshold(peak_kw: float, threshold_kw: float) -> bool:
    """설정 목표 피크 초과 여부 확인"""
    return peak_kw > threshold_kw

def calculate_estimated_cost(df: pd.DataFrame, base_rate_per_kw: float = 8320, kwh_rate: float = 120.5) -> Dict[str, float]:
    """추정 전력 요금 계산"""
    if df.empty or 'load_kw' not in df.columns:
        return {'base_cost': 0.0, 'usage_cost': 0.0, 'total_cost': 0.0}

    peak_kw = calculate_peak_load(df)
    total_kwh = calculate_total_consumption(df)

    base_cost = peak_kw * base_rate_per_kw
    usage_cost = total_kwh * kwh_rate
    total_cost = base_cost + usage_cost

    return {
        'base_cost': base_cost,
        'usage_cost': usage_cost,
        'total_cost': total_cost
    }

def generate_interactive_chart(df: pd.DataFrame, threshold_kw: float) -> go.Figure:
    """Plotly 기반 인터랙티브 전력 사용량 그래프 생성"""
    fig = go.Figure()
    
    # 기본 전력사용량 선 그래프
    fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['load_kw'],
        mode='lines+markers',
        name='전력 사용량 (kW)',
        line=dict(color='#1f77b4', width=2),
        hovertemplate='<b>시각:</b> %{x}<br><b>전력량:</b> %{y:.1f} kW<extra></extra>'
    ))

    # 목표 임계값 가로선 표시
    fig.add_hline(
        y=threshold_kw, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"목표 피크 ({threshold_kw} kW)", 
        annotation_position="top right"
    )

    fig.update_layout(
        title="시간대별 전력 사용량 및 목표 피크 임계선",
        xaxis_title="시각",
        yaxis_title="전력 (kW)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def generate_html_report(peak: float, peak_time: str, total: float, cost_info: Dict[str, float], threshold: float) -> str:
    """HTML 보고서 생성"""
    is_exceeded = peak > threshold
    status_text = "경고 (목표 초과)" if is_exceeded else "안정 (목표 준수)"
    status_color = "#d9534f" if is_exceeded else "#5cb85c"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>전력사용 분석 보고서</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; line-height: 1.6; color: #333; }}
            h1 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 8px; }}
            .status {{ font-weight: bold; color: {status_color}; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>⚡ 산업단지 전력사용 분석 보고서</h1>
        <p><strong>진단 결과:</strong> <span class="status">{status_text}</span></p>
        <h2>1. 주요 지표</h2>
        <table>
            <tr><th>최대수요전력 (Peak)</th><td>{peak:.1f} kW</td></tr>
            <tr><th>피크 발생 시각</th><td>{peak_time if peak_time else '-'}</td></tr>
            <tr><th>목표 피크 임계값</th><td>{threshold:.1f} kW</td></tr>
            <tr><th>총 사용량</th><td>{total:,.1f} kWh</td></tr>
        </table>
        <h2>2. 요금 산정 내역</h2>
        <table>
            <tr><th>기본 요금</th><td>{int(cost_info['base_cost']):,} 원</td></tr>
            <tr><th>사용량 요금</th><td>{int(cost_info['usage_cost']):,} 원</td></tr>
            <tr><th><strong>합계 추정 요금</strong></th><td><strong>{int(cost_info['total_cost']):,} 원</strong></td></tr>
        </table>
    </body>
    </html>
    """
def calculate_kepco_cost(df, base_rate=8320, summer_rates=None):
    """
    KEPCO 산업용(을) 기준 시간대별 차등 요금 계산 로직
    """
    if summer_rates is None:
        # 기본 설정 단가 (원/kWh) - 예시 기준
        summer_rates = {
            'off_peak': 65.2,   # 경부하
            'mid_peak': 109.0,  # 중간부하
            'on_peak': 191.1    # 최대부하
        }

    # 시간대 분류 함수
    def get_time_category(hour):
        if 22 <= hour or hour < 8:
            return 'off_peak'
        elif hour in [11, 13, 14, 15, 16]:
            return 'on_peak'
        else:
            return 'mid_peak'

    df_calc = df.copy()
    df_calc['hour'] = df_calc['datetime'].dt.hour
    df_calc['category'] = df_calc['hour'].apply(get_time_category)
    
    # 시간대별 사용량 합계
    category_usage = df_calc.groupby('category')['power_usage'].sum().to_dict()
    
    # 요금 계산
    off_cost = category_usage.get('off_peak', 0) * summer_rates['off_peak']
    mid_cost = category_usage.get('mid_peak', 0) * summer_rates['mid_peak']
    on_cost = category_usage.get('on_peak', 0) * summer_rates['on_peak']
    
    total_usage_cost = off_cost + mid_cost + on_cost
    
    return {
        'base_cost': base_rate,
        'usage_cost': total_usage_cost,
        'total_cost': base_rate + total_usage_cost,
        'category_usage': category_usage
    }
def calculate_kepco_cost(df, base_rate=8320, rates=None):
    """
    한전 산업용 3단계 시간대별(경부하, 중간부하, 최대부하) 요금 계산
    """
    if rates is None:
        rates = {'off_peak': 65.2, 'mid_peak': 109.0, 'on_peak': 191.1}

    df_calc = df.copy()
    df_calc['hour'] = df_calc['datetime'].dt.hour
    
    # 시간대 분류 (경부하: 22-08시, 최대부하: 11시,13-16시, 중간부하: 기타)
    def get_category(h):
        if 22 <= h or h < 8:
            return 'off_peak'
        elif h in [11, 13, 14, 15, 16]:
            return 'on_peak'
        else:
            return 'mid_peak'

    df_calc['category'] = df_calc['hour'].apply(get_category)
    usage_by_cat = df_calc.groupby('category')['power_usage'].sum().to_dict()

    off_cost = usage_by_cat.get('off_peak', 0) * rates['off_peak']
    mid_cost = usage_by_cat.get('mid_peak', 0) * rates['mid_peak']
    on_cost = usage_by_cat.get('on_peak', 0) * rates['on_peak']

    usage_cost = off_cost + mid_cost + on_cost

    return {
        'base_cost': base_rate,
        'usage_cost': usage_cost,
        'total_cost': base_rate + usage_cost,
        'usage_by_cat': usage_by_cat
    }