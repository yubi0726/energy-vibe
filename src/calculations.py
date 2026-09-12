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
    """단순 추정 전력 요금 계산"""
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


def calculate_kepco_cost(df: pd.DataFrame, base_rate: float = 8320, rates: Dict[str, float] = None) -> Dict[str, Any]:
    """
    한전 산업용 3단계 시간대별(경부하, 중간부하, 최대부하) 요금 계산
    """
    if df.empty or 'load_kw' not in df.columns:
        return {
            'base_cost': 0.0,
            'usage_cost': 0.0,
            'total_cost': 0.0,
            'usage_by_cat': {'off_peak': 0.0, 'mid_peak': 0.0, 'on_peak': 0.0}
        }

    if rates is None:
        rates = {'off_peak': 65.2, 'mid_peak': 109.0, 'on_peak': 191.1}

    df_calc = df.copy()
    
    # timestamp컬럼 이름을 기준으로 시간 추출 (안전한 컬럼 대응)
    time_col = 'timestamp' if 'timestamp' in df_calc.columns else 'datetime'
    df_calc['hour'] = pd.to_datetime(df_calc[time_col]).dt.hour
    
    # 시간대 분류 (경부하: 22-08시, 최대부하: 11시, 13-16시, 중간부하: 기타)
    def get_category(h):
        if 22 <= h or h < 8:
            return 'off_peak'
        elif h in [11, 13, 14, 15, 16]:
            return 'on_peak'
        else:
            return 'mid_peak'

    df_calc['category'] = df_calc['hour'].apply(get_category)
    usage_by_cat = df_calc.groupby('category')['load_kw'].sum().to_dict()

    peak_kw = calculate_peak_load(df)
    base_cost = peak_kw * base_rate

    off_cost = usage_by_cat.get('off_peak', 0.0) * rates['off_peak']
    mid_cost = usage_by_cat.get('mid_peak', 0.0) * rates['mid_peak']
    on_cost = usage_by_cat.get('on_peak', 0.0) * rates['on_peak']

    usage_cost = off_cost + mid_cost + on_cost

    return {
        'base_cost': base_cost,
        'usage_cost': usage_cost,
        'total_cost': base_cost + usage_cost,
        'usage_by_cat': usage_by_cat
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


def generate_html_report(peak: float, peak_time: str, total: float, cost_info: Dict[str, Any], threshold: float) -> str:
    """3단계 요금 내역을 포함한 HTML 보고서 생성"""
    is_exceeded = peak > threshold
    status_text = "경고 (목표 초과)" if is_exceeded else "안정 (목표 준수)"
    status_color = "#d9534f" if is_exceeded else "#5cb85c"

    cat_usage = cost_info.get('usage_by_cat', {})
    off_u = cat_usage.get('off_peak', 0.0)
    mid_u = cat_usage.get('mid_peak', 0.0)
    on_u = cat_usage.get('on_peak', 0.0)

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
        
        <h2>2. 시간대별 사용량 구분</h2>
        <table>
            <tr><th>경부하 사용량 (22시~08시)</th><td>{off_u:,.1f} kWh</td></tr>
            <tr><th>중간부하 사용량</th><td>{mid_u:,.1f} kWh</td></tr>
            <tr><th>최대부하 사용량 (피크시간)</th><td>{on_u:,.1f} kWh</td></tr>
        </table>

        <h2>3. 요금 산정 내역</h2>
        <table>
            <tr><th>기본 요금</th><td>{int(cost_info.get('base_cost', 0)):,} 원</td></tr>
            <tr><th>전력량 요금 (합계)</th><td>{int(cost_info.get('usage_cost', 0)):,} 원</td></tr>
            <tr><th><strong>합계 추정 요금</strong></th><td><strong>{int(cost_info.get('total_cost', 0)):,} 원</strong></td></tr>
        </table>
    </body>
    </html>
    """
def generate_energy_insights(peak_time: str, is_exceeded: bool) -> str:
    """피크 발생 시각 및 초과 여부를 기반으로 절감 권장사항 생성"""
    if not peak_time:
        return "분석할 전력 사용 데이터가 충분하지 않습니다."

    try:
        hour = pd.to_datetime(peak_time).hour
    except Exception:
        return "피크 시각 형식이 올바르지 않습니다."

    # 최대부하 시간대 (11시, 13~16시)
    if hour in [11, 13, 14, 15, 16]:
        time_msg = "🔥 현재 최대부하(피크) 시간대에 피크전력이 발생했습니다."
        action_msg = "해당 시간대의 대형 설비 가동을 경부하(22시~08시) 또는 중간부하 시간대로 이전하면 기본요금 및 전력량 요금을 대폭 절감할 수 있습니다."
    elif 22 <= hour or hour < 8:
        time_msg = "🌙 경부하 시간대에 피크전력이 발생했습니다."
        action_msg = "단가가 가장 저렴한 구간에 사용량이 집중되어 있어 요금 효율이 양호합니다."
    else:
        time_msg = "☀️ 중간부하 시간대에 피크전력이 발생했습니다."
        action_msg = "최대부하 시간대로 전력 사용이 쏠리지 않도록 피크 제어장치를점검하세요."

    if is_exceeded:
        warning_msg = " ⚠️ 목표 피크를 초과하였으므로 계약전력 증설 또는 피크 컷(Peak Cut) 에너지 저장장치(ESS) 도입을 검토하세요."
    else:
        warning_msg = " ✅ 목표 피크 범위 내에서 안정적으로 관리되고 있습니다."

    return f"{time_msg} {action_msg}{warning_msg}"