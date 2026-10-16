import streamlit as st
import google.generativeai as genai

# 1. 화면 기본 설정
st.set_page_config(page_title="베테랑 중개사 AI 블로그 작성기", layout="centered")

st.title("✍️ 베테랑 공인중개사 AI 블로그 자동 생성기")
st.markdown("네이버 SEO 로직에 최적화된, 법적 전문성이 돋보이는 신뢰감 있는 블로그 원고를 1분 만에 작성합니다.")
st.markdown("---")

# 2. 사이드바: API 키 입력란 (수동 입력 유지)
with st.sidebar:
    st.header("🔑 AI 설정")
    st.markdown("구글 AI 스튜디오에서 발급받은 Gemini API 키를 입력하세요.")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.info("💡 **네이버 블로그 팁**\n\n이 프로그램이 써준 원고를 그대로 복사한 뒤, 현장 사진 5~7장과 지도(위치)를 중간중간 첨부해서 발행하시면 검색 노출에 훨씬 유리합니다.")

# 3. 매물 정보 입력 폼
st.subheader("📝 매물 기본 정보 입력")

col1, col2 = st.columns(2)
with col1:
    property_type = st.selectbox("매물 종류", ["상가", "토지", "공장/창고", "아파트", "단독주택", "오피스텔"])
    transaction_type = st.selectbox("거래 종류", ["매매", "임대(전세/월세)"])
with col2:
    location = st.text_input("소재지 (예: 양산시 물금읍 범어리)", placeholder="동/리 단위까지 입력")
    price = st.text_input("가격 (보증금/월세/매매가)", placeholder="예: 보증금 3천 / 월세 200")

st.markdown("##### 📐 면적 및 상세 조건")
area_info = ""

# 매물 종류에 따라 면적 입력칸이 다르게 나타납니다.
if property_type in ["상가", "아파트", "오피스텔"]:
    area_val = st.text_input("전용/공급면적", placeholder="예: 전용 100㎡ (약 30평)")
    area_info = f"- 면적: {area_val}"
    
elif property_type in ["단독주택", "공장/창고"]:
    col3, col4 = st.columns(2)
    with col3:
        land_area = st.text_input("대지면적", placeholder="예: 330㎡ (약 100평)")
    with col4:
        bld_area = st.text_input("건축/연면적", placeholder="예: 150㎡ (약 45평)")
    area_info = f"- 대지면적: {land_area}\n- 건축/연면적: {bld_area}"

elif property_type == "토지":
    col3, col4 = st.columns(2)
    with col3:
        land_area = st.text_input("토지 면적", placeholder="예: 1000㎡ (약 300평)")
    with col4:
        zoning = st.text_input("용도지역 (건폐율/용적률)", placeholder="예: 제1종일반 (60%/200%)")
    area_info = f"- 토지 면적: {land_area}\n- 용도지역 및 건폐율/용적률: {zoning}"

features = st.text_area("✨ 매물 핵심 특장점 (키워드 위주로 편하게 작성)", 
                        placeholder="예: 물금역 도보 5분, 전면 통유리, 주차 5대 넉넉함, 권리금 없음, 최근 내부 올수리 완료, 유동인구 많음")

# 토지일 경우 AI에게 신축 시뮬레이션을 작성하라는 특별 명령
land_special_prompt = ""
if property_type == "토지":
    land_special_prompt = """
    8. 토지 신축 시뮬레이션 (토지 매물 특화) - ★매우 중요★:
       - 입력된 '토지 면적'과 '용도지역 (건폐율/용적률)' 정보를 계산하여, "이 땅을 매수할 경우 1층 바닥면적을 대략 몇 평까지 앉힐 수 있고, 전체 몇 층짜리 건물을 몇 평 규모로 올릴 수 있는지" 매수자 입장에서 상상하기 쉽게 설명하는 브리핑 문단을 추가해주세요.
    """

# 4. 블로그 생성 버튼 및 AI 로직
if st.button("🚀 전문성 넘치는 블로그 포스팅 생성하기", type="primary"):
    if not api_key:
        st.error("⚠️ 왼쪽 사이드바에 구글 Gemini API 키를 입력해주세요!")
    elif not location or not features:
        st.warning("⚠️ 소재지와 매물 핵심 특장점을 입력해주세요.")
    else:
        with st.spinner("AI가 양산시 베테랑 공인중개사의 마인드로 원고를 작성 중입니다... (약 10~15초 소요)"):
            try:
                # API 키 설정 (수동 입력받은 키 사용)
                genai.configure(api_key=api_key)
                
                # 🌟 일일 1,500회 무료로 넉넉하게 쓸 수 있는 1.5 플래시 모델로 변경!
                model = genai.GenerativeModel('gemini-pro')
                
                # 프롬프트(명령어) 세팅
                prompt = f"""
                당신은 경남 양산시에서 20년 이상 활동해온 베테랑 공인중개사입니다. 
                부동산 공법, 건축법, 세법 등에 대한 깊은 지식을 가지고 있으며, 
                단순히 매물을 포장하는 것을 넘어 법적인 안전성(용도지역, 건축물대장 확인 등)까지 철저하게 검증하여 중개하는 전문가의 느낌을 줍니다.

                아래 제공된 매물 정보를 바탕으로 네이버 블로그 포스팅 원고를 작성해주세요.

                [매물 정보]
                - 매물 종류: {property_type}
                - 거래 종류: {transaction_type}
                - 소재지: {location}
                - 가격: {price}
                {area_info}
                - 핵심 특징: {features}

                [블로그 작성 가이드라인 및 SEO 최적화 규칙]
                1. 제목 (Title): 
                   - 검색 유입이 잘 되도록 지역명({location})과 매물 짧은 특징을 반드시 포함하여 호기심을 유발하는 클릭하고 싶은 제목 3가지를 먼저 제안해주세요.
                
                2. 본문 도입부:
                   - 방문자의 이탈률을 줄이도록 지역 호재나 매물 수요자들의 최근 고충에 공감하며 글을 시작하세요.
                
                3. 전문가의 시선 (법적/안전성 강조) - ★가장 중요★:
                   - "단순히 눈에 보이는 것만 브리핑하지 않습니다. 건축물대장상 용도와 양산시 도시계획 조례에 따른 건폐율/용적률, 인허가 제약 여부까지 권리 분석을 마친 안전한 매물입니다." 와 같은 뉘앙스의 문단을 넣어 베테랑의 지식을 과시하세요.
                   
                4. 매물 특징 설명:
                   - 입력된 특징({features})을 자연스럽게 풀어쓰되, 장점을 극대화하세요.
                
                5. 🎯 최적의 활용도 및 타겟 고객 제안 (AI 자동 분석) - ★핵심 미션★:
                   - 매물의 종류({property_type}), 소재지({location}), 면적, 특징 등을 종합적으로 분석하여 이 매물에 가장 잘 어울리는 업종(예: 대형 베이커리 카페, 마라탕 전문점, 물류 창고 등)이나 최적의 매수자 타겟층을 당신(AI)이 스스로 판단해서 추천해 주세요. 중개사로서 "이 자리는 OO이 들어오면 딱입니다!"라고 자신 있게 제안하는 뉘앙스여야 합니다.

                6. 가독성 (모바일 최적화):
                   - 스마트폰으로 읽기 편하게 3~4줄마다 반드시 엔터를 치고, 적절한 소제목(##)과 이모지(📍, 💡, 🏢, ✅ 등)를 활용하세요.
                
                7. 클로징 (Call to Action):
                   - 희소성 있는 매물이니 빠른 현장 안내를 원하면 연락 달라는 멘트로 마무리하세요.
                   
                {land_special_prompt}

                자, 이제 완벽한 블로그 원고를 작성해주세요.
                """
                
                # AI에게 텍스트 생성 요청
                response = model.generate_content(prompt)
                
                # 결과 출력
                st.success("🎉 작성이 완료되었습니다! 아래 내용을 복사해서 네이버 블로그에 붙여넣기 하세요.")
                
                st.markdown("### 📝 생성된 블로그 원고")
                st.markdown("---")
                st.markdown(response.text)
                
                st.markdown("---")
                st.text_area("📋 [복사용 텍스트 박스] 여기를 클릭하고 Ctrl+A, Ctrl+C로 복사하세요.", value=response.text, height=400)
                
            except Exception as e:
                st.error(f"오류가 발생했습니다. API 키가 정확한지 확인해주세요.\n상세 오류: {e}")
