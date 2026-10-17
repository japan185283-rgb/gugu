import streamlit as st

st.set_page_config(page_title="VIP 투자 수익 분석기", layout="wide")

st.title("📊 VIP 맞춤형 부동산 자금/수익 분석기")
st.markdown("매매가, 대출, 세금을 종합하여 **실제 들어가는 현금**과 **월 유지비(또는 순수익)**를 즉석에서 계산해 브리핑합니다.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 💰 한국어 금액 변환 도우미 함수 (15550 -> 1억 5,550만 원)
# -----------------------------------------------------------------------------
def kor_money(man_won):
    if man_won <= 0:
        return "0원"
    uk = int(man_won // 10000)
    man = int(man_won % 10000)
    
    if uk > 0 and man > 0:
        return f"( {uk}억 {man:,}만 원 )"
    elif uk > 0:
        return f"( {uk}억 원 )"
    else:
        return f"( {man:,}만 원 )"

# -----------------------------------------------------------------------------
# 좌측 사이드바 메뉴 (깔끔하게 이름 변경)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📂 브리핑 물건 선택")
    property_menu = st.radio("물건 종류를 선택하세요", ["🏢 상가주택", "🏭 공장/창고", "🌄 토지", "🏠 아파트"])


# ==========================================
# 1. 상가주택 (수익형 브리핑)
# ==========================================
if property_menu == "🏢 상가주택":
    st.subheader("🏢 상가주택 매수 자금 및 수익률 브리핑")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 투자 및 대출 조건")
        price = st.number_input("매매가 (만원)", value=100000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(price)}</span>**", unsafe_allow_html=True)
        
        loan_rate = st.number_input("예상 대출 한도 (%)", value=60.0, step=5.0)
        interest_rate = st.number_input("연 대출 금리 (%)", value=4.5, step=0.1)
        acq_tax_rate = st.number_input("취득세 및 부대비용 (%)", value=4.6, step=0.1)
        
    with col2:
        st.markdown("#### 🏠 임대 수익 조건")
        deposit = st.number_input("총 임대 보증금 (만원)", value=10000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(deposit)}</span>**", unsafe_allow_html=True)
        
        monthly_rent = st.number_input("총 월세 (만원)", value=350, step=10)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(monthly_rent)}</span>**", unsafe_allow_html=True)

    loan_amount = price * (loan_rate / 100)
    tax_amount = price * (acq_tax_rate / 100)
    real_investment = price - loan_amount - deposit + tax_amount
    monthly_interest = (loan_amount * (interest_rate / 100)) / 12
    net_monthly_income = monthly_rent - monthly_interest
    annual_yield = (net_monthly_income * 12) / real_investment * 100 if real_investment > 0 else 0

    st.markdown("---")
    st.subheader("💡 브리핑 결과 요약")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("필요한 현금 (실투자금)", f"{real_investment:,.0f} 만원")
    c2.metric("은행 이자 뺀 [월 순수익]", f"{net_monthly_income:,.0f} 만원")
    c3.metric("최종 연 수익률", f"{annual_yield:.2f} %")

    st.markdown("#### 📑 세부 자금 흐름표")
    st.info(f"""
    * **매매 대금:** {price:,.0f} 만원 {kor_money(price)}
    * **(+) 취득세 등 부대비용:** {tax_amount:,.0f} 만원
    * **(-) 은행 대출금:** {loan_amount:,.0f} 만원 (금리 {interest_rate}%)
    * **(-) 회수 보증금:** {deposit:,.0f} 만원
    * **= 최종 초기 투자금:** **{real_investment:,.0f} 만원 {kor_money(real_investment)}**
    """)

# ==========================================
# 2. 공장/창고 (실사용 및 임대 겸용)
# ==========================================
elif property_menu == "🏭 공장/창고":
    st.subheader("🏭 공장/창고 자금 조달 및 운영 브리핑")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 매수 및 대출 조건")
        price = st.number_input("매매가 (만원)", value=200000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(price)}</span>**", unsafe_allow_html=True)
        
        loan_rate = st.number_input("공장 시설/운전자금 대출 한도 (%)", value=80.0, step=5.0)
        interest_rate = st.number_input("연 대출 금리 (%)", value=4.0, step=0.1)
        acq_tax_rate = st.number_input("취득세 등 (%)", value=4.6, step=0.1)
        
    with col2:
        st.markdown("#### 🏭 임대 조건 (임대 시)")
        deposit = st.number_input("임대 보증금 (만원)", value=15000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(deposit)}</span>**", unsafe_allow_html=True)
        
        monthly_rent = st.number_input("월세 (만원)", value=800, step=10)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(monthly_rent)}</span>**", unsafe_allow_html=True)

    loan_amount = price * (loan_rate / 100)
    tax_amount = price * (acq_tax_rate / 100)
    real_investment_use = price - loan_amount + tax_amount  # 직접 쓸 때 (보증금 차감 안 함)
    real_investment_rent = price - loan_amount - deposit + tax_amount # 임대 줄 때 (보증금 회수)
    
    monthly_interest = (loan_amount * (interest_rate / 100)) / 12
    net_monthly_income = monthly_rent - monthly_interest
    annual_yield = (net_monthly_income * 12) / real_investment_rent * 100 if real_investment_rent > 0 else 0

    st.markdown("---")
    st.subheader("💡 브리핑 결과 요약")
    
    t1, t2 = st.tabs(["대표님 직접 사용 시", "임대 수익 목적 시"])
    
    with t1:
        c1, c2 = st.columns(2)
        c1.metric("초기 필요 자금 (대출 제외)", f"{real_investment_use:,.0f} 만원")
        c2.metric("매월 부담해야 할 이자", f"{monthly_interest:,.0f} 만원")
        st.info(f"은행에서 **{kor_money(loan_amount)}**을 대출받으실 경우, 취득세를 포함하여 초기에 현금 **{kor_money(real_investment_use)}**이 필요하며, 매달 은행에 **{monthly_interest:,.0f}만원**의 이자를 납부하셔야 합니다.")
        
    with t2:
        c1, c2, c3 = st.columns(3)
        c1.metric("실투자금 (보증금 회수 후)", f"{real_investment_rent:,.0f} 만원")
        c2.metric("이자 빼고 남는 월 순수익", f"{net_monthly_income:,.0f} 만원")
        c3.metric("최종 연 수익률", f"{annual_yield:.2f} %")
        st.info(f"임차인에게 보증금 **{kor_money(deposit)}**을 받으시면 실제 투입되는 현금은 **{kor_money(real_investment_rent)}**으로 줄어들며, 매달 이자를 내고도 **{net_monthly_income:,.0f}만원**이 순수익으로 남습니다.")

# ==========================================
# 3. 토지 (평단가 및 자금 브리핑)
# ==========================================
elif property_menu == "🌄 토지":
    st.subheader("🌄 토지 매수 자금 및 평단가 분석")
    
    col1, col2 = st.columns(2)
    with col1:
        area_py = st.number_input("토지 면적 (평)", value=200.0, step=10.0)
        price = st.number_input("총 매매가 (만원)", value=60000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(price)}</span>**", unsafe_allow_html=True)
    with col2:
        loan_rate = st.number_input("예상 대출 한도 (%)", value=50.0, step=5.0)
        interest_rate = st.number_input("연 대출 금리 (%)", value=4.8, step=0.1)
        acq_tax_rate = st.number_input("취득세율 (%)", value=4.6, step=0.1) # 농지 등 제외 일반 토지 4.6%

    price_per_py = price / area_py if area_py > 0 else 0
    loan_amount = price * (loan_rate / 100)
    tax_amount = price * (acq_tax_rate / 100)
    real_investment = price - loan_amount + tax_amount
    monthly_interest = (loan_amount * (interest_rate / 100)) / 12

    st.markdown("---")
    st.subheader("💡 브리핑 결과 요약")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("3.3㎡ (1평) 당 단가", f"{price_per_py:,.0f} 만원")
    c2.metric("필요한 현금 (실투자금)", f"{real_investment:,.0f} 만원")
    c3.metric("매월 유지비 (대출 이자)", f"{monthly_interest:,.0f} 만원")

    st.info(f"""
    * 해당 토지의 평당 가격은 **{price_per_py:,.0f}만원** 입니다.
    * 대출을 {loan_rate}% 실행할 경우, 등기비용을 포함해 당장 **{kor_money(real_investment)}**의 현금이 필요합니다.
    * 땅값이 오를 때까지 보유하시는 동안 매달 은행에 **{monthly_interest:,.0f}만원**의 이자가 발생합니다.
    """)

# ==========================================
# 4. 아파트 (실매수자 자금 및 이자 브리핑)
# ==========================================
elif property_menu == "🏠 아파트":
    st.subheader("🏠 아파트 실거주/매수 자금 브리핑")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💰 매수 조건")
        price = st.number_input("아파트 매매가 (만원)", value=50000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(price)}</span>**", unsafe_allow_html=True)
        
        acq_tax_rate = st.number_input("취득세 및 등기비용 (%)", value=1.1, step=0.1)
        extra_cost = st.number_input("인테리어/복비 등 기타 여유자금 (만원)", value=2000, step=100)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(extra_cost)}</span>**", unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🏦 주택담보대출 요건")
        loan_amount = st.number_input("받을 대출 금액 (만원)", value=30000, step=1000)
        st.markdown(f"**<span style='color:#0052cc'>{kor_money(loan_amount)}</span>**", unsafe_allow_html=True)
        
        interest_rate = st.number_input("예상 연 금리 (%)", value=3.8, step=0.1)

    tax_amount = price * (acq_tax_rate / 100)
    total_cost = price + tax_amount + extra_cost
    real_investment = total_cost - loan_amount
    monthly_interest = (loan_amount * (interest_rate / 100)) / 12

    st.markdown("---")
    st.subheader("💡 입주 자금 브리핑 요약")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("총 매수 비용 (세금/인테리어 포함)", f"{total_cost:,.0f} 만원")
    c2.metric("내 주머니에서 나갈 진짜 현금", f"{real_investment:,.0f} 만원")
    c3.metric("매월 나갈 대출 이자", f"{monthly_interest:,.0f} 만원")

    st.markdown("#### 📑 자금 조달 계획표")
    st.info(f"""
    * **아파트 집값:** {kor_money(price)}
    * **(+) 취득세 및 부대비용:** {tax_amount:,.0f} 만원
    * **(+) 인테리어 등 여유자금:** {extra_cost:,.0f} 만원
    * **(-) 주택담보대출 실행:** {kor_money(loan_amount)}
    * **= 입주 시 총 필요한 내 돈:** **{kor_money(real_investment)}**
    
    (※ 위 계산은 순수 이자 비용만 나타낸 것이며, 원리금 균등 상환 시 매월 납입액은 더 높아집니다.)
    """)
