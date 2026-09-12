import pandas as pd
from src.calculations import (
    clean_data, 
    filter_by_time_range, 
    calculate_peak_load, 
    calculate_total_consumption,
    find_peak_info,
    check_peak_threshold,
    calculate_estimated_cost,
    generate_html_report
)

def test_clean_data_handles_negative_values():
    data = {'timestamp': ['2026-09-01 00:00'], 'load_kw': [-10.0]}
    df = pd.DataFrame(data)
    cleaned_df = clean_data(df)
    assert cleaned_df['load_kw'].iloc[0] == 0.0

def test_filter_by_time_range():
    data = {
        'timestamp': ['2026-09-01 08:00', '2026-09-01 12:00', '2026-09-01 20:00'],
        'load_kw': [100.0, 200.0, 150.0]
    }
    df = clean_data(pd.DataFrame(data))
    filtered = filter_by_time_range(df, 9, 18)
    assert len(filtered) == 1
    assert filtered['load_kw'].iloc[0] == 200.0

def test_calculate_estimated_cost():
    data = {
        'timestamp': ['2026-09-01 10:00', '2026-09-01 14:00'],
        'load_kw': [100.0, 200.0]
    }
    df = clean_data(pd.DataFrame(data))
    cost = calculate_estimated_cost(df, base_rate_per_kw=1000, kwh_rate=100)
    assert cost['base_cost'] == 200000.0
    assert cost['usage_cost'] == 30000.0
    assert cost['total_cost'] == 230000.0

def test_generate_html_report():
    cost_info = {'base_cost': 1000.0, 'usage_cost': 500.0, 'total_cost': 1500.0}
    report = generate_html_report(500.0, '2026-09-01 14:00', 1000.0, cost_info, 400.0)
    assert '산업단지 전력사용 분석 보고서' in report
    assert '경고 (목표 초과)' in report