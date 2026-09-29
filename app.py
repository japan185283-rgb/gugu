import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정 (세로형 중심 배치)
st.set_page_config(page_title="부동산 전 업종 완벽 통합 진단 시뮬레이터 Pro", layout="centered")

st.title("🛡️ 부동산 전 업종 완벽 통합 법적 진단 시뮬레이터 Pro")
st.markdown("국토계획법, 건축법, 학교보건법, 양산시 도시계획/건축 조례 및 개별 인허가법 기반의 전수 크로스 체크 규제 진단 툴")

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

# 🌟 [업종 연동형 개편] 양산시 도시계획 조례 및 건축 조례 기반 용도지역별 세부 업종 교차 진단 데이터베이스
yangsan_ordinance_rules = {
    "제1종전용주거지역": {
        "additional_prohibited": ["음식점", "카페", "제과점", "골프연습장", "안마시술소", "학원", "PC방", "노래연습장", "사무소", "식육판매업", "미용업", "세탁소", "동물위탁관리업", "동물미용업", "공인중개사", "병원", "의원"],
        "legal_basis": "양산시 도시계획 조례에 따라 제1종전용주거지역 내에서는 단독주택 및 양호한 주거환경에 지장을 주지 않는 일부 부수시설 외의 일반 영업·상업·근린생활시설 설치가 엄격히 금지됩니다."
    },
    "제2종전용주거지역": {
        "additional_prohibited": ["음식점", "카페", "제과점", "골프연습장", "안마시술소", "단란주점", "유흥주점", "PC방", "노래연습장", "동물위탁관리업"],
        "legal_basis": "양산시 도시계획 조례에 따라 공동주택 중심의 양호한 주거환경 보호를 위해 소음, 악취, 유해물질 또는 방문객 밀집을 유발하는 상업 업종의 입점이 제한됩니다."
    },
    "제1종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마시술소", "골프연습장", "공장", "제조업", "세차장", "창고시설", "고물상", "식육포장처리업", "식품제조"],
        "legal_basis": "양산시 도시계획 조례 별표 및 교육환경보호구역 기준에 의거, 주거 밀집 지역 내 소음·악취·빛공해·환경오염 유발 시설은 입점이 제한됩니다."
    },
    "제2종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마시술소", "공장", "제조업", "고물상"],
        "legal_basis": "양산시 도시계획 조례에 따라 중층 주택가 및 아파트 단지 인근의 정주 환경을 해치는 공장 및 위락·유흥 업종의 입점이 차단됩니다."
    },
    "제3종일반주거지역": {
        "additional_prohibited": ["유흥주점", "위락시설", "안마시술소", "공장", "제조업"],
        "legal_basis": "양산시 도시계획 조례상 고층 공동주택 밀집 지역으로 대규모 인파 유입이나 주거 안정성을 저해하는 위락·숙박·공장 업종이 제한됩니다."
    },
    "준주거지역": {
        "additional_prohibited": ["숙박시설", "위락시설", "공장(위해물실)"],
        "legal_basis": "양산시 도시계획 조례상 주거와 상업이 혼재하는 지역이나, 학교 및 공동주택 부지 경계와의 직선거리에 따라 숙박·위락 및 소음 유발 업종 허가가 제한됩니다."
    },
    "중심상업지역": {
        "additional_prohibited": [],
        "legal_basis": "양산시 조례상 상업·업무 기능의 중심 지역으로 대부분의 업종이 허용되나, 주차장법 및 다중이용업소 소방 방재 기준을 충족해야 합니다."
    },
    "일반상업지역": {
        "additional_prohibited": [],
        "legal_basis": "양산시 조례상 일반 상업 및 업무 활동 지역으로 판매, 서비스, 위락 등 대부분의 업종이 허용됩니다."
    },
    "근린상업지역": {
        "additional_prohibited": ["유흥주점", "대형단란주점", "무도장", "카지노"],
        "legal_basis": "양산시 조례에 따라 주거지역과 인접한 근린상업지역은 야간 소음 및 주거 환경 침해 우려가 있는 대형 유흥·위락 업종의 영업 허가가 제한될 수 있습니다."
    },
    "전용공업지역": {
        "additional_prohibited": ["일반음식점", "휴게음식점", "소매점", "숙박시설", "주거시설", "판매시설", "의료시설", "교육연구시설", "학원", "오피스"],
        "legal_basis": "양산시 조례상 순수 공업 전용 구역이므로 주거 및 일반 대중 대상 상업 서비스 시설의 입주가 엄격히 차단됩니다."
    },
    "일반공업지역": {
        "additional_prohibited": ["숙박시설", "위락시설", "대규모 판매시설", "주거시설"],
        "legal_basis": "양산시 조례에 따라 공장, 지식산업센터 및 공장 지원 시설 외의 일반 대중 이용 상업시설은 허용 구역이 엄격히 제한됩니다."
    },
    "준공업지역": {
        "additional_prohibited": ["위락시설(대형)", "숙박시설"],
        "legal_basis": "양산시 조례에 따라 아파트형 공장 및 지원상가 비율에 따른 업종 제한 규정이 적용됩니다."
    },
    "보전녹지지역": {
        "additional_prohibited": ["일반음식점", "휴게음식점", "카페", "숙박시설", "공장", "제조업", "창고시설", "근린생활시설", "판매시설", "운동시설", "교육연구시설", "위락시설", "동물위탁관리업"],
        "legal_basis": "양산시 도시계획 조례에 따라 보전녹지지역은 자연환경 및 녹지 보호를 위해 원칙적으로 건축 및 영리 목적의 영업 행위가 극도로 제한됩니다."
    },
    "자연녹지지역": {
        "additional_prohibited": ["숙박시설", "공장(일부제한)", "위락시설", "창고시설(대규모)", "폐기물처리시설"],
        "legal_basis": "양산시 조례에 따라 건폐율 20%, 용적률 80% 이하가 적용되며, 성장관리방안 수립 여부 및 도로 접도 조건에 따라 허용 업종 심사가 엄격합니다."
    },
    "계획관리지역": {
        "additional_prohibited": ["숙박시설", "위락시설", "공장(배출시설 기준 초과)"],
        "legal_basis": "양산시 도시계획 조례에 따라 공장 및 제조업소 입주 시 폐수·대기 배출시설 설치 승인 대상인 경우 지정된 업종만 허용될 수 있습니다."
    }
}

# 🌟 양산시 건축 조례 상세 건축기준 및 특례 데이터베이스
yangsan_building_ordinance_rules = {
    "제1종전용주거지역": {
        "max_height_rule": "양산시 건축 조례에 따라 인접 대지경계선 및 도로와의 관계에 따른 높이 제한이 매우 엄격하며, 일조권 확보를 위한 건축물 높이 제한이 우선 적용됩니다.",
        "parking_rule": "주차장 설치 기준: 시설물 면적당 주차대수 산정 시 조례에 따른 강화된 기준이 적용될 수 있습니다."
    },
    "제2종전용주거지역": {
        "max_height_rule": "양산시 건축 조례에 따른 높이 제한 및 정북 방향 일조권 기준이 엄격하게 적용됩니다.",
        "parking_rule": "가구당 또는 면적당 법정 주차 대수 준수 필수."
    },
    "제1종일반주거지역": {
        "max_height_rule": "건축물 높이는 인접 대지경계선으로부터 정북 방향 및 채광을 위한 일조 확보 높이 제한을 받습니다.",
        "parking_rule": "다세대주택 및 근린생활시설 복합 건축 시 양산시 주차장 조례에 따른 세대당 주차 대수 확인 필수."
    },
    "제2종일반주거지역": {
        "max_height_rule": "공동주택 및 인접 대지와의 일조권 확보를 위한 높이 제한 및 층수 규정이 엄격히 적용됩니다.",
        "parking_rule": "상가 및 주택 복합 건축물 주차요건 강화 적용."
    },
    "제3종일반주거지역": {
        "max_height_rule": "고층 건축물 허가 시 가로구역별 최고 높이 지정 여부 및 대지 안의 공지 규정을 확인해야 합니다.",
        "parking_rule": "대단지 주변 상가 및 오피스텔의 경우 주차장 설치 기준이 강화됩니다."
    },
    "준주거지역": {
        "max_height_rule": "상업 업무 시설과 주거가 혼재되어 있으므로 인근 주거지역 일조권 영향에 따른 높이 완화 또는 제한 규정을 검토해야 합니다.",
        "parking_rule": "상업시설 및 부설주차장 설치 기준 엄수."
    },
    "중심상업지역": {
        "max_height_rule": "가로구역별 건축물 최고 높이 지정 구역 내에 해당하는지 확인이 필요합니다.",
        "parking_rule": "부설주차장 설치 면제 또는 완화 규정이 적용될 수 있으나 다중이용업소의 경우 자체 주차 확보가 필수입니다."
    },
    "일반상업지역": {
        "max_height_rule": "미관지구 또는 경관지구 내 건축물의 경우 높이 및 형태 제한을 받습니다.",
        "parking_rule": "상업용 시설 규모에 따른 법정 주차 대수 산정 확인."
    },
    "근린상업지역": {
        "max_height_rule": "주거지역과 인접한 경우 일조권 및 높이 제한 규정이 일부 연계 적용될 수 있습니다.",
        "parking_rule": "근린생활시설 및 유흥·위락시설 복합 시 주차요건 강화."
    },
    "전용공업지역": {
        "max_height_rule": "공장 건축물의 처마높이 및 층수 제한, 구조안전 확인 대상 건축물 기준 적용.",
        "parking_rule": "공장 면적 및 상시 고용 인원 기준 부설주차장 확보."
    },
    "일반공업지역": {
        "max_height_rule": "대형 공장 및 지식산업센터 건축 시 최고 높이 및 소방도로 확보 기준 적용.",
        "parking_rule": "화물차 주차공간 및 일반 승용차 주차구획 동시 확보."
    },
    "준공업지역": {
        "max_height_rule": "아파트형 공장 및 복합 지원시설의 높이 및 대지 안의 공지 기준 적용.",
        "parking_rule": "지원시설 비율에 따른 주차장 산정 기준 준수."
    },
    "보전녹지지역": {
        "max_height_rule": "건축물의 높이는 원칙적으로 3층 이하 또는 높이 11미터 이하로 제한되는 경우가 많습니다.",
        "parking_rule": "녹지지역 내 예외적 건축물 허용 시 법정 주차기준 적용."
    },
    "자연녹지지역": {
        "max_height_rule": "건폐율 20%, 용적률 80% 이하 및 층수 제한(일반적으로 4층 이하)이 적용됩니다.",
        "parking_rule": "건축 조례에 따른 부설주차장 설치 기준 적용."
    },
    "계획관리지역": {
        "max_height_rule": "성장관리방안 수립 구역 여부에 따라 층수 및 높이 인센티브 또는 제한이 다르게 적용됩니다.",
        "parking_rule": "계획관리지역 내 공장·창고·근린생활시설 부설주차장 기준 준수."
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
    
    # 🌟 UI 개편: 단순 문자열이 아닌 딕셔너리로 저장하여 직관적인 카드형 UI로 렌더링
    fatal_errors = []
    warnings = []
    legal_actions = []

    # 1. 용도지역 제한 검증 (국토계획법)
    if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
        prohibited_list = zoning_restrictions[zoning]["prohibited"]
        for p in prohibited_list:
            if p in target_biz or p in biz_category or (p == "위락시설" and target_biz in ["무도장 및 카지노업소", "유흥주점 (룸살롱·클럽 - 위락시설)", "단란주점"]):
                fatal_errors.append({
                    "title": f"[국토계획법 제한] '{zoning}' 지역 입점 원천 금지",
                    "content": f"국토의 계획 및 이용에 관한 법률 시행령에 따라 '{zoning}' 지역 내에서는 '{target_biz}'의 입점 및 영업이 법적으로 엄격히 금지됩니다.",
                    "solution": "용도지역 제한은 용도변경이나 기재변경으로 해결할 수 없습니다. 상업지역 등 해당 업종이 허용되는 타 용도지역 상가로 물건을 완전히 변경해야 합니다.",
                    "sub_note": None
                })

    # 🌟 2. [업종 연동형 정밀 교차 체크] 양산시 도시계획 조례 기반 세부 업종별 규제 진단
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_ordinance_rules:
        yangsan_rule = yangsan_ordinance_rules[zoning]
        
        matched_ban = False
        for add_p in yangsan_rule["additional_prohibited"]:
            if add_p in target_biz or add_p in biz_category or any(kw in target_biz for kw in add_p.split()):
                matched_ban = True
                fatal_errors.append({
                    "title": f"[양산시 도시계획 조례 위반] 계약 절대 금지",
                    "content": f"국토계획법상 가능하더라도, **양산시 도시계획 조례**에 따라 '{zoning}' 지역에서는 임차인이 선택한 **'{target_biz}'**의 입점 및 건축허가가 추가로 차단됩니다.\n\n📜 **법적 근거:** {yangsan_rule['legal_basis']}",
                    "solution": "양산시 조례 기준 위반이므로 계약 불가. 양산시 조례상 해당 업종이 허용되는 타 지역 상가를 수배하세요.",
                    "sub_note": None
                })
                break
        
        if not matched_ban:
            if zoning == "중심상업지역":
                warnings.append({
                    "title": "🏛️ [양산시 도시계획 조례 크로스 체크 - 중심상업지역 주의]",
                    "content": f"{yangsan_rule['legal_basis']}\n\n💡 중심상업지역이라 업종 자체는 허용되나, 현장 실무 시 **주차장법 대수 기준 및 소방방재 시설 기준** 미달로 인한 허가 반려 사고가 빈번하므로 건축물대장 및 소방 동선을 반드시 실측·확인하세요.",
                    "sub_note": None
                })
            else:
                legal_actions.append({
                    "title": "🏛️ [양산시 도시계획 조례 교차 검증 통과]",
                    "content": f"'{zoning}' 지역 내에서 **'{target_biz}'** 입점은 양산시 조례상 추가 제한 규정에 저촉되지 않으며 법적 근거가 확보됩니다. (근거: {yangsan_rule['legal_basis']})",
                    "sub_note": None
                })

    # 🌟 2-1. [도시계획 + 건축조례 동시교차 검증] 양산시 건축 조례상 높이, 일조권 및 주차장 기준 검토
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_building_ordinance_rules:
        bld_rule = yangsan_building_ordinance_rules[zoning]
        legal_actions.append({
            "title": "📐 [양산시 건축 조례 동시교차 검증 - 건축기준/주차장]",
            "content": f"**[높이/일조]** {bld_rule['max_height_rule']}\n\n🚗 **[주차장]** {bld_rule['parking_rule']}",
            "sub_note": None
        })

    # 3. 학교정화구역 검증 (학교보건법)
    if has_school_zone:
        if any(kw in target_biz for kw in ["유흥주점", "단란주점", "PC방", "노래연습장", "호텔", "모텔", "당구장", "청소년게임제공업", "인형뽑기방", "무도장", "카지노", "생활숙박시설"]):
            fatal_errors.append({
                "title": "[학교보건법 위반] 학교환경위생정화구역 저촉",
                "content": f"본 물건지는 학교환경위생정화구역 내에 위치하고 있어 '{target_biz}'의 영업이 원칙적으로 금지됩니다.",
                "solution": "절대정화구역인 경우 영업이 절대 불가하며, 상대정화구역인 경우 관할 양산교육지원청 학교환경위생정화위원회 심의를 통과해야만 허가 가능합니다.",
                "sub_note": None
            })

    # 4. [건축법 주용도 및 "기타용도(표시변경)" 전수 검증] 🌟 완벽한 실무 디테일 적용
    if property_type == "상가 / 일반 건축물":
        
        if "동물위탁관리업" in target_biz:
            if area >= 300.0 and bld_use != "동물관련시설":
                fatal_errors.append({
                    "title": "[건축법 위반] 면적 300㎡ 이상 동물위탁시설 용도 부적합",
                    "content": f"면적 300㎡ 이상 동물위탁시설은 주용도가 반드시 '동물관련시설'이어야 합니다. (현재 주용도: {bld_use}, 면적: {area}㎡)",
                    "solution": "건축법 제19조에 따라 건축물 용도변경 허가를 거쳐 주용도를 '동물관련시설'로 완전히 변경해야 합니다.",
                    "sub_note": "이 면적은 단순 기재변경으로 해결할 수 없으며, 정식 용도변경 설계가 필요합니다."
                })
            elif area < 300.0 and bld_use not in ["제2종근린생활시설", "동물관련시설"]:
                fatal_errors.append({
                    "title": "[건축법 위반] 300㎡ 미만 동물위탁관리업 용도 부적합",
                    "content": f"300㎡ 미만 동물위탁관리업(유치원, 호텔 등)은 주용도가 최소 '제2종근린생활시설'이어야 합니다. (현재 주용도: {bld_use})",
                    "solution": "제2종근린생활시설로 건축물 용도변경 허가(또는 신고)를 선행해야 합니다.",
                    "sub_note": "주용도가 이미 제2종근린생활시설인 경우라도, 건축물대장 우측 상단의 '기타용도(세부용도)'에 동물관련 영업 명시가 없으면 영업등록이 안 될 수 있습니다. 관할청에 **기재사항 변경(표시변경)**을 신청하여 기타용도란에 명확히 표기해 두세요."
                })
            else:
                legal_actions.append({
                    "title": "🐶 [반려동물 영업 적합 검토 가이드]",
                    "content": "건축법상 주용도 및 면적 요건은 적합합니다. ① 동물보호법에 따른 독립된 공간(이중문), ② CCTV 설치, ③ 인접 호실 민원 방지를 위한 방음·방취 공사를 특약에 명시하세요.",
                    "sub_note": "현재 대장상 2종근생이더라도 기타용도가 '사무소' 등으로 되어있다면, **'기재변경'**을 통해 동물관련 영업임을 분명히 하는 것이 훗날 민원이나 갱신 시 안전합니다."
                })
        
        elif "동물미용업" in target_biz or "동물생산업·판매업" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설"]:
                fatal_errors.append({
                    "title": "[건축법 위반] 동물미용업/펫샵 용도 부적합",
                    "content": f"동물미용업 및 펫샵은 주용도가 제1·2종근린생활시설 또는 동물관련시설이어야 합니다. (현재: {bld_use})",
                    "solution": "적합한 용도의 상가로 용도변경하거나 다른 물건을 수배하세요.",
                    "sub_note": "주용도가 1/2종 근생이 맞다면, 대장상 기타용도에 해당 업종이 명시되어 있는지 체크하고 필요시 **표시변경 신청**을 하세요."
                })
            else:
                legal_actions.append({
                    "title": "🐾 [동물미용/판매업 실무 체크]",
                    "content": "동물보호법에 따른 시설기준(격리실, 급수시설 등) 준수 여부를 확인하세요.",
                    "sub_note": "동일한 근린생활시설 내라도 기타용도가 다른 업종으로 되어있을 경우, 담당 공무원에 따라 **기재변경(표시변경)**을 요구할 수 있으니 영업등록 전 필히 대장을 확인하세요."
                })

        elif "일반음식점" in target_biz or "휴게음식점" in target_biz or "제과점" in target_biz:
            if "300㎡이상" in target_biz and bld_use != "제2종근린생활시설" and bld_use != "판매시설":
                fatal_errors.append({
                    "title": "[건축법 위반] 대형 휴게음식점 용도 부적합",
                    "content": f"바닥면적 300㎡ 이상의 휴게음식점은 '제2종근린생활시설'(또는 판매시설)이어야 합니다. (현재: {bld_use}, 면적: {area}㎡)",
                    "solution": "제2종근린생활시설로 용도변경 필수.",
                    "sub_note": "용도변경 시 기타용도란에 명확히 '휴게음식점'을 명시하여 신청하세요."
                })
            elif bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "판매시설", "숙박시설"]:
                fatal_errors.append({
                    "title": "[건축법 위반] 음식점 영업 용도 부적합",
                    "content": f"해당 음식·휴게업은 제1·2종 근린생활시설 등에 해당해야 영업허가/신고가 가능합니다. (현재: {bld_use})",
                    "solution": "건축물 용도를 근린생활시설로 변경해야 합니다.",
                    "sub_note": None
                })
            else:
                legal_actions.append({
                    "title": "🍽️ [음식점 창업 실무 꼼꼼 체크]",
                    "content": "식품위생법에 따른 위생교육 수령, 지하층인 경우 직통계단 설치 여부 및 그리스트랩 설치 의무를 확인하세요.",
                    "sub_note": "현재 건축물대장의 기타용도가 '일반음식점', '휴게음식점', '제과점' 등 실제 업종과 정확히 일치해야 가장 안전합니다. 만약 2종근생이면서 기타용도가 '사무소' 등으로 되어있다면, 관할청에 **기재사항 변경(표시변경)**을 신청하여 용도를 완벽히 일치시키세요."
                })

        elif "자동차정비공장" in target_biz or "자동차매매장" in target_biz:
            if bld_use != "자동차관련시설":
                fatal_errors.append({
                    "title": "[건축법 위반] 카센터 및 정비공장 용도 부적합",
                    "content": f"카센터 및 자동차정비·매매장은 주용도가 원칙적으로 **'자동차관련시설'**이어야 합니다. (현재: {bld_use})",
                    "solution": "자동차관련시설 용도 상가로 이전 또는 용도변경해야 합니다.",
                    "sub_note": "💡 **[카센터 특례]** 만약 바닥면적 500㎡ 미만의 카센터(부분정비)라면, 주용도가 '자동차관련시설'이 아니더라도 **'제2종근린생활시설'**이면서 기타용도(세부용도)에 **'수리점'**으로 되어 있으면 영업이 가능합니다. 주용도가 2종근생인데 다른 용도(예: 사무실)로 되어 있다면, 관할청에 **'수리점'으로 기재변경(표시변경)**을 신청해 해결할 수 있습니다."
                })
            else:
                legal_actions.append({
                    "title": "🔧 [정비공장 실무 체크]",
                    "content": "대기환경보전법 및 소음진동관리법에 따른 인허가 및 배출시설 확인 필수.",
                    "sub_note": "자동차관련시설 내에서도 기타용도가 '정비공장'인지 '매매장'인지 일치해야 하므로 대장을 꼭 확인하세요."
                })

        elif "식육포장처리업" in target_biz or "식육가공업" in target_biz or "식품제조·가공업" in target_biz or "금속가공제품 제조업" in target_biz or "인쇄소 및 출판업" in target_biz:
            if bld_use != "공장":
                if bld_use == "제2종근린생활시설" and area < 500.0:
                    warnings.append({
                        "title": "[제2종근생 소규모 제조업 입점 예외 요건 심사]",
                        "content": f"현재 주용도가 '제2종근린생활시설'이며 면적({area}㎡)이 500㎡ 미만이므로 예외적으로 소규모 공장 입점이 가능할 수 있습니다. 단, 오폐수·악취 등 환경오염 배출시설 허가 대상인 경우 입주가 원천 불가능합니다.",
                        "solution": "관할 양산시청 환경부서 및 위생과를 통해 '배출시설 비대상'임을 사전 확인받으세요.",
                        "sub_note": "💡 **[제조업 기재변경 필수]** 입점이 가능하더라도 건축물대장 기타용도(세부용도)란에 반드시 **'제조업소'**로 명시되어 있어야 공장등록 및 영업신고가 가능합니다. 만약 일반 사무소 등으로 표기되어 있다면, 배출시설 비대상 확인서를 첨부하여 관할청에 **'제조업소'로 기재변경(표시변경)**을 신청하세요."
                    })
                else:
                    fatal_errors.append({
                        "title": "[건축법 위반] 제조업/가공업 용도 부적합",
                        "content": f"해당 제조업·가공업은 주용도가 원칙적으로 **'공장'**이어야 합니다. (현재: {bld_use}, 면적: {area}㎡)",
                        "solution": "공장 또는 지식산업센터 내 공장 용도로 물건을 완전히 변경해야 합니다.",
                        "sub_note": None
                    })
            else:
                legal_actions.append({
                    "title": "🏭 [공장 내 가공 실무 체크]",
                    "content": "주용도가 '공장'으로 적합합니다. 산집법 및 환경법상 배출시설 허가 여부를 심층 검토하세요.",
                    "sub_note": "공장 내에서도 세부 업종코드에 따라 기타용도 명시가 필요할 수 있습니다."
                })

        elif "학원" in target_biz or "직업훈련소" in target_biz:
            if area >= 500.0 and bld_use not in ["교육연구시설", "제2종근린생활시설(학원)"]:
                fatal_errors.append({
                    "title": "[건축법 위반] 대형 학원 용도 부적합",
                    "content": f"바닥면적 500㎡ 이상 학원은 주용도가 반드시 '교육연구시설'이어야 합니다. (현재: {bld_use}, 면적: {area}㎡)",
                    "solution": "교육연구시설로 용도변경 필수.",
                    "sub_note": None
                })
            elif area < 500.0 and bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                fatal_errors.append({
                    "title": "[건축법 위반] 중소형 학원 용도 부적합",
                    "content": f"500㎡ 미만 학원은 제2종근린생활시설 또는 교육연구시설이어야 합니다. (현재: {bld_use})",
                    "solution": "용도변경 필요.",
                    "sub_note": "💡 **[기재변경 팁]** 현재 2종근생이더라도 기타용도가 '일반음식점' 등으로 되어있다면 교육청 학원 등록 시 반려될 수 있습니다. 학원 등록 전 기타용도를 **'학원'**으로 기재변경(표시변경) 해두는 것이 원칙입니다."
                })
            else:
                legal_actions.append({
                    "title": "📚 [학원업 실무 체크]",
                    "content": "학원의 설립·운영 및 과외교습에 관한 법률에 따른 강의실 면적(통상 60㎡~90㎡ 이상) 및 소방시설(비상구 등) 확인.",
                    "sub_note": "건축물대장상 기타용도란에 명확히 '학원' 또는 '교습소'로 표기되어 있는지 확인 후, 다를 경우 **표시변경**을 진행하세요."
                })

        elif "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz or "인형뽑기방" in target_biz:
            if bld_use not in ["제2종근린생활시설", "문화및집회시설"]:
                fatal_errors.append({
                    "title": "[건축법 위반] 게임/오락시설 용도 부적합",
                    "content": f"PC방, 노래연습장, 게임제공업은 주용도가 반드시 **'제2종근린생활시설'**(또는 문화및집회시설)이어야 합니다. (현재: {bld_use})",
                    "solution": "제2종근린생활시설로 용도변경을 선행해야 합니다.",
                    "sub_note": "용도변경 시 기타용도를 명확히 특정해야 합니다."
                })
            else:
                legal_actions.append({
                    "title": "🕹️ [PC방/게임장 실무 체크포인트]",
                    "content": "① 학교정화구역 거리 검토 필수, ② 다중이용업소 소방필증 발급 의무 엄수.",
                    "sub_note": "💡 **[기재변경 팁]** 제2종근린생활시설 내에서도 기타용도란에 '인터넷컴퓨터게임시설제공업' 등 관련 명칭이 명시되어 있지 않은 단순 상가라면, 인허가 부서 요구에 따라 해당 명칭으로 **기재사항 변경(표시변경)**을 신청하여 대장을 깔끔하게 정리하세요."
                })

        elif "세탁소" in target_biz:
            if bld_use != "제1종근린생활시설":
                fatal_errors.append({
                    "title": "[건축법 위반] 세탁소 용도 부적합",
                    "content": f"세탁소(공중위생세탁업)는 주용도가 '제1종근린생활시설'이어야 합니다. (현재: {bld_use})",
                    "solution": "제1종근생으로 용도변경 필요.",
                    "sub_note": "용도변경 시 기타용도에 '세탁소' 표기 필수."
                })
            else:
                legal_actions.append({
                    "title": "👕 [세탁소 실무 체크]",
                    "content": "드라이클리닝 장비 사용 시 대기배출시설 신고 여부 확인.",
                    "sub_note": "같은 1종근생 내(예: 소매점)에 있더라도, 위생영업 허가를 위해 관할청에 **기타용도 표시변경**을 통해 '세탁소'로 명시하는 것이 바람직합니다."
                })

        elif "일반 숙박업" in target_biz or "생활숙박시설(레지던스)" in target_biz or "펜션 및 휴양콘도미니엄" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append({
                    "title": "[건축법 위반] 숙박업 관련 용도 부적합",
                    "content": f"해당 숙박 관련 영업은 주용도가 반드시 **'숙박시설'**이어야 합니다. (현재: {bld_use})",
                    "solution": "일반 상가나 주택은 숙박시설로 용도변경이 극도로 어려우므로, 처음부터 대장상 주용도가 숙박시설인 물건만 취급하세요.",
                    "sub_note": "💡 **[세부용도 일치 필수]** 주용도가 숙박시설이라도 기타용도가 '일반숙박시설', '생활숙박시설', '관광숙박시설'로 세분화됩니다. 하시고자 하는 영업(예: 취사 가능한 레지던스 = 생활숙박시설)과 대장상 **기타용도**가 100% 일치해야 하며, 다를 경우 용도변경 수준의 까다로운 절차가 수반될 수 있습니다."
                })
            else:
                legal_actions.append({
                    "title": "🏨 [숙박시설 실무 체크]",
                    "content": "공중위생관리법상 영업신고, 소방시설완비증명서 및 위탁운영사 여부 등을 꼼꼼히 확인하세요.",
                    "sub_note": "건축물대장상 기타용도가 본인이 운영하려는 세부 숙박 카테고리와 정확히 일치하는지 재차 확인하세요."
                })

        elif "외국인관광 도시민박업" in target_biz:
            if bld_use not in ["단독/다세대/아파트(주택류)"]:
                fatal_errors.append({
                    "title": "[관광진흥법 위반] 도시민박업 주택 요건 부적합",
                    "content": f"외국인관광 도시민박업은 실제 거주하는 주택(단독·다세대·연립·아파트)에서만 가능합니다. (현재: {bld_use})",
                    "solution": "건축물대장상 용도가 상가나 오피스텔이 아닌 '주택'인 물건으로 변경하세요.",
                    "sub_note": "오피스텔은 업무시설이므로 절대 불가합니다."
                })
            else:
                legal_actions.append({
                    "title": "🏡 [외국인관광 도시민박업 체크]",
                    "content": "도시민박업 지정 신청 시 소방안전기준 및 거주 요건, 외국어 안내 서비스 구비를 증빙하세요.",
                    "sub_note": None
                })
        
        # --- 기타 범용 근린생활/업무시설 체크 (미용업, 의원, 사무소 등) ---
        else:
            required_use = "제1/2종근린생활시설 등"
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "업무시설", "판매시설", "의료시설", "운동시설", "자원순환관련시설", "창고시설", "위락시설"]:
                 fatal_errors.append({
                    "title": f"[건축법 위반] {target_biz} 용도 부적합",
                    "content": f"해당 업종은 현재 건축물 주용도({bld_use})에 적합하지 않을 확률이 매우 높습니다.",
                    "solution": "업종에 맞는 적합한 주용도로 용도변경을 선행하세요.",
                    "sub_note": "근린생활시설로 변경 시 기타용도란에 실제 입점 업종을 명확히 기재하세요."
                })
            else:
                legal_actions.append({
                    "title": f"✅ [{target_biz} 입점 기본 적합 검토]",
                    "content": f"입력된 건축물 주용도({bld_use}) 및 면적({area}㎡) 기준 일반적인 법적 요건에 부합합니다. 양산시 조례 및 개별 지침을 최종 확인하세요.",
                    "sub_note": "💡 **[실무 핵심: 기타용도 일치화]** 주용도가 근린생활시설로 맞더라도, 건축물대장 우측 상단의 **'기타용도(세부용도)'**란에 입점하시려는 업종명(예: 의원, 사무소, 미용업 등)이 텍스트로 정확히 기재되어 있어야 관련 관청의 인허가(영업증 발급 등)가 반려되지 않습니다. 만약 다르게 기재되어 있다면, 동일 시설군 내이므로 쉽게 **'건축물대장 기재사항 변경(표시변경) 신청'**을 통해 세부 용도를 맞춘 뒤 영업신고를 진행하세요."
                })

    else: # 산업단지 내 공장
        if bld_use != "공장":
            fatal_errors.append({
                "title": "[산집법 치명적 결격] 산업단지 건축물 주용도 부적합",
                "content": f"산업집적활성화 및 공장설립에 관한 법률(산집법)에 따라 산단 내 공장 등록을 위해서는 주용도가 무조건 **'공장'**이어야 합니다. (현재 주용도: {bld_use})",
                "solution": "다른 공장 물건을 선택해야 합니다. 산단 내에서는 임의 용도변경이 불가합니다.",
                "sub_note": None
            })
        
        if selected_parcel_row is not None:
            input_val = target_biz.strip().upper()
            code_match = input_val in auto_detected_code.upper() or any(c.strip() in input_val for c in auto_detected_code.split(','))
            name_match = input_val in auto_detected_name.upper() or any(w in auto_detected_name for w in target_biz.split())
            
            if target_biz and not code_match and not name_match:
                fatal_errors.append({
                    "title": "[산단 관리기본계획 위반] 허용 업종코드 불일치",
                    "content": f"해당 지번의 한국산업단지공단(KICOX) 관리기본계획상 허용 업종코드(`{auto_detected_code}`)에 임차인 희망 업종('{target_biz}')이 포함되지 않습니다.",
                    "solution": "해당 지번에서는 입주계약 체결이 불가능합니다. 코드가 맞는 다른 필지를 찾으세요.",
                    "sub_note": None
                })
            else:
                legal_actions.append({
                    "title": "✅ [산단 입주계약 적합]",
                    "content": "한국산업단지공단 관리기본계획상 허용 업종 코드 및 명칭에 부합합니다.",
                    "sub_note": None
                })


    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 1. 상세 법적 리포트", "💰 2. 원인자부담금", "⚡ 3. 전기용량(승압)", "🧯 4. 소방·환경·위생", "🚽 5. 정화조·오수"
    ])

    with tab1:
        st.subheader("📋 공법상 적합성 및 상세 법적 리포트")
        st.info("💡 **[중개사무소 실무 필독]** 건축물대장상 **주용도**뿐만 아니라 **'기타용도(세부용도)'**의 일치 여부가 실무 인허가에서 매우 중요합니다. 동일한 시설군(예: 2종근생 내)이라도 세부 업종이 다르다면 관할청에 **'건축물대장 기재사항 변경(표시변경)'**을 신청하여 용도를 완벽히 맞추는 것이 사고를 예방하는 지름길입니다.")
        st.markdown("---")
        
        # ❌ 에러 처리 (카드형 UI)
        if fatal_errors:
            st.markdown("### ❌ [계약 불가 / 중개사고 고위험 사유]")
            for err in fatal_errors:
                with st.container():
                    st.error(f"🚨 **{err['title']}**\n\n{err['content']}")
                    st.markdown(f"💡 **해결 대안:** {err['solution']}")
                    if err.get('sub_note'):
                        st.info(f"🔎 **기타용도 / 기재변경 실무 팁:** {err['sub_note']}")
                    st.markdown("
                    # ⚠️ 경고 처리
    if warnings:
        st.markdown("### ⚠️ [주의 및 필수 검토 사항]")
        for w in warnings:
            with st.container():
                st.warning(f"**{w['title']}**\n\n{w['content']}")
                if w.get('solution'):
                    st.markdown(f"💡 **해결 대안:** {w['solution']}")
                if w.get('sub_note'):
                    st.info(f"🔎 **기타용도 / 기재변경 실무 팁:** {w['sub_note']}")
                st.markdown("
                # 🛠️ 실무 가이드 (Expander 활용)
    if legal_actions:
        st.markdown("### 🛠️ [실무 법적 조치 및 상세 가이드]")
        for act in legal_actions:
            with st.expander(f"📌 {act['title']}", expanded=True):
                st.write(act['content'])
                if act.get('sub_note'):
                    st.info(f"🔎 **기타용도 / 기재변경 실무 팁:** {act['sub_note']}")

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
