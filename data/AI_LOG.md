# 프로젝트 진행 일지 (Final Report)

## 1일 차
- 개발 환경 구축 (Miniconda, VS Code) 및 기본 Streamlit 앱 작성 완료

## 2일 차
- `src/calculations.py` 로직 분리 (최대수요전력, 총 사용량 계산)
- `tests/test_calculations.py` 단위 테스트 작성 및 pytest 검증 완료

## 3일 차
- 데이터 전처리(`clean_data`) 및 시간대 필터링 기능 추가
- 사이드바 슬라이더 UI 적용 및 단위 테스트 확장

## 4일 차
- 피크 발생 시각 탐지 및 목표 임계값 초과 경고 알림 기능 추가
- 필터링된 데이터 CSV 다운로드 기능 구현

## 5일 차
- 요금 산정 알고리즘 구현 (`calculate_estimated_cost`)
- Streamlit 앱 UI 탭(Tabs) 구조 도입 및 요금 명세서 대시보드 구현

## 6일 차 (최종)
- HTML 보고서 자동 생성 기능 구현 (`generate_html_report`) 및 다운로드 연동
- 전체 모듈에 대한 단위 테스트 4종 최종 통과 (100% Passed)
- 프로젝트 개발 완료 및 최종 정리