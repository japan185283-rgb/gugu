import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정 (세로형 중심 배치)
st.set_page_config(page_title="부동산 전 업종 완벽 통합 진단 시뮬레이터 Pro", layout="centered")

st.title("🛡️ 부동산 전 업종 완벽 통합 법적 진단 시뮬레이터 Pro")
st.markdown("국토계획법, 건축법, 학교보건법, 양산시 도시계획/건축 조례 및 개별 인허가법 기반의 고난도 규제 진단 툴")

st.markdown("---")

# 📁 [자동 로드 로직] 폴더 안에 지정된 파일명이 있으면 자동 로드, 없으면 업로더 표시
DEFAULT_CSV_NAME = "industrial_complex.csv"
df_parcels = None

if os.path.exists(DEFAULT_CSV_NAME):
    try:
        df_parcels = pd.read_csv(DEFAULT_CSV_NAME)
        df_parcels.columns = df_parcels.columns.str.strip()
        st.success(f"✅ **[산단 데이터 자동 연동됨]** 서버 폴더에서 기본 데이터를 불러왔습니다. (총 {len(df_parcels)}개 필지)")
    except Exception as e:
        st.error(f"⚠️ 기본 데이터 파일 읽기 실패: {e}")
else:
    st.subheader("📁 1. 노션 산단 필지 데이터 파일 업로드 (최초 1회)")
    uploaded_file = st.file_uploader("산단 필지별 업종코드 CSV 파일을 업로드해주세요.", type=["csv"])
    if uploaded_file is not None:
        df_parcels = pd.read_csv(uploaded_file)
        df_parcels.columns = df_parcels.columns.str.strip()
        st.success(f"✅ 산단 데이터 연동 완료! (총 {len(df_parcels)}개 필지 데이터 탑재)")
    else:
        st.info(f"💡 폴더 내에 `{DEFAULT_CSV_NAME}` 파일이 없습니다. 공장/산단 진단을 원하시면 파일을 업로드하거나 해당 이름으로 폴더에 넣어주세요.")

# 건축물대장 주용도 데이터베이스 (건축법 시행령 별표 1 기준 세분화)
general_building_uses = {
    "제1종근린생활시설": ["소매점", "휴게음식점(300㎡미만)", "이용원", "미용원", "세탁소", "탁구장", "체육도장", "의원", "치과의원", "한의원", "약국", "동사무소·파출소"],
    "제2종근린생활시설": ["일반음식점", "휴게음식점(300㎡이상)", "제과점", "학원", "독서실", "공인중개사사무소", "사진관", "금융업소", "종교집회장", "당구장", "PC방", "일반미용업·네일숍", "골프연습장(스크린)", "청소년게임제공업(인형뽑기방·오락실)"],
    "문화및집회시설": ["공연장", "관람장", "전시장", "집회장", "영화상영관", "예식장", "청소년게임제공업(대형)"],
    "판매시설": ["도매시장", "소매시장", "상점", "백화점", "쇼핑센터", "대형마트", "복합쇼핑몰"],
    "운수시설": ["여객자동차터미널", "철도시설", "공항시설", "항만시설", "화물터미널"],
    "의료시설": ["병원", "종합병원", "치과병원", "한방병원", "정신병원", "요양병원"],
    "교육연구시설": ["학교", "교육원", "직업훈련소", "연구소", "도서관", "생활권수련시설"],
    "운동시설": ["체육관", "수영장", "체력단련장(헬스)", "볼링장", "테니스장", "축구장"],
    "업무시설": ["공공업무시설", "일반업무시설(사무소)", "오피스텔", "금융업소"],
    "숙박시설": ["호텔", "모텔", "여관", "펜션", "휴양콘도미니엄", "생활숙박시설(레지던스)"],
    "위락시설": ["주점(유흥주점·단란주점)", "무도장", "카지노업소", "투견장"],
    "공장": ["제조업", "일반공장", "축산물가공업", "식육포장처리업", "식품제조·가공업", "금속가공제품제조업", "인쇄·출판업"],
    "창고시설": ["일반창고", "냉장·냉동창고", "물류터미널", "하역시설", "보관창고"],
    "자동차관련시설": ["주차장", "세차장", "폐차장", "자동차검사장", "매매장", "정비공장"],
    "동물관련시설": ["동물장묘업", "대규모동물생산업", "대형동물위탁관리시설(300㎡이상)", "도축장·도계장"],
    "자원순환관련시설": ["폐기물재활용시설", "폐기물처분시설", "고물상·폐기물보관시설"],
    "단독/다세대/아파트(주택류)": ["외국인관광 도시민박업(에어비앤비 합법)", "단독주택", "다세대주택"]
}

# 용도지역별 기본 금지 업종 (국토계획법 시행령 별표)
zoning_restrictions = {
    "제1종전용주거지역": {"prohibited": ["일반음식점", "휴게음식점", "숙박업", "공장", "제조업", "판매시설", "PC방", "노래연습장", "축산물가공업", "세차장", "창고시설", "위락시설", "무도장", "카지노", "청소년게임제공업", "생활숙박시설", "펜션", "콘도"]},
    "제2종전용주거지역": {"prohibited": ["일반음식점", "숙박업", "공장", "제조업", "축산물가공업", "위락시설", "무도장", "카지노", "청소년게임제공업", "생활숙박시설", "펜션", "콘도"]},
    "제1종일반주거지역": {"prohibited": ["숙박업", "위락시설", "무도장", "카지노", "공장", "제조업", "세차장", "창고시설", "생활숙박시설", "펜션", "콘도"]},
    "제2종일반주거지역": {"prohibited": ["숙박업", "위락시설", "무도장", "카지노", "공장", "제조업", "창고시설", "생활숙박시설", "펜션", "콘도"]},
    "제3종일반주거지역": {"prohibited": ["숙박업", "위락시설", "무도장", "카지노", "공장", "제조업", "생활숙박시설", "펜션", "콘도"]},
    "준주거지역": {"prohibited": ["위락시설(일부제한)", "무도장(지자체조례확인)", "카지노"]},
    "중심상업지역": {"prohibited": []},
    "일반상업지역": {"prohibited": []},
    "근린상업지역": {"prohibited": ["위락시설(일부제한)", "무도장(지자체조례확인)"]},
    "전용공업지역": {"prohibited": ["주거시설", "판매시설", "근린생활시설", "의료시설", "위락시설", "무도장", "카지노", "숙박업", "생활숙박시설"]},
    "일반공업지역": {"prohibited": ["주거시설", "판매시설(대규모)", "위락시설", "무도장", "카지노", "숙박업", "생활숙박시설"]},
    "준공업지역": {"prohibited": ["위락시설(대형)", "무도장(일부제한)"]},
    "보전녹지지역": {"prohibited": ["근린생활시설", "공장", "제조업", "숙박업", "음식점", "축산물가공업", "세차장", "창고시설", "위락시설", "무도장", "카지노", "청소년게임제공업", "생활숙박시설"]},
    "자연녹지지역": {"prohibited": ["숙박업", "공장(일부제한)", "위락시설", "무도장", "카지노", "생활숙박시설"]},
    "계획관리지역": {"prohibited": ["위락시설", "무도장", "카지노"]}
}

# 🌟 양산시 도시계획 조례 및 건축 조례 기반 용도지역별 추가 제한 및 특례 상세 데이터베이스 (모든 업종별 분기 포함)
yangsan_ordinance_rules = {
    "제1종전용주거지역": {
        "additional_prohibited": ["일반음식점", "휴게음식점", "제과점", "골프연습장", "안마시술소", "학원", "PC방", "노래연습장", "사무소"],
        "special_exception": "양산시 도시계획 조례에 따라 제1종전용주거지역 내에서는 원칙적으로 주택 및 부수적인 공공·편익 건축물(공중화장실 등) 외의 상업 및 영업용 시설 설치가 엄격히 금지됩니다."
    },
    "제2종전용주거지역": {
        "additional_prohibited": ["일반음식점", "휴게음식점", "골프연습장", "안마시술소", "단란주점", "유흥주점"],
        "special_exception": "양산시 도시계획 조례에 따라 양호한 주거환경 보호를 위해 근린생활시설 중 소음·악취·유해를 유발하는 업종의 입점이 제한됩니다."
    },
    "제1종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마시술소", "골프연습장(주거환경 저해 시 제한)", "안마시술소", "공장", "제조업"],
        "special_exception": "양산시 도시계획 조례 별표에 의거, 교육환경보호구역 및 주거 밀집 지역 내 소음·악취·빛공해 유발 시설은 건축 위원회 심의 또는 허가가 제한될 수 있습니다."
    },
    "제2종일반주거지역": {
        "additional_prohibited": ["단란주점(주거지역 경계 50m 이내 제한)", "유흥주점(일부 지역)", "안마시술소"],
        "special_exception": "양산시 건축 조례에 따라 공동주택 및 인접 대지와의 일조권 확보를 위한 높이 제한 및 층수 규정이 엄격히 적용됩니다."
    },
    "제3종일반주거지역": {
        "additional_prohibited": ["유흥주점(학교 경계 직선거리 규제 적용)", "위락시설"],
        "special_exception": "양산시 도시계획 조례에 따라 고층 아파트 및 대단지 주변 상가의 경우 주차장 설치 기준이 강화될 수 있습니다."
    },
    "준주거지역": {
        "additional_prohibited": ["숙박시설(주거환경 보호가 필요한 지역)", "위락시설 중 일부(학교·주거지 인근)"],
        "special_exception": "양산시 도시계획 조례상 주거·상업 혼재 지역으로, 학교 및 공동주택 부지 경계로부터의 직선거리에 따라 숙박·위락시설 허가가 엄격히 제한됩니다."
    },
    "중심상업지역": {
        "additional_prohibited": [],
        "special_exception": "양산시 조례상 중심상업지역은 대부분의 상업·업무·위락시설이 허용되나, 주차장법 및 소방방재 기준을 철저히 충족해야 합니다."
    },
    "일반상업지역": {
        "additional_prohibited": [],
        "special_exception": "양산시 조례상 상업 활동 중심 지역으로 대형 판매시설, 유흥시설 등이 가능하나 미관지구 내 건축물 높이 및 용도 제한에 유의해야 합니다."
    },
    "근린상업지역": {
        "additional_prohibited": ["대규모 위락시설(조례 기준 초과)"],
        "special_exception": "양산시 조례에 따라 주거지역과 인접한 근린상업지역은 야간 소음 유발 업종(유흥주점, 단란주점 등)의 영업 허가 시 인근 주민 동의나 심의가 요구될 수 있습니다."
    },
    "전용공업지역": {
        "additional_prohibited": ["일반음식점(지원시설 구역 외)", "소매점(일부)", "숙박시설", "주거시설"],
        "special_exception": "양산시 조례상 순수 공업 전용 구역이므로 주거 및 일반 상업 서비스 시설의 입주가 엄격히 차단됩니다."
    },
    "일반공업지역": {
        "additional_prohibited": ["숙박시설", "위락시설", "대규모 판매시설"],
        "special_exception": "양산시 조례에 따라 공장 및 지식산업센터 외의 일반 대중 이용 시설은 허용 구역이 제한됩니다."
    },
    "준공업지역": {
        "additional_prohibited": ["대규모 위락시설", "숙박시설(주거 밀집 인접 시 제한)"],
        "special_exception": "양산시 조례에 따라 아파트형 공장 및 지원시설(지원상가)의 비율과 업종 제한 규정이 적용됩니다."
    },
    "보전녹지지역": {
        "additional_prohibited": ["모든 일반음식점 및 휴게음식점(조례 예외 제외)", "숙박시설", "공장", "제조업", "창고시설", "근린생활시설 대부분"],
        "special_exception": "양산시 도시계획 조례에 따라 보전녹지지역은 자연환경 보호를 위해 원칙적으로 건축 및 영업 행위가 극도로 제한됩니다."
    },
    "자연녹지지역": {
        "additional_prohibited": ["일반음식점(연면적 300㎡ 이상 또는 조례 기준 초과)", "숙박시설", "공장(일부 오염 배출 업종)", "위락시설"],
        "special_exception": "양산시 조례에 따라 건폐율 20%, 용적률 80부하가 적용되며, 성장관리방안 수립 여부 및 도로 접도 조건에 따라 허용 업종 심사가 까다로울 수 있습니다."
    },
    "계획관리지역": {
        "additional_prohibited": ["숙박시설(배출시설 허가 대상)", "아파트 등 공동주택(조례 층수·세대수 초과 시)", "위락시설"],
        "special_exception": "양산시 도시계획 조례에 따라 공장 및 제조업소 입주 시 폐수·대기 배출시설 설치 승인 대상인 경우 지정된 업종(예: 배출시설 비대상 또는 특정 업종)만 허용될 수 있습니다."
    }
}

st.markdown("---")

# 3. 대상 부동산 기본 팩트 입력
st.subheader("📝 2. 대상 부동산 기본 팩트 입력")

property_type = st.radio("중개 대상물 형태 선택", ["상가 / 일반 건축물", "산업단지 내 공장 (지번 조회)"])
zoning = st.selectbox("토지 용도지역 (국토계획법)", list(zoning_restrictions.keys()))
bld_use = st.selectbox("건축물대장 주용도 (건축법 시행령 별표1)", list(general_building_uses.keys()))

col_f1, col_f2 = st.columns(2)
with col_f1:
    floor_num = st.number_input("건물 층수 (지하층은 음수 입력)", min_value=-5, max_value=50, value=1)
with col_f2:
    area = st.number_input("바닥면적 / 전용면적 (㎡)", min_value=0.0, value=100.0, help="해당 업종이 실제로 사용할 면적")

has_school_zone = st.checkbox("🎓 학교환경위생정화구역(절대·상대정화구역) 저촉 여부 확인", value=False)

# 산단 지번별 자동 조회 변수
selected_parcel_row = None
auto_detected_code = ""
auto_detected_name = ""

if property_type == "산업단지 내 공장 (지번 조회)":
    st.markdown("---")
    st.subheader("🏭 산단 지번별 허용 업종코드 자동 조회")
    if df_parcels is not None:
        jibun_col = '지번' if '지번' in df_parcels.columns else df_parcels.columns[0]
        road_col = '도로명' if '도로명' in df_parcels.columns else df_parcels.columns[1] if len(df_parcels.columns) > 1 else jibun_col

        search_kw = st.text_input("🔍 대상 지번 또는 도로명 검색", placeholder="예: 어곡동 865-23 또는 865")
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
            st.success(f"🎯 **[지번 매칭 완료]** `{sel_addr}` (허용 업종코드: {auto_detected_code})")
        else:
            st.warning("⚠️ 일치하는 지번이 없습니다. 검색어를 다시 확인해주세요.")
    else:
        st.warning("⚠️ 산단 데이터 파일이 로드되지 않았습니다.")

st.markdown("---")
st.subheader("🎯 3. 임차인 희망 업종 및 설비 조건 선택")

comprehensive_biz_dict = {
    "🐶 반려동물 관련 영업": [
        "동물위탁관리업 (강아지유치원·호텔)", "동물미용업 (펫뷰티)", "동물생산업·판매업 (펫샵)", "동물장묘업 및 동물병원"
    ],
    "🍽️ 일반 음식점 및 카페·디저트": [
        "한식·중식·일식·양식 일반음식점", "휴게음식점 (카페·베이커리·디저트)", "제과점 및 아이스크림 전문점", "식육판매업 (정육점 - 소매)"
    ],
    "🍺 주점 및 유흥·위락": [
        "일반주점·맥주집 (간이음식)", "유흥주점 (룸살롱·클럽 - 위락시설)", "단란주점", "무도장 및 카지노업소"
    ],
    "🥩 제조업 및 축산물·식품가공": [
        "식육포장처리업 (축산물가공·도매 공장형)", "식육가공업 (햄·소시지·양념육 제조)", 
        "식품제조·가공업 (일반식품공장)", "금속가공제품 제조업", "인쇄소 및 출판업"
    ],
    "📦 창고, 물류 및 자원순환": [
        "일반 물류창고 및 보관업", "냉장·냉동창고 (신선식품 물류)", "택배 대리점 및 집화시설", "고물상 및 폐기물재활용시설"
    ],
    "🏥 병의원 및 의료시설": [
        "일반의원·소아과·내과", "치과의원 및 치과병원", "한의원 및 한방병원", "요양병원 및 정신병원", "동물병원"
    ],
    "🏋️ 스포츠, 레저 및 운동시설": [
        "피트니스·헬스장 (체력단련장)", "스크린골프장 및 실내골프연습장", "당구장 및 실내 테니스·배드민턴장", "수영장 및 볼링장"
    ],
    "📚 교육, 연구 및 청소년시설": [
        "보습학원·입시학원 및 외국어학원", "독서실 및 스터디카페", "직업훈련소 및 기술학원", "PC방 및 노래연습장", "청소년게임제공업 (인형뽑기방·오락실)"
    ],
    "🚗 자동차 및 환경·세차장": [
        "세차장 (손세차·자동세차 - 폐수배출)", "자동차정비공장 (카센터)", "자동차매매장 및 전시장", "주차장업"
    ],
    "🏡 숙박 및 공유숙박": [
        "일반 숙박업 (모텔·호텔·여관)", "생활숙박시설(레지던스)", "오피스텔 에어비앤비", "외국인관광 도시민박업 (에어비앤비 합법)", "펜션 및 휴양콘도미니엄"
    ],
    "💄 뷰티, 공중위생 및 서비스": [
        "일반미용업·헤어샵 (미용실)", "네일아트 및 피부미용실", "목욕장업 (대중목욕탕·사우나)", "세탁소 (공중위생세탁업)"
    ],
    "💼 일반 오피스 및 전문서비스": [
        "공인중개사사무소", "일반 법무사·행정사·세무사 사무소", "일반 기업체 오피스 (본사·지사)", "금융업소 (은행·증권)"
    ]
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

    # 1. 용도지역 제한 검증 (국토계획법)
    if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
        prohibited_list = zoning_restrictions[zoning]["prohibited"]
        for p in prohibited_list:
            if p in target_biz or p in biz_category or (p == "위락시설" and target_biz in ["무도장 및 카지노업소", "유흥주점 (룸살롱·클럽 - 위락시설)", "단란주점"]):
                fatal_errors.append(
                    f"[국토계획법 제76조 및 동법 시행령 별표] '{zoning}' 지역에서는 국토의 계획 및 이용에 관한 법률에 따라 "
                    f"'{target_biz}'의 입점 및 영업이 법적으로 원천 금지되어 있습니다. "
                    f"💡 **해결 대안:** 해당 용도지역 내에서는 허용되지 않으므로, 상업지역 등 해당 업종이 허용되는 다른 입지로 물건을 변경해야 합니다."
                )

    # 🌟 2. 모든 업종 대상 양산시 도시계획 조례 및 건축 조례 특례 심사 로직 반영
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_ordinance_rules:
        yangsan_rule = yangsan_ordinance_rules[zoning]
        
        # 1) 양산시 조례상 추가 금지 업종 정밀 검증
        for add_p in yangsan_rule["additional_prohibited"]:
            # 키워드 매칭 확장 (예: 일반음식점, 휴게음식점, 숙박, 공장 등)
            if add_p in target_biz or any(kw in target_biz for kw in add_p.split()):
                fatal_errors.append(
                    f"[양산시 도시계획 조례 규제 위반] 양산시 지역 조례에 따라 '{zoning}'에서는 '{target_biz}'({add_p} 관련)의 입점 및 건축허가가 추가로 제한 또는 금지됩니다. "
                    f"💡 **해결 대안:** 양산시청 허가민원과 또는 건축과에 사전 허가 가능 여부를 공식 문의하거나, 허용되는 타 용도지역 물건을 검토하세요."
                )
        
        # 2) 양산시 조례 특례 안내 및 주의사항 추가
        if yangsan_rule["special_exception"]:
            warnings.append(
                f"🏛️ **[양산시 도시계획 조례 특례 및 허가 기준 안내]** {yangsan_rule['special_exception']}"
            )

    # 3. 학교정화구역 검증 (학교보건법)
    if has_school_zone:
        if any(kw in target_biz for kw in ["유흥주점", "단란주점", "PC방", "노래연습장", "호텔", "모텔", "당구장", "청소년게임제공업", "인형뽑기방", "무도장", "카지노", "생활숙박시설"]):
            fatal_errors.append(
                f"[학교보건법 제6조 위반] 본 물건지는 학교환경위생정화구역 내에 위치하고 있어 '{target_biz}'의 영업이 원칙적으로 금지됩니다. "
                f"💡 **해결 대안:** 절대정화구역인 경우 영업이 절대 불가능하며, 상대정화구역인 경우 관할 양산교육지원청 학교환경위생정화위원회 심의를 통과해야만 허가 가능합니다."
            )

    # 4. 업종별 정밀 건축법 및 개별 인허가법 검증 로직 (무조건 적합 방지 엄격 심사)
    if property_type == "상가 / 일반 건축물":
        
        # [반려동물 관련 영업 정밀 검증]
        if "동물위탁관리업" in target_biz:
            if area >= 300.0 and bld_use != "동물관련시설":
                fatal_errors.append(
                    f"[건축법 시행령 별표1 위반] 면적 300㎡ 이상 동물위탁시설은 주용도가 반드시 '동물관련시설'이어야 합니다. (현재 주용도: {bld_use}, 면적: {area}㎡) "
                    f"💡 **해결 대안:** 건축법 제19조에 따라 건축물 용도변경 허가를 거쳐 주용도를 '동물관련시설'로 변경해야 합니다."
                )
            elif area < 300.0 and bld_use not in ["제2종근린생활시설", "동물관련시설"]:
                fatal_errors.append(
                    f"[건축법 시행령 별표1 위반] 300㎡ 미만 동물위탁관리업(강아지유치원 등)은 주용도가 '제2종근린생활시설'(또는 동물관련시설)이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근린생활시설로 건축물 용도변경 허가(또는 신고)를 선행해야 합니다."
                )
            else:
                legal_actions.append("🐶 **[반려동물 영업 적합 검토 가이드]** 건축법상 주용도 및 면적 요건은 적합합니다. ① 동물보호법에 따른 독립된 공간(이중문), ② CCTV 설치, ③ 인접 호실 민원 방지를 위한 방음·방취 공사 시공 여부를 특약으로 명시하세요.")
        
        elif "동물미용업" in target_biz or "동물생산업·판매업" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 동물미용업 및 펫샵은 주용도가 제1·2종근린생활시설 또는 동물관련시설이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 적합한 용도의 건축물로 변경하거나 이전해야 합니다."
                )
            else:
                legal_actions.append("🐾 **[동물미용/판매업 체크]** 동물보호법에 따른 시설기준(격리실, 급수시설 등) 준수 필수.")

        # [음식점 및 카페·디저트 정밀 검증]
        elif "일반음식점" in target_biz or "휴게음식점" in target_biz or "제과점" in target_biz:
            if "300㎡이상" in target_biz and bld_use != "제2종근린생활시설" and bld_use != "판매시설":
                fatal_errors.append(
                    f"[건축법 시행령 별표1 위반] 바닥면적 300㎡ 이상의 휴게음식점은 주용도가 '제2종근린생활시설'(또는 판매시설)이어야 합니다. (현재 주용도: {bld_use}, 면적: {area}㎡) "
                    f"💡 **해결 대안:** 제2종근린생활시설로 용도변경 필수."
                )
            elif bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "판매시설", "숙박시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 해당 음식·휴게업은 제1·2종 근린생활시설 등에 해당해야 영업허가가 가능합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 건축물 용도를 제1·2종 근린생활시설로 변경해야 합니다."
                )
            else:
                legal_actions.append("🍽️ **[음식점 창업 실무 꼼꼼 체크]** 식품위생법에 따른 위생교육 수령, 지하층인 경우 별도 직통계단 설치 여부 및 방수·그리스트랩 설치 의무 확인.")

        elif "식육판매업" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 식육판매업(정육점 소매)은 주용도가 제1종 또는 제2종 근린생활시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 근린생활시설 용도의 상가로 변경 필요."
                )
            else:
                legal_actions.append("🥩 **[식육판매업 체크]** 축산물 위생관리법에 따른 냉장·냉동 쇼케이스 및 도마·칼 소독고 구비 필수.")

        # [주점 및 유흥·위락 정밀 검증]
        elif "유흥주점" in target_biz or "단란주점" in target_biz or "무도장 및 카지노업소" in target_biz:
            if bld_use != "위락시설":
                fatal_errors.append(
                    f"[건축법 위반] 유흥·단란주점 및 무도장·카지노업소는 건축법 시행령 별표1에 따라 반드시 주용도가 **'위락시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 일반 상가에는 위락시설 용도변경이 불가능한 경우가 많으므로, 처음부터 주용도가 '위락시설'인 건축물이나 상업지역 내 전용 건물을 선택해야 합니다."
                )
            else:
                legal_actions.append("🍺 **[위락시설 실무 체크]** 취득세·재산세 중과세 대상 여부, 다중이용업소 소방안전시설완비증명서 발급 가능 여부를 확인하세요.")
        
        elif "일반주점·맥주집" in target_biz:
            if bld_use not in ["제2종근린생활시설", "위락시설", "판매시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 일반음식점 형태로 운영되는 주점은 주용도가 '제2종근린생활시설' 이상이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근생으로 용도변경 필요."
                )
            else:
                legal_actions.append("🍻 **[일반주점 체크]** 식품위생법상 일반음식점 허가 대상이며 청소년 고용 및 주류 판매 규정 준수.")

        # [제조업 및 축산물·식품가공 정밀 검증]
        elif "식육포장처리업" in target_biz or "식육가공업" in target_biz or "식품제조·가공업" in target_biz or "금속가공제품 제조업" in target_biz or "인쇄소 및 출판업" in target_biz:
            if bld_use != "공장":
                if bld_use == "제2종근린생활시설" and area < 500.0:
                    warnings.append(
                        f"[제2종근생 제조업 예외 요건 심사] 주용도가 '제2종근린생활시설'이며 면적({area}㎡)이 500㎡ 미만입니다. "
                        f"다만, 오폐수·악취 등 환경오염 배출시설 허가 대상인 경우 입주가 원천 불가능합니다. "
                        f"💡 **해결 대안:** 관할 양산시청 환경부서 및 위생과를 통해 '배출시설 비대상'임을 사전 확인받으세요."
                    )
                else:
                    fatal_errors.append(
                        f"[건축법 위반] 해당 제조업·가공업은 주용도가 원칙적으로 **'공장'**이어야 합니다. (현재: {bld_use}, 면적: {area}㎡) "
                        f"💡 **해결 대안:** 공장 또는 지식산업센터 내 공장 용도로 물건을 변경해야 합니다."
                    )
            else:
                legal_actions.append("🏭 **[공장 내 가공 실무 체크]** 주용도가 '공장'으로 적합합니다. 산집법 및 환경법상 배출시설 허가 여부를 검토하세요.")

        # [창고, 물류 및 자원순환 정밀 검증]
        elif "냉장·냉동창고" in target_biz or "일반 물류창고" in target_biz:
            if bld_use != "창고시설":
                fatal_errors.append(
                    f"[건축법 위반] 창고업 및 물류센터는 건축법 시행령상 주용도가 반드시 **'창고시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 주용도를 '창고시설'로 변경하거나 전용 창고 건물을 계약해야 합니다."
                )
            else:
                legal_actions.append("📦 **[창고업 실무 체크]** 1톤 이상 화물차 진출입 도로 조건 및 바닥 적재 하중을 확인하세요.")

        elif "고물상 및 폐기물재활용시설" in target_biz:
            if bld_use != "자원순환관련시설":
                fatal_errors.append(
                    f"[건축법 위반] 고물상 및 폐기물 관련 시설은 주용도가 반드시 **'자원순환관련시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 자원순환관련시설로 허가된 부지 및 건물로만 이전해야 합니다."
                )
            else:
                legal_actions.append("♻️ **[자원순환시설 체크]** 폐기물관리법에 따른 허가 및 허가 야적장 펜스 설치 요건 확인.")

        # [병의원 및 의료시설 정밀 검증]
        elif "병원" in target_biz or "종합병원" in target_biz or "요양병원" in target_biz or "정신병원" in target_biz:
            if bld_use != "의료시설":
                fatal_errors.append(
                    f"[건축법 위반] 병원급 의료기관은 주용도가 반드시 **'의료시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 의료시설로 용도변경이 가능한지 건축사 통해 확인 필요."
                )
            else:
                legal_actions.append("🏥 **[의료시설 체크]** 의료법에 따른 병상 간격, 소방시설(스프링클러 등) 엄격 기준 충족 필수.")

        elif "일반의원·소아과·내과" in target_biz or "치과의원" in target_biz or "한의원" in target_biz:
            if bld_use not in ["제1종근린생활시설", "의료시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 의원급 의료기관은 주용도가 제1종근린생활시설 또는 의료시설이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 제1종근린생활시설로 용도변경 선행."
                )
            else:
                legal_actions.append("🩺 **[의원급 체크]** 의료법에 따른 진료실 및 소독시설 구비.")

        elif "동물병원" in target_biz:
            if bld_use not in ["제2종근린생활시설", "동물관련시설", "의료시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 동물병원은 주용도가 제2종근린생활시설, 동물관련시설 또는 의료시설이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근린생활시설 등으로 용도변경 필요."
                )
            else:
                legal_actions.append("🐾 **[동물병원 체크]** 수의사법에 따른 진료실 및 X-ray 방사선 방어벽 설치 확인.")

        # [스포츠, 레저 및 운동시설 정밀 검증]
        elif "피트니스" in target_biz or "헬스장" in target_biz or "수영장" in target_biz or "볼링장" in target_biz:
            if area >= 500.0 and bld_use != "운동시설":
                fatal_errors.append(
                    f"[건축법 시행령 별표1 위반] 바닥면적 500㎡ 이상 운동시설은 주용도가 반드시 **'운동시설'**이어야 합니다. (현재 주용도: {bld_use}, 면적: {area}㎡) "
                    f"💡 **해결 대안:** 건축물대장 주용도를 '운동시설'로 변경하는 용도변경 절차가 필수적입니다."
                )
            elif area < 500.0 and bld_use not in ["제2종근린생활시설", "운동시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 500㎡ 미만 체력단련장은 주용도가 제2종근린생활시설 또는 운동시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근생으로 용도변경 필요."
                )
            else:
                legal_actions.append("🏋️ **[운동시설 실무 체크]** 슬래브 바닥 하중 안전성 검토(건축구조기술사 확인 필수) 및 방진·방음 매트 시공 조건을 확인하세요.")

        elif "스크린골프장" in target_biz or "당구장" in target_biz:
            if bld_use not in ["제2종근린생활시설", "운동시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 스크린골프장 및 당구장은 주용도가 제2종근린생활시설 또는 운동시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근생으로 용도변경 필요."
                )
            else:
                legal_actions.append("⛳ **[스크린골프/당구장 체크]** 층고 높이(보통 3m 이상) 및 방음 시공 확인.")

        # [교육, 연구 및 청소년시설 정밀 검증]
        elif "학원" in target_biz or "직업훈련소" in target_biz:
            if area >= 500.0 and bld_use not in ["교육연구시설", "제2종근린생활시설(학원)"]:
                fatal_errors.append(
                    f"[건축법 위반] 바닥면적 500㎡ 이상 학원은 주용도가 '교육연구시설'이어야 합니다. (현재: {bld_use}, 면적: {area}㎡) "
                    f"💡 **해결 대안:** 교육연구시설로 용도변경 필수."
                )
            elif area < 500.0 and bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 500㎡ 미만 학원은 제2종근린생활시설 또는 교육연구시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 용도변경 필요."
                )
            else:
                legal_actions.append("📚 **[학원업 체크]** 학원의 설립·운영 및 과외교습에 관한 법률에 따른 강의실 면적 및 소방시설(비상구 등) 확인.")

        elif "독서실" in target_biz or "스터디카페" in target_biz:
            if bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 독서실 및 스터디카페는 제2종근린생활시설 또는 교육연구시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 용도변경 필요."
                )
            else:
                legal_actions.append("📖 **[독서실/스카 체크]** 소방안전시설완비증명서 및 소음 방지 설비 확인.")

        elif "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz or "인형뽑기방" in target_biz:
            if bld_use not in ["제2종근린생활시설", "문화및집회시설"]:
                fatal_errors.append(
                    f"[건축법 위반] PC방, 노래연습장, 게임제공업은 주용도가 반드시 **'제2종근린생활시설'**(또는 문화및집회시설)이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근린생활시설로 용도변경을 선행해야 합니다."
                )
            else:
                legal_actions.append("🕹️ **[PC방/게임장 실무 체크포인트]** ① 학교정화구역 거리 검토 필수, ② 다중이용업소 소방필증 발급 의무.")

        # [자동차 및 환경·세차장 정밀 검증]
        elif "세차장" in target_biz:
            if bld_use not in ["자동차관련시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 세차장은 주용도가 반드시 **'자동차관련시설'**이어야 원활합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 건축물 용도를 자동차관련시설로 변경하고 폐수배출시설 승인을 받아야 합니다."
                )
            else:
                legal_actions.append("🚗 **[세차장 실무 꼼꼼 체크]** 오수 정화시설, 유수분리기 설치 여부 및 하수도법상 폐수배출시설 신고 필수.")

        elif "자동차정비공장" in target_biz or "자동차매매장" in target_biz:
            if bld_use != "자동차관련시설":
                fatal_errors.append(
                    f"[건축법 위반] 카센터 및 자동차정비·매매장은 주용도가 반드시 **'자동차관련시설'**이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 자동차관련시설 용도 상가로 이전 또는 변경."
                )
            else:
                legal_actions.append("🔧 **[정비공장 체크]** 대기환경보전법 및 소음진동관리법에 따른 인허가 확인.")

        # [숙박 및 공유숙박 정밀 검증]
        elif "일반 숙박업" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반] 일반숙박업(모텔·호텔)은 건축법 시행령에 따라 주용도가 반드시 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 일반 상가나 주택은 숙박시설 용도변경이 사실상 불가능하므로, 처음부터 주용도가 숙박시설인 물건을 선택해야 합니다."
                )
            else:
                legal_actions.append("🏨 **[숙박업 체크]** 공중위생관리법에 따른 숙박업 영업신고 및 소방시설완비증명서 필수.")

        elif "생활숙박시설(레지던스)" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반] 생활숙박시설(레지던스)은 건축법 시행령에 따라 주용도가 반드시 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 오피스텔이나 일반 주택/상가 등은 생활숙박시설로 용도변경이 엄격히 금지되므로, 건축물대장상 주용도가 '숙박시설'로 허가된 물건만 취득·운영할 수 있습니다."
                )
            else:
                warnings.append(
                    "[주거용 사용 규제 주의] 생활숙박시설은 공중위생관리법상 '숙박업' 신고를 하고 운영해야 합니다. "
                    "주거용으로 불법 사용 시 이행강제금 부과 대상이 되며, 숙박업 영위 시 관할 지자체 및 세무서에 숙박업 등록 및 사업자 등록이 필수적입니다."
                )
                legal_actions.append("🏨 **[생활숙박시설 실무 체크포인트]** 위탁운영사 계약 여부, 주차장 설치 기준 및 소방시설 적합 여부를 확인하세요.")

        elif "오피스텔 에어비앤비" in target_biz:
            fatal_errors.append(
                "[형사 처벌 대상 / 불법 영업] 오피스텔은 건축법상 '업무시설'이므로, 공중위생관리법상 숙박업 합법 등록이 원천 불가능합니다. "
                "💡 **해결 대안:** '생활숙박시설(레지던스)'이거나 '외국인관광 도시민박업' 등록이 가능한 주택 물건으로 계약하셔야 합니다."
            )

        elif "외국인관광 도시민박업" in target_biz:
            if bld_use not in ["단독/다세대/아파트(주택류)"]:
                fatal_errors.append(
                    f"[관광진흥법 위반] 외국인관광 도시민박업은 실제 거주하는 주택(단독·다세대·연립·아파트)에서만 가능합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 건축물대장상 용도가 주택인 물건으로 한정됩니다."
                )
            else:
                legal_actions.append("🏡 **[외국인관광 도시민박업 체크]** 도시민박업 지정 신청, 소방안전기준 및 외국어 안내 서비스 구비.")

        elif "펜션 및 휴양콘도미니엄" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반] 펜션 및 휴양콘도미니엄은 건축법상 주용도가 **'숙박시설'**(또는 농어촌정비법에 따른 농어촌민박 요건)이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 일반 상가나 주택 등은 펜션·콘도 영업이 불가하므로, 해당 용도가 허용되는 부지 및 건축물인지 확인해야 합니다."
                )
            else:
                warnings.append(
                    "[개별 인허가법 주의] 펜션의 경우 건축법상 '숙박시설' 외에도 **'농어촌정비법'**(농어촌민박업) 또는 **'관광진흥법'**에 따른 별도의 등록 요건(실거주 요건 등)을 충족해야 합니다."
                )
                legal_actions.append("🏡 **[펜션/콘도 실무 체크포인트]** 하수처리구역 외 지역인 경우 개인 오수처리시설 용량 및 방류수 수질 기준 검토가 필수적입니다.")

        # [뷰티, 공중위생 및 서비스 정밀 검증]
        elif "일반미용업·헤어샵" in target_biz or "네일아트 및 피부미용실" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 미용업 및 피부미용실은 주용도가 제1종 또는 제2종 근린생활시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 근린생활시설로 용도변경 필요."
                )
            else:
                legal_actions.append("💄 **[미용업 체크]** 공중위생관리법에 따른 면허증 보유 및 소독 장비 구비.")

        elif "목욕장업" in target_biz:
            if bld_use != "제2종근린생활시설":
                fatal_errors.append(
                    f"[건축법 시행령 별표1 위반] 대중목욕탕 및 사우나는 주용도가 반드시 **'제2종근린생활시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근린생활시설 용도 상가로 변경 필수."
                )
            else:
                legal_actions.append("♨️ **[목욕장업 체크]** 수질검사 성적서, 보일러실 안전검사 및 대형 정화조 용량 확보 필수.")

        elif "세탁소" in target_biz:
            if bld_use != "제1종근린생활시설":
                fatal_errors.append(
                    f"[건축법 위반] 세탁소(공중위생세탁업)는 주용도가 '제1종근린생활시설'이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 제1종근생 용도변경 필요."
                )
            else:
                legal_actions.append("👕 **[세탁소 체크]** 드라이클리닝 장비 사용 시 대기배출시설 신고 여부 확인.")

        # [일반 오피스 및 전문서비스 정밀 검증]
        elif "공인중개사사무소" in target_biz or "일반 법무사·행정사·세무사 사무소" in target_biz or "일반 기업체 오피스" in target_biz:
            if bld_use not in ["제2종근린생활시설", "업무시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 일반 사무소 및 공인중개사사무소는 주용도가 제2종근린생활시설 또는 업무시설이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 제2종근생 또는 업무시설로 용도변경 선행."
                )
            else:
                legal_actions.append("💼 **[오피스 입점 적합]** 건축법상 사무소 용도에 부합합니다. 간판 설치 규정 및 통신설비 확인.")

        elif "금융업소" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "업무시설"]:
                fatal_errors.append(
                    f"[건축법 위반] 금융업소는 제1·2종 근린생활시설 또는 업무시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **해결 대안:** 용도변경 필요."
                )
            else:
                legal_actions.append("🏦 **[금융업소 체크]** ATM 코너 설치 시 바닥 하중 및 보안시설 확인.")

        else:
            # 기타 업종 기본 안전장치
            legal_actions.append(f"✅ **[{target_biz} 적합성 검토 완료]** 입력된 건축물 주용도({bld_use}) 및 면적({area}㎡) 기준 일반적인 건축법·국토계획법 요건에 부합합니다. 단, 양산시 조례 및 개별 지침을 최종 확인하세요.")

    else: # 산업단지 내 공장
        if bld_use != "공장":
            fatal_errors.append(
                f"치명적 결격: 산업집적활성화 및 공장설립에 관한 법률(산집법)에 따라 산단 내 공장 등록을 위해서는 주용도가 무조건 **'공장'**이어야 합니다. (현재 주용도: {bld_use}) "
                f"💡 **해결 대안:** 다른 공장 물건을 선택해야 합니다."
            )
        
        if selected_parcel_row is not None:
            input_val = target_biz.strip().upper()
            code_match = input_val in auto_detected_code.upper() or any(c.strip() in input_val for c in auto_detected_code.split(','))
            name_match = input_val in auto_detected_name.upper() or any(w in auto_detected_name for w in target_biz.split())
            
            if target_biz and not code_match and not name_match:
                fatal_errors.append(
                    f"산단 관리기본계획 위반: 해당 지번의 한국산업단지공단(KICOX) 관리기본계획상 허용 업종코드(`{auto_detected_code}`)에 임차인 희망 업종('{target_biz}')이 포함되지 않습니다. "
                    f"💡 **해결 대안:** 해당 지번에서는 입주계약 체결이 불가능합니다."
                )
            else:
                legal_actions.append("✅ **산단 입주계약 적합:** 한국산업단지공단 관리기본계획상 허용 업종 코드 및 명칭에 부합합니다.")

    # 탭 구성 (세로형 정렬에 최적화된 구조)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 1. 상세 법적 리포트", "💰 2. 원인자부담금", "⚡ 3. 전기용량(승압)", "🧯 4. 소방·환경·위생", "🚽 5. 정화조·오수"
    ])

    with tab1:
        st.subheader("📋 공법상 적합성 및 상세 법적 리포트")
        if fatal_errors:
            st.error("### ❌ [계약 절대 금지 / 중개사고 고위험 사유]")
            for err in fatal_errors: st.markdown(f"- **{err}**")
        else:
            st.success("### ✅ [공법상 입주 및 영업 기본 요건 적합]")
        if warnings:
            st.warning("### ⚠️ [주의 및 필수 검토]")
            for w in warnings: st.markdown(f"- {w}")
        if legal_actions:
            st.markdown("### 🛠️ [실무 법적 조치 및 상세 가이드]")
            for act in legal_actions: st.markdown(f"- {act}")

    with tab2:
        st.subheader("💰 상하수도 원인자부담금 시뮬레이션")
        unit_discharge_rates = {
            "동물위탁관리업 (강아지유치원·호텔)": 0.08,
            "식육포장처리업 (축산물가공·도매 공장형)": 0.20,
            "세차장 (손세차·자동세차 - 폐수배출)": 0.35,
            "목욕장업 (대중목욕탕·사우나)": 0.30,
            "한식·중식·일식·양식 일반음식점": 0.18,
            "피트니스·헬스장 (체력단련장)": 0.12,
            "유흥주점 (룸살롱·클럽 - 위락시설)": 0.25,
            "무도장 및 카지노업소": 0.25,
            "청소년게임제공업 (인형뽑기방·오락실)": 0.05,
            "생활숙박시설(레지던스)": 0.20,
            "펜션 및 휴양콘도미니엄": 0.20,
        }
        rate = unit_discharge_rates.get(target_biz, 0.05)
        estimated_discharge = area * rate
        est_water_fee = estimated_discharge * 1823000
        est_sewage_fee = (estimated_discharge * 1910000) if estimated_discharge >= 10 else 0

        st.markdown(f"- 추정 일일 오수량: **{estimated_discharge:.1f} 톤(㎥/일)** (면적 {area}㎡ 기준)")
        st.markdown(f"- **상수도원인자부담금:** 약 **{est_water_fee:,.0f} 원**")
        if estimated_discharge >= 10:
            st.markdown(f"- **하수도원인자부담금:** 약 **{est_sewage_fee:,.0f} 원** *(10톤 이상 전량 부과 대상)*")
        else:
            st.markdown("- **하수도원인자부담금:** ✅ **면제 대상** *(10톤 미만)*")
        st.info("💡 양산시 수도조례에 따라 실제 부과 금액은 상이할 수 있습니다.")

    with tab3:
        st.subheader("⚡ 현실적인 계약전력 및 승압 진단")
        
        if "피트니스" in target_biz or "헬스장" in target_biz or "제조업" in target_biz or "공장" in target_biz or "식품제조" in target_biz or "식육포장" in target_biz or "무도장" in target_biz:
            base_kw = 15.0
            kw_per_sqm = 0.08 
            max_cap = 60.0
        elif "음식점" in target_biz or "카페" in target_biz or "제과점" in target_biz or "유흥주점" in target_biz or "카지노" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz:
            base_kw = 15.0
            kw_per_sqm = 0.06
            max_cap = 50.0
        elif "청소년게임제공업" in target_biz or "인형뽑기방" in target_biz:
            base_kw = 12.0
            kw_per_sqm = 0.04
            max_cap = 45.0
        else:
            base_kw = 5.0
            kw_per_sqm = 0.02
            max_cap = 25.0

        req_power = min(base_kw + (area * kw_per_sqm), max_cap)
        power_diff = req_power - current_power
        est_electric_fee = max(0, power_diff) * 110000

        st.markdown(f"- **현재 건물(호실) 계약전력:** `{current_power} kW`")
        st.markdown(f"- **업종별 현실적 권장 소요전력:** 약 `{req_power:.1f} kW` (상가/사무소 표준 부하 산정 기준)")

        if power_diff > 0:
            st.warning(f"⚠️ **[승압 필요]** 현재 전력보다 약 `{power_diff:.1f} kW`의 추가 전력이 필요합니다.")
            st.markdown(f"- **예상 한전 표준시설부담금(참고용):** 약 **{est_electric_fee:,.0f} 원** *(한전 불입금 별도)*")
        else:
            st.success("✅ **[전기 용량 충분]** 현재 계약전력으로 정상적인 영업 가동이 가능합니다.")

    with tab4:
        st.subheader("🧯 소방, 환경 및 위생 규제 요건 상세 심사")
        if "유흥주점" in target_biz or "단란주점" in target_biz or "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz or "인형뽑기방" in target_biz or "무도장" in target_biz or "카지노" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz:
            st.markdown("- **다중이용업소 특별법 / 숙박시설 소방안전기준:** 소방시설완비증명서, 방염필증, 객실별 완강기 및 화재경보기 설치 의무 대상.")
        elif "병원" in target_biz or "의원" in target_biz or "동물병원" in target_biz:
            st.markdown("- **의료폐기물:** 감염성·의료폐기물 전용 보관함 및 전문 처리업체 계약 필수.")
        elif "세차장" in target_biz:
            st.markdown("- **환경부 수질관리:** 폐수배출시설 설치 승인 및 오수정화시설 필수.")
        else:
            st.markdown("- 일반 건축물 소방안전점검 기준 준수 대상.")

    with tab5:
        st.subheader("🚽 건물 정화조 용량 검토 및 오수 발생량")
        est_dis = area * rate
        st.markdown(f"- 추정 일일 오수량: `{est_dis:.1f} 톤/일`")
        if est_dis >= 5.0 or "음식점" in target_biz or "목욕" in target_biz or "무도장" in target_biz or "숙박시설" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz:
            st.warning("⚠️ 오수 발생량이 많거나 수질오염 유발 시설이므로, 건물 정화조 인용 초과 여부를 관리사무소에 반드시 확인하세요.")
        else:
            st.success("✅ 정화조 오수 부담 안정적")
