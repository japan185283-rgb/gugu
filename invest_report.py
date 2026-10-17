import streamlit as st

st.set_page_config(page_title="VIP 투자 수익 분석기", layout="wide")

st.title("📊 VIP 고객 맞춤형 투자 수익 분석기")
st.markdown("매매가, 대출, 세금을 종합하여 **실제 들어가는 돈(실투자금)**과 **월 순수익**을 즉석에서 계산해 브리핑합니다.")
st.markdown("---")

# 좌측 사이드바 메뉴 (업종별 페이지 이동)
with st.sidebar:
    st.header("📂 브리핑 물건 선택")
    property_menu = st.radio("물건 종류를 선택하세요", ["🏢 상가주택 (수익형)", "🏭 공장/창고", "🌄 토지 (차익형)", "🏠 아파트 (갭투자)"])

# ==========================================
# 1. 상가주택 (수익형 부동산 브리핑)
# ==========================================
if property_menu == "🏢 상가주택 (수익형)":
    st.subheader("🏢 상가주택 투자 수익률 브리핑")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 투자 및 대출 조건")
        price = st.number_input("매매가 (만원)", value=100000, step=1000) # 기본 10억
        loan_rate = st.number_input("예상 대출 한도 (%)", value=60, step=10) # 60% 대출
        interest_rate = st.number_input("연 대출 금리 (%)", value=4.5, step=0.1)
        acq_tax_rate = st.number_input("취득세 및 부대비용 (%)", value=4.6, step=0.1) # 상가 4.6%
        
    with col2:
        st.markdown("#### 🏠 임대 수익 조건")
        deposit = st.number_input("총 임대 보증금 (만원)", value=10000, step=1000)
        monthly_rent = st.number_input("총 월세 (만원)", value=350, step=10)

    # 계산 로직
    loan_amount = price * (loan_rate / 100)
    tax_amount = price * (acq_tax_rate / 100)
    
    # 실투자금 = 매매가 - 대출금 - 보증금 + 취득세
    real_investment = price - loan_amount - deposit + tax_amount
    
    # 월 이자 및 순수익
    monthly_interest = (loan_amount * (interest_rate / 100)) / 12
    net_monthly_income = monthly_rent - monthly_interest
    
    # 연 수익률 = (월 순수익 * 12) / 실투자금
    annual_yield = 0
    if real_investment > 0:
        annual_yield = (net_monthly_income * 12) / real_investment * 100

    st.markdown("---")
    st.subheader("💡 브리핑 결과 요약")
    
    # 큼지막한 핵심 데이터 출력 (손님 시선 집중용)
    c1, c2, c3 = st.columns(3)
    c1.metric("필요한 현금 (실투자금)", f"{real_investment:,.0f} 만원")
    c2.metric("은행 이자 뺀 [월 순수익]", f"{net_monthly_income:,.0f} 만원")
    c3.metric("최종 연 수익률", f"{annual_yield:.2f} %")

    # 표 형태의 상세 브리핑 (SNS 캡처 화면과 유사한 구조)
    st.markdown("#### 📑 세부 자금 흐름표")
    st.info(f"""
    * **매매 대금:** {price:,.0f} 만원
    * **(-) 은행 대출금:** {loan_amount:,.0f} 만원 (금리 {interest_rate}%)
    * **(-) 회수 보증금:** {deposit:,.0f} 만원
    * **(+) 취득세 등 부대비용:** {tax_amount:,.0f} 만원
    * **= 최종 초기 투자금:** **{real_investment:,.0f} 만원**
    """)

# ==========================================
# 2. 아파트 (갭투자 브리핑)
# ==========================================
elif property_menu == "🏠 아파트 (갭투자)":
    st.subheader("🏠 아파트 갭투자 및 차익 분석")
    
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("매매가 (만원)", value=50000, step=1000)
        jeonse = st.number_input("전세가 (보증금) (만원)", value=35000, step=1000)
    with col2:
        acq_tax_rate = st.number_input("취득세율 (다주택 중과 주의) (%)", value=1.1, step=0.1)
        expected_sale = st.number_input("2년 뒤 예상 매도가 (만원)", value=60000, step=1000)

    gap_investment = price - jeonse + (price * (acq_tax_rate / 100))
    expected_profit = expected_sale - price
    roi = (expected_profit / gap_investment) * 100 if gap_investment > 0 else 0

    st.markdown("---")
    st.subheader("💡 갭투자 브리핑 요약")
    c1, c2, c3 = st.columns(3)
    c1.metric("실제 필요한 갭 (취득세 포함)", f"{gap_investment:,.0f} 만원")
    c2.metric("예상 시세 차익", f"{expected_profit:,.0f} 만원")
    c3.metric("투자 대비 수익률(ROI)", f"{roi:.1f} %")

# 다른 메뉴들은 추후 뼈대를 덧붙이면 됩니다.
elif property_menu == "🏭 공장/창고":
    st.info("공장 및 창고 브리핑 화면 (기업 대출 및 시설 감가상각 로직 추가 예정)")
elif property_menu == "🌄 토지 (차익형)":
    st.info("토지 브리핑 화면 (개발부담금 및 보유 기간별 양도소득세 로직 추가 예정)")
