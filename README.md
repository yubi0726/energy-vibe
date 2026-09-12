# ⚡ 산업단지 전력사용 분석기 (Energy-Vibe)

산업용 전력 데이터(CSV)를 기반으로 최대수요전력(Peak) 진단, KEPCO 계절·시간대별 3단계 차등 요금 계산, AI 운영 인사이트를 제공하는 **웹 기반 대시보드**입니다.

🌐 **실시간 서비스 주소:** [https://energy-vibe-analyzer.streamlit.app](https://energy-vibe-analyzer.streamlit.app)

---

## 🛠️ 주요 기능

- **📈 전력 사용량 인터랙티브 시각화:** Plotly 기반 시간대별 전력 추이 및 목표 피크 임계선 표시
- **💰 KEPCO 3단계 정밀 요금 엔진:** 한전 산업용(경부하, 중간부하, 최대부하) 차등 단가 산정 및 파이 차트 제공
- **💡 AI 에너지 운영 진단:** 피크 발생 시각 자동 분석을 통한 부하 이전 및 절감 가이드 제시
- **📁 사용자 데이터 분석:** 자체 전력 사용량 CSV 업로드 및 기본 샘플 데이터 다운로드 지원
- **📄 리포트 출력:** 분석 결과 및 요금 내역을 포함한 HTML 진단 보고서 다운로드

---

## 💻 기술 스택

- **Language:** Python 3.11+
- **Frontend / Framework:** Streamlit
- **Visualization:** Plotly, Pandas
- **Testing:** Pytest
- **Deployment:** Git / GitHub, Streamlit Community Cloud

---

## 🚀 로컬 실행 방법

```bash
# 1. 저장소 클론
git clone [https://github.com/yubi0726/energy-vibe.git](https://github.com/yubi0726/energy-vibe.git)
cd energy-vibe

# 2. 의존성 패키지 설치
pip install -r requirements.txt

# 3. Streamlit 앱 실행
streamlit run app.py