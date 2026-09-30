import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="부동산 전 업종 완벽 통합 진단 시뮬레이터 Pro v3", layout="centered")

st.title("🛡️ 부동산 전 업종 완벽 통합 법적 진단 시뮬레이터 Pro v3")
st.markdown("양산시 도시계획/건축 조례, 주요 지구단위계획 및 산단 맞춤형 실무 진단 툴")

st.markdown("---")

# 📁 [자동 로드 로직] 산단 필지 데이터
DEFAULT_CSV_NAME = "industrial_complex.csv"
df_parcels = None

if os.path.exists(DEFAULT_CSV_NAME):
    try:
        df_parcels = pd.read_csv(DEFAULT_CSV_NAME)
        df_parcels.columns = df_parcels.columns.str.strip()
    except Exception as e:
        pass

# 건축물대장 주용도 데이터베이스
general_building_uses = [
    "제1종근린생활시설", "제2종근린생활시설", "문화및집회시설", "판매시설", "운수시설",
    "의료시설", "교육연구시설", "운동시설", "업무시설", "숙박시설", "위락시설",
    "공장", "창고시설", "자동차관련시설", "동물관련시설", "자원순환관련시설", "단독/다세대/아파트(주택류)"
]

# 용도지역별 기본 금지 업종
zoning_restrictions = {
    "제1종전용주거지역": {"prohibited": ["일반음식점", "휴게음식점", "숙박업", "공장", "제조업", "판매시설", "PC방", "노래연습장", "위락시설"]},
    "제2종전용주거지역": {"prohibited": ["일반음식점", "숙박업", "공장", "제조업", "위락시설"]},
    "제1종일반주거지역": {"prohibited": ["숙박업", "위락시설", "공장", "제조업", "세차장", "창고시설"]},
    "제2종일반주거지역": {"prohibited": ["숙박업", "위락시설", "공장", "제조업", "창고시설"]},
    "제3종일반주거지역": {"prohibited": ["숙박업", "위락시설", "공장", "제조업"]},
    "준주거지역": {"prohibited": ["위락시설(일부제한)", "카지노"]},
    "중심상업지역": {"prohibited": []},
    "일반상업지역": {"prohibited": []},
    "근린상업지역": {"prohibited": ["위락시설(일부제한)"]},
    "전용공업지역": {"prohibited": ["주거시설", "판매시설", "근린생활시설", "의료시설", "위락시설", "숙박업"]},
    "일반공업지역": {"prohibited": ["주거시설", "판매시설(대규모)", "위락시설", "숙박업"]},
    "준공업지역": {"prohibited": ["위락시설(대형)"]},
    "보전녹지지역": {"prohibited": ["근린생활시설", "공장", "제조업", "숙박업", "음식점", "창고시설", "위락시설"]},
    "자연녹지지역": {"prohibited": ["숙박업", "공장(일부제한)", "위락시설"]},
    "계획관리지역": {"prohibited": ["위락시설"]}
}

# 양산시 대표 지구단위계획구역별 맞춤 규제 데이터베이스 (실무형 자동 매칭)
yangsan_district_presets = {
    "해당 없음 (일반 지역)": {
        "prohibited": "",
        "allowed": "국토계획법 및 조례에 따름"
    },
    "양산 물금택지개발지구 (근린상업/준주거)": {
        "prohibited": "단란주점, 유흥주점, 안마시술소, 숙박시설(일부 블록), 대형창고, 고물상",
        "allowed": "제1·2종근린생활시설, 교육연구시설, 업무시설, 운동시설, 판매시설"
    },
    "양산 사송공공주택지구 (상업용지/근린생활)": {
        "prohibited": "유흥주점, 단란주점, 안마시술소, 숙박시설, 공장, 위험물저장및처리시설",
        "allowed": "제1·2종근린생활시설, 의료시설, 교육연구시설, 노유자시설"
    },
    "양산 어곡/산막 일반산업단지 (지원시설/공장)": {
        "prohibited": "주거시설, 숙박시설, 위락시설, 학교, 일반음식점(일부 공장용지 내 제한)",
        "allowed": "공장, 제조업, 창고시설, 지원시설(지식산업센터 및 근린생활시설 일부)"
    },
    "웅상 소주/주진 지구단위계획구역": {
        "prohibited": "단란주점, 유흥주점, 공해유발 공장, 숙박시설(주거인접지)",
        "allowed": "제1·2종근린생활시설, 판매시설, 업무시설"
    }
}

# 양산시 도시계획 조례 세부 업종 교차 진단 데이터베이스
yangsan_ordinance_rules = {
    "제1종전용주거지역": {
        "additional_prohibited": ["음식점", "카페", "제과점", "골프연습장", "안마시술소", "학원", "PC방", "노래연습장", "사무소", "식육판매업", "미용업", "세탁소", "동물위탁관리업", "병원", "의원"],
        "legal_basis": "양산시 도시계획 조례에 따라 제1종전용주거지역 내 영업·상업·근린생활시설 설치 엄격 금지"
    },
    "제2종전용주거지역": {
        "additional_prohibited": ["음식점", "카페", "제과점", "골프연습장", "안마시술소", "단란주점", "유흥주점", "PC방", "노래연습장", "동물위탁관리업"],
        "legal_basis": "양산시 도시계획 조례에 따라 주거환경 보호를 위해 상업 업종 입점 제한"
    },
    "제1종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마시술소", "골프연습장", "공장", "제조업", "세차장", "창고시설", "고물상"],
        "legal_basis": "양산시 도시계획 조례 및 교육환경보호구역 기준에 의거 소음·환경오염 유발 시설 제한"
    },
    "제2종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마시술소", "공장", "제조업", "고물상"],
        "legal_basis": "양산시 도시계획 조례에 따라 정주 환경을 해치는 공장 및 위락·유흥 업종 차단"
    },
    "제3종일반주거지역": {
        "additional_prohibited": ["유흥주점", "위락시설", "안마시술소", "공장", "제조업"],
        "legal_basis": "양산시 도시계획 조례상 고층 공동주택 밀집 지역으로 위락·숙박·공장 업종 제한"
    },
    "준주거지역": {
        "additional_prohibited": ["숙박시설", "위락시설"],
        "legal_basis": "양산시 도시계획 조례상 주거·상업 혼재 지역이나 학교 경계 거리에 따라 숙박·위락 제한"
    },
    "중심상업지역": {"additional_prohibited": [], "legal_basis": "상업·업무 중심 지역 (주차장·소방 기준 준수 필수)"},
    "일반상업지역": {"additional_prohibited": [], "legal_basis": "일반 상업 및 업무 활동 지역"},
    "근린상업지역": {"additional_prohibited": ["유흥주점", "무도장"], "legal_basis": "주거지역 인접 근린상업지역 대형 유흥·위락 업종 영업 허가 제한"},
    "전용공업지역": {"additional_prohibited": ["일반음식점", "휴게음식점", "소매점", "숙박시설", "주거시설"], "legal_basis": "순수 공업 전용 구역으로 대중 대상 상업 서비스 시설 입주 차단"},
    "일반공업지역": {"additional_prohibited": ["숙박시설", "위락시설", "주거시설"], "legal_basis": "공장 및 공장 지원시설 외 일반 상업시설 허용 구역 엄격 제한"},
    "준공업지역": {"additional_prohibited": ["위락시설(대형)", "숙박시설"], "legal_basis": "아파트형 공장 및 지원상가 비율 규정 적용"},
    "보전녹지지역": {"additional_prohibited": ["일반음식점", "휴게음식점", "카페", "숙박시설", "공장", "제조업", "창고시설", "위락시설"], "legal_basis": "자연환경 및 녹지 보호를 위해 영리 목적 영업 행위 극도로 제한"},
    "자연녹지지역": {"additional_prohibited": ["숙박시설", "공장(일부제한)", "위락시설"], "legal_basis": "건폐율 20%, 용적률 80% 이하 적용, 성장관리방안 확인 필수"},
    "계획관리지역": {"additional_prohibited": ["숙박시설", "위락시설"], "legal_basis": "공장 및 제조업소 입주 시 배출시설 기준 적용"}
}

yangsan_building_ordinance_rules = {
    "제1종전용주거지역": {"max_height_rule": "인접 대지경계선 및 도로와의 관계에 따른 일조권 확보 높이 제한 엄격", "parking_rule": "조례에 따른 강화된 주차장 설치 기준 적용"},
    "제2종전용주거지역": {"max_height_rule": "정북 방향 일조권 및 높이 제한 엄격 적용", "parking_rule": "가구당 법정 주차 대수 준수 필수"},
    "제1종일반주거지역": {"max_height_rule": "정북 방향 및 채광을 위한 일조 확보 높이 제한", "parking_rule": "다세대·근생 복합 건축 시 세대당 주차 대수 확인"},
    "제2종일반주거지역": {"max_height_rule": "공동주택 및 인접 대지 일조권 확보 높이 제한", "parking_rule": "상가 및 주택 복합 건축물 주차요건 강화"},
    "제3종일반주거지역": {"max_height_rule": "가로구역별 최고 높이 지정 구역 확인 필요", "parking_rule": "주변 상가 및 오피스텔 주차장 설치 기준 강화"},
    "준주거지역": {"max_height_rule": "인근 주거지역 일조권 영향에 따른 높이 규정 검토", "parking_rule": "상업시설 및 부설주차장 설치 기준 엄수"},
    "중심상업지역": {"max_height_rule": "가로구역별 건축물 최고 높이 지정 구역 확인", "parking_rule": "부설주차장 설치 면제/완화 가능하나 다중이용업소 자체 주차 필수"},
    "일반상업지역": {"max_height_rule": "미관지구·경관지구 내 높이 및 형태 제한", "parking_rule": "상업용 시설 규모별 법정 주차 대수 산정"},
    "근린상업지역": {"max_height_rule": "주거지역 인접 시 일조권 및 높이 제한 연계 적용", "parking_rule": "근생 및 유흥·위락 복합 시 주차요건 강화"},
    "전용공업지역": {"max_height_rule": "공장 처마높이 및 층수 제한, 구조안전 확인", "parking_rule": "공장 면적 및 상시 고용 인원 기준 부설주차장"},
    "일반공업지역": {"max_height_rule": "대형 공장 최고 높이 및 소방도로 확보 기준", "parking_rule": "화물차 및 일반 승용차 주차구획 동시 확보"},
    "준공업지역": {"max_height_rule": "아파트형 공장 및 복합 지원시설 높이 기준", "parking_rule": "지원시설 비율에 따른 주차장 산정 기준 준수"},
    "보전녹지지역": {"max_height_rule": "원칙적으로 3층 이하 또는 높이 11미터 이하 제한", "parking_rule": "예외적 건축물 허용 시 법정 주차기준 적용"},
    "자연녹지지역": {"max_height_rule": "건폐율 20%, 용적률 80% 이하 및 4층 이하 제한", "parking_rule": "건축 조례에 따른 부설주차장 설치 기준 적용"},
    "계획관리지역": {"max_height_rule": "성장관리방안 구역 여부에 따른 층수·높이 인센티브", "parking_rule": "공장·창고·근생 부설주차장 기준 준수"}
}

st.markdown("---")

# 3. 대상 부동산 기본 팩트 입력
st.subheader("📝 1. 대상 부동산 기본 팩트 및 위치 설정")

property_type = st.radio("중개 대상물 형태 선택", ["상가 / 일반 건축물", "산업단지 내 공장 (지번 조회)"])
zoning = st.selectbox("토지 용도지역 (국토계획법)", list(zoning_restrictions.keys()))

# 📐 양산시 실무 맞춤형 지구단위계획 선택창
st.markdown("#### 📐 양산시 주요 지구단위계획구역 선택 (자동 규제 매칭)")
selected_district = st.selectbox("진단할 지구단위계획구역 선택", list(yangsan_district_presets.keys()))

# 선택된 지구에 따른 기본값 불러오기
preset_info = yangsan_district_presets[selected_district]

col_d1, col_d2 = st.columns(2)
with col_d1:
    district_prohibited_input = st.text_input(
        "🚫 지구단위계획상 **불허(금지) 업종** (수정 가능)", 
        value=preset_info["prohibited"],
        placeholder="예: 단란주점, 유흥주점 등"
    )
with col_d2:
    district_allowed_input = st.text_input(
        "✅ 지구단위계획상 **허용/지정 업종** (수정 가능)", 
        value=preset_info["allowed"],
        placeholder="예: 제1·2종근린생활시설 등"
    )

bld_use = st.selectbox("건축물대장 주용도 (건축법 시행령 별표1)", general_building_uses)

col_f1, col_f2 = st.columns(2)
with col_f1:
    floor_num = st.number_input("건물 층수 (지하층은 음수)", min_value=-5, max_value=50, value=1)
with col_f2:
    area = st.number_input("바닥면적 / 전용면적 (㎡)", min_value=0.0, value=100.0)

has_school_zone = st.checkbox("🎓 학교환경위생정화구역(절대·상대정화구역) 저촉 여부 확인", value=False)

selected_parcel_row = None
auto_detected_code = ""
auto_detected_name = ""

if property_type == "산업단지 내 공장 (지번 조회)":
    st.markdown("---")
    st.subheader("🏭 산단 지번별 실시간 검색 및 허용 업종 자동 조회")
    if df_parcels is not None:
        jibun_col = '지번' if '지번' in df_parcels.columns else df_parcels.columns[0]
        road_col = '도로명' if '도로명' in df_parcels.columns else df_parcels.columns[1] if len(df_parcels.columns) > 1 else jibun_col

        search_kw = st.text_input("🔍 산단 지번 또는 도로명 실시간 검색", placeholder="예: 어곡동, 865, 산단로 등 입력")
        if search_kw:
            clean_kw = search_kw.replace(" ", "")
            f_df = df_parcels[
                df_parcels[jibun_col].astype(str).str.replace(" ", "").str.contains(clean_kw, na=False) | 
                df_parcels[road_col].astype(str).str.replace(" ", "").str.contains(clean_kw, na=False)
            ]
        else:
            f_df = df_parcels
        
        if len(f_df) > 0:
            parcel_options = f_df[jibun_col].astype(str).tolist()
            sel_addr = st.selectbox("조회된 필지(지번) 선택", parcel_options)
            selected_parcel_row = f_df[f_df[jibun_col].astype(str) == sel_addr].iloc[0]
            
            code_col = '허용 업종코드' if '허용 업종코드' in df_parcels.columns else (df_parcels.columns[2] if len(df_parcels.columns) > 2 else '')
            name_col = '업종 명칭' if '업종 명칭' in df_parcels.columns else (df_parcels.columns[3] if len(df_parcels.columns) > 3 else '')
            
            auto_detected_code = str(selected_parcel_row.get(code_col, ''))
            auto_detected_name = str(selected_parcel_row.get(name_col, ''))
            st.success(f"🎯 **[지번 매칭 완료]** `{sel_addr}` (허용 업종코드: {auto_detected_code} / 업종명: {auto_detected_name})")
        else:
            st.warning("⚠ 일치하는 지번이 없습니다. 검색어를 다시 확인해주세요.")
    else:
        st.warning("⚠️ 산단 데이터 파일(`industrial_complex.csv`)이 서버 폴더에 없습니다.")

st.markdown("---")
st.subheader("🎯 2. 임차인 희망 업종 및 조건 선택")

comprehensive_biz_dict = {
    "🐶 반려동물 관련 영업": ["동물위탁관리업", "동물미용업", "동물생산업·판매업", "동물장묘업 및 동물병원"],
    "🍽 일반 음식점 및 카페·디저트": ["일반음식점", "휴게음식점", "제과점 및 아이스크림 전문점", "식육판매업"],
    "🍺 주점 및 유흥·위락": ["일반주점·맥주집", "유흥주점", "단란주점", "무도장 및 카지노업소"],
    "🥩 제조업 및 축산물·식품가공": ["식육포장처리업", "식육가공업", "식품제조·가공업", "금속가공제품 제조업", "인쇄소 및 출판업"],
    "📦 창고, 물류 및 자원순환": ["일반 물류창고", "냉장·냉동창고", "택배 대리점 및 집화시설", "고물상 및 폐기물재활용시설"],
    "🏥 병의원 및 의료시설": ["병원", "치과의원", "한의원", "요양병원", "동물병원"],
    "🏋 스포츠, 레저 및 운동시설": ["피트니스·헬스장", "스크린골프장", "당구장", "수영장 및 볼링장"],
    "📚 교육, 연구 및 청소년시설": ["학원", "독서실 및 스터디카페", "직업훈련소", "PC방", "노래연습장", "청소년게임제공업"],
    "🚗 자동차 및 환경·세차장": ["세차장", "자동차정비공장", "자동차매매장", "주차장업"],
    "🏡 숙박 및 공유숙박": ["일반 숙박업", "생활숙박시설", "오피스텔 에어비앤비", "외국인관광 도시민박업", "펜션 및 휴양콘도미니엄"],
    "💄 뷰티, 공중위생 및 서비스": ["일반미용업·헤어샵", "네일아트 및 피부미용실", "목욕장업", "세탁소"],
    "💼 일반 오피스 및 전문서비스": ["공인중개사사무소", "일반 법무사·행정사·세무사 사무소", "일반 기업체 오피스", "금융업소"]
}

biz_category = st.selectbox("희망 업종 대분류", list(comprehensive_biz_dict.keys()))
target_biz = st.selectbox("세부 희망 업종 선택", comprehensive_biz_dict[biz_category])
current_power = st.number_input("현재 건물(호실) 계약전력 (kW)", min_value=1.0, value=10.0, step=1.0)

submitted = st.button("🚀 종합 법적 진단 리포트 생성", type="primary")

if submitted:
    st.markdown("---")
    
    fatal_errors = []
    warnings = []
    legal_actions = []

    # 1. 국토계획법 용도지역 검증
    if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
        prohibited_list = zoning_restrictions[zoning]["prohibited"]
        for p in prohibited_list:
            if p in target_biz or p in biz_category or (p == "위락시설" and target_biz in ["무도장 및 카지노업소", "유흥주점", "단란주점"]):
                fatal_errors.append(
                    f"[국토계획법 제76조] '{zoning}' 지역에서는 국토계획법에 따라 '{target_biz}'의 입점 및 영업이 원천 금지되어 있습니다."
                )

    # 2. 지구단위계획 불허/허용 검증
    if property_type == "상가 / 일반 건축물" and selected_district != "해당 없음 (일반 지역)":
        if district_prohibited_input.strip():
            banned_keywords = [b.strip() for b in district_prohibited_input.split(",") if b.strip()]
            for bk in banned_keywords:
                if len(bk) > 1 and (bk in target_biz or any(bk in w for w in target_biz.split()) or any(w in bk for w in target_biz.split())):
                    fatal_errors.append(
                        f"[지구단위계획 불허용도 저촉 위반] 선택하신 구역('{selected_district}')의 불허 업종 규정에 '{target_biz}'(관련 규제: {bk})가 포함되어 있어 영업이 불가합니다."
                    )
                    break

    # 3. 양산시 도시계획 조례 교차 진단
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_ordinance_rules:
        yangsan_rule = yangsan_ordinance_rules[zoning]
        matched_ban = False
        for add_p in yangsan_rule["additional_prohibited"]:
            if add_p in target_biz or add_p in biz_category:
                matched_ban = True
                fatal_errors.append(
                    f"[양산시 도시계획 조례 위반] **양산시 도시계획 조례**에 따라 '{zoning}' 지역에서는 '{target_biz}'의 입점이 엄격히 금지됩니다. (근거: {yangsan_rule['legal_basis']})"
                )
                break
        if not matched_ban:
            legal_actions.append(f"🏛 **[양산시 도시계획 조례 통과]** '{zoning}' 지역 내 '{target_biz}' 입점은 조례 추가 제한에 저촉되지 않습니다.")

    # 4. 양산시 건축 조례 검토
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_building_ordinance_rules:
        bld_rule = yangsan_building_ordinance_rules[zoning]
        legal_actions.append(f"📐 **[양산시 건축 조례 - 높이/일조]** {bld_rule['max_height_rule']}")
        legal_actions.append(f"🚗 **[양산시 건축 조례 - 주차장]** {bld_rule['parking_rule']}")

    # 5. 학교정화구역 검증
    if has_school_zone and any(kw in target_biz for kw in ["유흥주점", "단란주점", "PC방", "노래연습장", "숙박", "당구장", "청소년게임제공업", "무도장", "카지노"]):
        fatal_errors.append(f"[학교보건법 제6조 위반] 학교환경위생정화구역 내 위치하여 '{target_biz}' 영업이 제한됩니다.")

    # 6. 건축법 주용도 및 합법화 표시변경 대안 가이드
    if property_type == "상가 / 일반 건축물":
        if "세탁소" in target_biz and bld_use != "제1종근린생활시설":
            warnings.append("[세탁소 합법화 대안] '건축물 표시변경(제1종근린생활시설)'을 신청해야 합니다.")
        elif "일반음식점" in target_biz or "휴게음식점" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "판매시설"]:
                warnings.append("[음식점 합법화 대안] '건축물 표시변경(제2종근린생활시설)'이 필요합니다.")
        elif "유흥주점" in target_biz or "단란주점" in target_biz:
            if bld_use != "위락시설":
                fatal_errors.append(f"[건축법 위반] 유흥·단란주점은 주용도가 반드시 '위락시설'이어야 합니다. (현재: {bld_use}) 상가 건물은 변경 불가하므로 위락시설 허가 건물을 구하셔야 합니다.")
        elif "식품제조" in target_biz or "제조업" in target_biz:
            if bld_use != "공장" and not (bld_use == "제2종근린생활시설" and area < 500.0):
                warnings.append("[제조업소 합법화 가이드] 면적 500㎡ 미만 소규모 제조업은 '제2종근린생활시설(제조업소)' 표시변경을 통해 입점할 수 있습니다.")
        else:
            legal_actions.append(f"✅ **[{target_biz}]** 건축법상 주용도 검토 완료")
    else:
        if bld_use != "공장":
            fatal_errors.append(f"치명적 결격: 산단 내 공장 등록을 위해서는 주용도가 무조건 '공장'이어야 합니다. (현재: {bld_use})")
        if selected_parcel_row is not None:
            input_val = target_biz.strip().upper()
            code_match = input_val in auto_detected_code.upper() or any(c.strip() in input_val for c in auto_detected_code.split(','))
            if target_biz and not code_match:
                fatal_errors.append(f"산단 관리기본계획 위반: 해당 지번의 허용 업종코드(`{auto_detected_code}`)에 포함되지 않습니다.")
            else:
                legal_actions.append("✅ **산단 입주계약 적합:** 허용 업종 코드에 부합합니다.")

    # 탭 구성 출력
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 1. 상세 법적 리포트", "💰 2. 원인자부담금", "⚡ 3. 전기용량(승압)", "🧯 4. 소방·환경·위생", "🚽 5. 정화조·오수"
    ])

    with tab1:
        st.subheader("📋 공법상 적합성 및 상세 법적 진단 리포트")
        st.markdown("---")
        if fatal_errors:
            st.error("### ❌ [계약 절대 금지 / 중개사고 고위험 사유]")
            for err in fatal_errors: st.markdown(f"- **{err}**")
            st.markdown("---")
        else:
            st.success("### ✅ [공법상 입주 및 영업 기본 요건 적합]")
            st.markdown("---")
            
        if warnings:
            st.warning("### ⚠ [주의 및 용도변경·표시변경 합법화 대안]")
            for w in warnings: st.markdown(f"- {w}")
            st.markdown("---")
            
        if legal_actions:
            st.markdown("### 🛠️ [실무 법적 조치 및 가이드]")
            for act in legal_actions: st.markdown(f"- {act}")

    with tab2:
        st.subheader("💰 상하수도 원인자부담금 시뮬레이션")
        est_discharge = area * 0.08
        st.markdown(f"- 추정 일일 오수량: **{est_discharge:.1f} 톤(㎥/일)**")
        st.markdown(f"- 상수도원인자부담금: 약 **{est_discharge * 1823000:,.0f} 원**")
        st.markdown(f"- 하수도원인자부담금: {'약 ' + f'{est_discharge * 1910000:,.0f} 원' if est_discharge >= 10 else '✅ 면제 대상 (10톤 미만)'}")

    with tab3:
        st.subheader("⚡ 전기용량 및 승압 진단")
        req_power = min(15.0 + (area * 0.06), 50.0)
        st.markdown(f"- 현재 계약전력: `{current_power} kW` / 권장 소요전력: 약 `{req_power:.1f} kW`")
        if req_power > current_power:
            st.warning(f"⚠️ 약 `{req_power - current_power:.1f} kW` 승압 필요 (예상 한전비용: 약 `{(req_power - current_power) * 110000:,.0f} 원`)")
        else:
            st.success("✅ 전기 용량 충분")

    with tab4:
        st.subheader("🧯 소방, 환경 및 위생 규제 요건")
        st.markdown("- 다중이용업소 소방방재기준, 환경부 수질/대기 배출시설 승인 여부 현장 확인 필수")

    with tab5:
        st.subheader("🚽 건물 정화조 용량 검토")
        st.markdown(f"- 추정 오수발생량: `{area * 0.08:.1f} 톤/일` (관리사무소 정화조 용량 잔여분 확인 필수)")
