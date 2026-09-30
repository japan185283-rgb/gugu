import streamlit as st
import pandas as pd
import os

# 1. 페이지 기본 설정 (세로형 중심 배치)
st.set_page_config(page_title="부동산 전 업종 완벽 통합 진단 시뮬레이터 Pro", layout="centered")

# 🎨 [UI/UX 개선] 상세 리포트 텍스트 가독성(검정색 고대비 및 카드형 디자인)을 위한 커스텀 CSS 주입
st.markdown("""

""", unsafe_allow_html=True)

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

# 🏗️ 건축물대장 주용도 및 세부 괄호 표기 데이터베이스 (전 용도 세분화 확장)
general_building_uses = {
    "제1종근린생활시설": [
        "제1종근린생활시설 (일반 소매점·휴게음식점 300㎡미만)",
        "제1종근린생활시설 (이용원·미용원·세탁소)",
        "제1종근린생활시설 (탁구장·체육도장)",
        "제1종근린생활시설 (의원·치과의원·한의원·약국)",
        "제1종근린생활시설 (기타 세부 표기 없음)"
    ],
    "제2종근린생활시설": [
        "제2종근린생활시설 (대분류만 해당 / 세부용도 표기 없음)",
        "제2종근린생활시설 (제조업소)",
        "제2종근린생활시설 (수리점)",
        "제2종근린생활시설 (일반음식점·휴게음식점·제과점)",
        "제2종근린생활시설 (학원·독서실·교습소)",
        "제2종근린생활시설 (공인중개사사무소·사진관·금융업소)",
        "제2종근린생활시설 (PC방·노래연습장·당구장·청소년게임제공업)"
    ],
    "문화및집회시설": [
        "문화및집회시설 (공연장·관람장·전시장)",
        "문화및집회시설 (영화상영관·예식장·집회장)"
    ],
    "판매시설": [
        "판매시설 (도매시장·소매시장)",
        "판매시설 (백화점·쇼핑센터·대형마트)"
    ],
    "운수시설": [
        "운수시설 (여객자동차터미널·철도시설)",
        "운수시설 (공항·항만·화물터미널)"
    ],
    "의료시설": [
        "의료시설 (병원·종합병원·치과병원·한방병원)",
        "의료시설 (정신병원·요양병원)"
    ],
    "교육연구시설": [
        "교육연구시설 (학교·교육원·직업훈련소)",
        "교육연구시설 (연구소·도서관)"
    ],
    "운동시설": [
        "운동시설 (체육관·수영장)",
        "운동시설 (체력단련장·볼링장·테니스장)"
    ],
    "업무시설": [
        "업무시설 (공공업무시설)",
        "업무시설 (일반업무시설·일반사무소)",
        "업무시설 (오피스텔)"
    ],
    "숙박시설": [
        "숙박시설 (일반호텔·모텔·여관·펜션)",
        "숙박시설 (생활숙박시설·레지던스)",
        "숙박시설 (휴양콘도미니엄)"
    ],
    "위락시설": [
        "위락시설 (유흥주점·단란주점)",
        "위락시설 (무도장·카지노업소)"
    ],
    "공장": [
        "공장 (일반 제조공장)",
        "공장 (지식산업센터·아파트형공장)",
        "공장 (식품·축산물가공업소)"
    ],
    "창고시설": [
        "창고시설 (일반창고·보관창고)",
        "창고시설 (냉장·냉동창고·물류터미널)"
    ],
    "자동차관련시설": [
        "자동차관련시설 (주차장·세차장)",
        "자동차관련시설 (정비공장·수리점·매매장)"
    ],
    "동물관련시설": [
        "동물관련시설 (동물장묘업·도축장)",
        "동물관련시설 (대규모 동물위탁관리·생산업)"
    ],
    "자원순환관련시설": [
        "자원순환관련시설 (폐기물재활용·처분시설)",
        "자원순환관련시설 (고물상·폐기물보관시설)"
    ],
    "단독/다세대/아파트(주택류)": [
        "단독/다세대/아파트 (단독주택·다가구주택)",
        "단독/다세대/아파트 (다세대주택·연립주택·아파트)"
    ]
}

# 용도지역별 기본 금지 업종 키워드 맵 (국토계획법 시행령 별표)
zoning_restrictions = {
    "제1종전용주거지역": {"prohibited": ["음식점", "휴게음식점", "숙박", "공장", "제조업", "판매", "PC방", "노래", "축산물", "세차장", "창고", "위락", "무도장", "카지노", "청소년게임", "생활숙박", "펜션", "콘도", "학원", "사무소", "미용", "세탁"]},
    "제2종전용주거지역": {"prohibited": ["일반음식점", "휴게음식점", "숙박", "공장", "제조업", "축산물", "위락", "무도장", "카지노", "청소년게임", "생활숙박", "펜션", "콘도"]},
    "제1종일반주거지역": {"prohibited": ["숙박", "위락", "무도장", "카지노", "공장", "제조업", "세차장", "창고", "생활숙박", "펜션", "콘도"]},
    "제2종일반주거지역": {"prohibited": ["숙박", "위락", "무도장", "카지노", "공장", "제조업", "창고", "생활숙박", "펜션", "콘도"]},
    "제3종일반주거지역": {"prohibited": ["숙박", "위락", "무도장", "카지노", "공장", "제조업", "생활숙박", "펜션", "콘도"]},
    "준주거지역": {"prohibited": ["위락시설(일부제한)", "무도장", "카지노"]},
    "중심상업지역": {"prohibited": []},
    "일반상업지역": {"prohibited": []},
    "근린상업지역": {"prohibited": ["무도장", "카지노"]},
    "전용공업지역": {"prohibited": ["주거", "판매", "근린생활", "의료", "위락", "무도장", "카지노", "숙박", "생활숙박", "음식점", "학원"]},
    "일반공업지역": {"prohibited": ["주거", "위락", "무도장", "카지노", "숙박", "생활숙박"]},
    "준공업지역": {"prohibited": ["위락(대형)", "무도장"]},
    "보전녹지지역": {"prohibited": ["근린생활", "공장", "제조업", "숙박", "음식점", "카페", "축산물", "세차장", "창고", "위락", "무도장", "카지노", "청소년게임", "생활숙박", "운동", "교육", "동물"]},
    "자연녹지지역": {"prohibited": ["숙박", "위락", "무도장", "카지노", "생활숙박", "폐기물"]},
    "계획관리지역": {"prohibited": ["위락", "무도장", "카지노"]}
}

# 양산시 도시계획 조례 세부 제한 업종 맵
yangsan_ordinance_rules = {
    "제1종전용주거지역": {
        "additional_prohibited": ["음식점", "카페", "제과점", "골프", "안마", "학원", "PC방", "노래", "사무소", "식육", "미용", "세탁소", "동물", "공인중개사", "병원", "의원"],
        "legal_basis": "양산시 도시계획 조례에 따라 제1종전용주거지역 내에서는 단독주택 및 양호한 주거환경에 지장을 주지 않는 일부 부수시설 외의 일반 영업·상업·근린생활시설 설치가 엄격히 금지됩니다."
    },
    "제2종전용주거지역": {
        "additional_prohibited": ["음식점", "카페", "제과점", "골프", "안마", "단란주점", "유흥주점", "PC방", "노래", "동물"],
        "legal_basis": "양산시 도시계획 조례에 따라 공동주택 중심의 양호한 주거환경 보호를 위해 소음, 악취, 유해물질 또는 방문객 밀집을 유발하는 상업 업종의 입점이 제한됩니다."
    },
    "제1종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마", "골프", "공장", "제조업", "세차장", "창고", "고물상", "식육", "식품제조"],
        "legal_basis": "양산시 도시계획 조례 별표 및 교육환경보호구역 기준에 의거, 주거 밀집 지역 내 소음·악취·빛공해·환경오염 유발 시설은 입점이 제한됩니다."
    },
    "제2종일반주거지역": {
        "additional_prohibited": ["단란주점", "유흥주점", "안마", "공장", "제조업", "고물상"],
        "legal_basis": "양산시 도시계획 조례에 따라 중층 주택가 및 아파트 단지 인근의 정주 환경을 해치는 공장 및 위락·유흥 업종의 입점이 차단됩니다."
    },
    "제3종일반주거지역": {
        "additional_prohibited": ["유흥주점", "위락", "안마", "공장", "제조업"],
        "legal_basis": "양산시 도시계획 조례상 고층 공동주택 밀집 지역으로 대규모 인파 유입이나 주거 안정성을 저해하는 위락·숙박·공장 업종이 제한됩니다."
    },
    "준주거지역": {
        "additional_prohibited": ["숙박", "위락"],
        "legal_basis": "양산시 도시계획 조례상 주거와 상업이 혼재하는 지역이나, 숙박·위락 및 소음 유발 업종 허가가 제한됩니다."
    },
    "중심상업지역": {"additional_prohibited": [], "legal_basis": "양산시 조례상 상업·업무 기능의 중심 지역으로 대부분 허용."},
    "일반상업지역": {"additional_prohibited": [], "legal_basis": "양산시 조례상 일반 상업 및 업무 활동 지역."},
    "근린상업지역": {
        "additional_prohibited": ["유흥주점", "무도장", "카지노"],
        "legal_basis": "양산시 조례에 따라 주거지역과 인접한 근린상업지역은 야간 소음 및 주거 환경 침해 우려가 있는 대형 유흥·위락 업종의 영업 허가가 제한될 수 있습니다."
    },
    "전용공업지역": {
        "additional_prohibited": ["음식점", "휴게음식점", "소매점", "숙박", "주거", "판매", "의료", "교육", "학원", "오피스"],
        "legal_basis": "양산시 조례상 순수 공업 전용 구역이므로 주거 및 일반 대중 대상 상업 서비스 시설의 입주가 엄격히 차단됩니다."
    },
    "일반공업지역": {
        "additional_prohibited": ["숙박", "위락", "주거"],
        "legal_basis": "양산시 조례에 따라 공장 및 공장 지원 시설 외의 일반 대중 이용 상업시설은 허용 구역이 엄격히 제한됩니다."
    },
    "준공업지역": {
        "additional_prohibited": ["위락", "숙박"],
        "legal_basis": "양산시 조례에 따라 아파트형 공장 및 지원상가 비율에 따른 업종 제한 규정이 적용됩니다."
    },
    "보전녹지지역": {
        "additional_prohibited": ["음식점", "휴게음식점", "카페", "숙박", "공장", "제조업", "창고", "근린생활", "판매", "운동", "교육", "위락", "동물"],
        "legal_basis": "양산시 도시계획 조례에 따라 보전녹지지역은 자연환경 및 녹지 보호를 위해 원칙적으로 건축 및 영업 행위가 엄격히 제한됩니다."
    },
    "자연녹지지역": {
        "additional_prohibited": ["숙박", "공장", "위락", "창고", "폐기물"],
        "legal_basis": "양산시 조례에 따라 건폐율 20%, 용적률 80% 이하가 적용됩니다."
    },
    "계획관리지역": {
        "additional_prohibited": ["숙박", "위락"],
        "legal_basis": "양산시 도시계획 조례에 따라 공장 및 제조업소 입주 시 배출시설 설치 승인 대상인 경우 지정된 업종만 허용될 수 있습니다."
    }
}

yangsan_building_ordinance_rules = {
    "제1종전용주거지역": {"max_height_rule": "인접 대지경계선 및 도로와의 관계에 따른 높이 제한 엄격 적용.", "parking_rule": "주차장 설치 강화 기준 적용."},
    "제2종전용주거지역": {"max_height_rule": "정북 방향 일조권 기준 엄격 적용.", "parking_rule": "가구당 법정 주차 대수 준수."},
    "제1종일반주거지역": {"max_height_rule": "채광을 위한 일조 확보 높이 제한.", "parking_rule": "다세대/근생 복합 건축 시 세대당 주차 대수 확인."},
    "제2종일반주거지역": {"max_height_rule": "인접 대지와의 일조권 확보 및 층수 규정.", "parking_rule": "상가/주택 복합 건축물 주차요건 강화."},
    "제3종일반주거지역": {"max_height_rule": "고층 건축물 가로구역별 최고 높이 지정 확인.", "parking_rule": "대단지 주변 상가 주차장 설치 기준 강화."},
    "준주거지역": {"max_height_rule": "인근 주거지역 일조권 영향에 따른 높이 검토.", "parking_rule": "상업시설 부설주차장 설치 기준 준수."},
    "중심상업지역": {"max_height_rule": "가로구역별 건축물 최고 높이 지정 구역 확인.", "parking_rule": "다중이용업소 자체 주차 확보 필수."},
    "일반상업지역": {"max_height_rule": "미관지구/경관지구 내 높이 및 형태 제한.", "parking_rule": "상업용 시설 규모별 법정 주차 대수 산정."},
    "근린상업지역": {"max_height_rule": "주거지역 연계 일조권 및 높이 제한.", "parking_rule": "근린생활 및 유흥·위락 복합 시 주차 강화."},
    "전용공업지역": {"max_height_rule": "공장 처마높이 및 층수 제한.", "parking_rule": "공장 면적 및 고용 인원 기준 부설주차장."},
    "일반공업지역": {"max_height_rule": "대형 공장 최고 높이 및 소방도로 확보.", "parking_rule": "화물차 및 승용차 주차구획 동시 확보."},
    "준공업지역": {"max_height_rule": "아파트형 공장 대지 안의 공지 기준.", "parking_rule": "지원시설 비율에 따른 주차장 산정."},
    "보전녹지지역": {"max_height_rule": "3층 이하 또는 높이 11미터 이하 제한.", "parking_rule": "녹지지역 내 예외적 건축물 법정 주차기준."},
    "자연녹지지역": {"max_height_rule": "건폐율 20%, 용적률 80%, 4층 이하 제한.", "parking_rule": "건축 조례 부설주차장 설치 기준 적용."},
    "계획관리지역": {"max_height_rule": "성장관리방안 구역 여부 확인.", "parking_rule": "공장·창고·근생 부설주차장 기준 준수."}
}

st.markdown("---")
st.subheader("📝 2. 대상 부동산 기본 팩트 입력")

property_type = st.radio("중개 대상물 형태 선택", ["상가 / 일반 건축물", "산업단지 내 공장 (지번 조회)"])
zoning = st.selectbox("토지 용도지역 (국토계획법)", list(zoning_restrictions.keys()))

col_u1, col_u2 = st.columns(2)
with col_u1:
    bld_category = st.selectbox("건축물대장 주용도 대분류 (건축법 시행령 별표1)", list(general_building_uses.keys()))
with col_u2:
    bld_use = st.selectbox("건축물대장 세부 용도 및 괄호 표기 선택", general_building_uses[bld_category])

col_f1, col_f2 = st.columns(2)
with col_f1:
    floor_num = st.number_input("건물 층수 (지하층은 음수 입력)", min_value=-5, max_value=50, value=1)
with col_f2:
    area = st.number_input("바닥면적 / 전용면적 (㎡)", min_value=0.0, value=100.0, help="해당 업종이 실제로 사용할 면적")

has_school_zone = st.checkbox("🎓 학교환경위생정화구역(절대·상대정화구역) 저촉 여부 확인", value=False)

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
            st.warning("⚠ 일치하는 지번이 없습니다. 검색어를 다시 확인해주세요.")
    else:
        st.warning("⚠️ 산단 데이터 파일이 로드되지 않았습니다.")

st.markdown("---")
st.subheader("🎯 3. 임차인 희망 업종 및 설비 조건 선택")

comprehensive_biz_dict = {
    "🐶 반려동물 관련 영업": [
        "동물위탁관리업", "동물미용업", "동물생산업·판매업", "동물장묘업 및 동물병원"
    ],
    "🍽️ 일반 음식점 및 카페·디저트": [
        "일반음식점", "휴게음식점", "제과점 및 아이스크림 전문점", "식육판매업"
    ],
    "🍺 주점 및 유흥·위락": [
        "일반주점·맥주집", "유흥주점", "단란주점", "무도장 및 카지노업소"
    ],
    "🥩 제조업 및 축산물·식품가공": [
        "식육포장처리업", "식육가공업", "식품제조·가공업", "금속가공제품 제조업", "인쇄소 및 출판업"
    ],
    "📦 창고, 물류 및 자원순환": [
        "일반 물류창고", "냉장·냉동창고", "택배 대리점 및 집화시설", "고물상 및 폐기물재활용시설"
    ],
    "🏥 병의원 및 의료시설": [
        "병원", "치과의원", "한의원", "요양병원", "동물병원"
    ],
    "🏋️ 스포츠, 레저 및 운동시설": [
        "피트니스·헬스장", "스크린골프장", "당구장", "수영장 및 볼링장"
    ],
    "📚 교육, 연구 및 청소년시설": [
        "학원", "독서실 및 스터디카페", "직업훈련소", "PC방", "노래연습장", "청소년게임제공업"
    ],
    "🚗 자동차 및 환경·세차장": [
        "세차장", "자동차정비공장", "자동차매매장", "주차장업"
    ],
    "🏡 숙박 및 공유숙박": [
        "일반 숙박업", "생활숙박시설", "오피스텔 에어비앤비", "외국인관광 도시민박업", "펜션 및 휴양콘도미니엄"
    ],
    "💄 뷰티, 공중위생 및 서비스": [
        "일반미용업·헤어샵", "네일아트 및 피부미용실", "목욕장업", "세탁소"
    ],
    "💼 일반 오피스 및 전문서비스": [
        "공인중개사사무소", "일반 법무사·행정사·세무사 사무소", "일반 기업체 오피스", "금융업소"
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

    # 1. 국토계획법 용도지역 검증 (엄격한 키워드 매칭)
    if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
        prohibited_list = zoning_restrictions[zoning]["prohibited"]
        for p in prohibited_list:
            # 업종 명칭이나 대분류에 금지 키워드가 정확히 포함될 때만 차단
            if p in target_biz or p in biz_category:
                fatal_errors.append(
                    f"[국토계획법 제76조 위반] '{zoning}' 지역에서는 해당 법령에 따라 '{target_biz}'의 입점 및 영업이 원천 금지되어 있습니다. "
                    f"💡 **해결 대안:** 상업지역 등 해당 업종이 허용되는 다른 입지로 물건을 변경해야 합니다."
                )
                break

    # 2. 양산시 도시계획 조례 교차 진단
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_ordinance_rules:
        yangsan_rule = yangsan_ordinance_rules[zoning]
        matched_ban = False
        for add_p in yangsan_rule["additional_prohibited"]:
            if add_p in target_biz or add_p in biz_category:
                matched_ban = True
                fatal_errors.append(
                    f"[양산시 도시계획 조례 규제 위반 / 계약 절대금지] **양산시 도시계획 조례**에 따라 "
                    f"'{zoning}' 지역에서는 **'{target_biz}'**의 입점 및 건축허가가 법적으로 엄격히 금지됩니다. "
                    f"📜 **법적 근거:** {yangsan_rule['legal_basis']} "
                    f"💡 **해결 대안:** 양산시 조례 기준 위반이므로 본 물건은 계약할 수 없으며, 타 용도지역 상가 물건을 검토하세요."
                )
                break
        
        if not matched_ban:
            legal_actions.append(
                f"🏛️ **[양산시 도시계획 조례 교차 검증 통과]** '{zoning}' 지역 내에서 **'{target_biz}'** 입점은 양산시 조례상 추가 제한 규정에 저촉되지 않습니다."
            )

    # 2-1. 양산시 건축 조례 검토
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_building_ordinance_rules:
        bld_rule = yangsan_building_ordinance_rules[zoning]
        legal_actions.append(f"📐 **[양산시 건축 조례 - 높이 및 일조]** {bld_rule['max_height_rule']}")
        legal_actions.append(f"🚗 **[양산시 건축 조례 - 주차장 기준]** {bld_rule['parking_rule']}")

    # 3. 학교정화구역 검증
    if has_school_zone:
        if any(kw in target_biz for kw in ["유흥주점", "단란주점", "PC방", "노래연습장", "숙박", "당구장", "청소년게임제공업", "무도장", "카지노"]):
            fatal_errors.append(
                f"[학교보건법 제6조 위반] 본 물건지는 학교환경위생정화구역 내에 위치하여 '{target_biz}' 영업이 제한됩니다. "
                f"💡 **해결 대안:** 상대정화구역인 경우 관할 교육지원청 심의 필수, 절대정화구역인 경우 영업 불가."
            )

    # 4. 건축물대장 주용도 및 세부 괄호 표기 검증 (핵심 수정 영역)
    if property_type == "상가 / 일반 건축물":
        
        # 세탁소 검증
        if "세탁소" in target_biz:
            if "제1종근린생활시설" not in bld_category:
                warnings.append(
                    f"⚠️ **[조건부 허용 / 용도변경 필요]** 현재 건축물대장 주용도가 **'{bld_category}'**입니다. 세탁소는 제1종근생이므로 관할 관청에 **용도변경(표시변경)**을 신청하여 입점해야 합니다."
                )
            else:
                legal_actions.append("👕 **[세탁소 적합]** 주용도가 제1종근린생활시설로 적합합니다.")

        # 세차장 / 자동차관련시설 검증
        elif "세차장" in target_biz or "자동차정비공장" in target_biz:
            if "자동차관련시설" not in bld_category:
                fatal_errors.append(
                    f"[건축법 위반 / 주용도 불일치] '{target_biz}'은(는) 반드시 건축물대장 주용도가 **'자동차관련시설'**이어야 합니다. (현재 주용도: {bld_category}) "
                    f"💡 **해결 대안:** 주거지역 등에서는 용도변경 자체가 불가하므로, 상업/공업지역 내 자동차관련시설 허가 건물을 구하셔야 합니다."
                )
            else:
                legal_actions.append("🚗 **[자동차관련시설 적합]** 주용도가 일치합니다.")

        # 제조업소 / 수리점 / 식품가공 등 검증
        elif any(kw in target_biz for kw in ["식육포장처리업", "식육가공업", "식품제조·가공업", "금속가공제품 제조업", "인쇄소 및 출판업"]):
            is_explicit_mf = ("제조업소" in bld_use) or ("수리점" in bld_use)
            
            if bld_category == "제2종근린생활시설" and not is_explicit_mf and area < 500.0:
                warnings.append(
                    f"⚠️ **[조건부 허용 / 세부 괄호 표기 변경 필요]** "
                    f"현재 건축물대장이 단순 `제2종근린생활시설(대분류)` 상태이므로 이대로는 입점이 불가할 수 있습니다. "
                    f"💡 **[실무 팁]** 건축물대장에 **`제2종근린생활시설 (제조업소)`** 또는 **`(수리점)`** 세부 괄호 표기 변경(표시변경)을 진행하고 면적 500㎡ 미만을 충족하면 **합법적 입점이 가능해집니다!**"
                )
            elif is_explicit_mf and area < 500.0:
                legal_actions.append(f"✅ **[세부 용도 일치]** 건축물대장 세부 표기가 **'{bld_use}'**로 되어 있어 500㎡ 미만 요건 충족 시 즉시 영업 가능합니다.")
            elif bld_category != "공장" and not is_explicit_mf:
                warnings.append(
                    f"[주용도 검토 필요] 해당 제조업은 '공장' 또는 세부 괄호가 포함된 근생이어야 합니다. (현재: {bld_category} - {bld_use})"
                )
            else:
                legal_actions.append("🏭 **[공장/제조시설 적합]** 주용도 요건에 부합합니다.")

        # 위락시설 검증
        elif "유흥주점" in target_biz or "단란주점" in target_biz or "무도장 및 카지노업소" in target_biz:
            if bld_category != "위락시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 불가] 유흥·단란주점 및 무도장·카지노는 주용도가 반드시 **'위락시설'**이어야 합니다. (현재: {bld_category})"
                )
            else:
                legal_actions.append("🍺 **[위락시설 적합]** 소방안전시설완비증명서 발급 여부 확인 필요.")

        # 숙박시설 검증
        elif "일반 숙박업" in target_biz or "생활숙박시설" in target_biz:
            if bld_category != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 불가] 숙박시설은 주용도가 반드시 **'숙박시설'**이어야 합니다. (현재: {bld_category})"
                )
            else:
                legal_actions.append("🏨 **[숙박시설 적합]** 숙박업 영업신고 대상.")

        elif "오피스텔 에어비앤비" in target_biz:
            fatal_errors.append("[불법 영업] 오피스텔은 업무시설이므로 공중위생관리법상 숙박업 합법 등록이 원천 불가합니다.")

        elif "외국인관광 도시민박업" in target_biz:
            if bld_category != "단독/다세대/아파트(주택류)":
                fatal_errors.append("[관광진흥법 위반] 도시민박업은 실제 거주하는 주택(단독·다세대·연립·아파트)에서만 가능합니다.")
            else:
                legal_actions.append("🏡 **[도시민박업 주택 요건 적합]**")

        else:
            legal_actions.append(f"✅ **[{target_biz} 적합성 검토 완료]** 대분류({bld_category}), 세부 표기({bld_use}) 및 면적 요건에 부합합니다.")

    else: # 산단 공장
        if bld_category != "공장":
            fatal_errors.append(
                f"치명적 결격: 산단 내 공장 등록을 위해서는 주용도가 무조건 **'공장'**이어야 합니다. (현재: {bld_category})"
            )
        if selected_parcel_row is not None:
            input_val = target_biz.strip().upper()
            code_match = input_val in auto_detected_code.upper() or any(c.strip() in input_val for c in auto_detected_code.split(','))
            name_match = input_val in auto_detected_name.upper() or any(w in auto_detected_name for w in target_biz.split())
            if target_biz and not code_match and not name_match:
                fatal_errors.append(
                    f"산단 관리기본계획 위반: 해당 지번의 허용 업종코드(`{auto_detected_code}`)에 임차인 희망 업종('{target_biz}')이 포함되지 않습니다."
                )
            else:
                legal_actions.append("✅ **산단 입주계약 적합:** 허용 업종 코드 및 명칭에 부합합니다.")

    # 탭 구성 출력
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 1. 상세 법적 리포트", "💰 2. 원인자부담금", "⚡ 3. 전기용량(승압)", "🧯 4. 소방·환경·위생", "🚽 5. 정화조·오수"
    ])

    with tab1:
        st.subheader("📋 공법상 적합성 및 상세 법적 리포트")
        st.markdown("---")
        
        if fatal_errors:
            st.error("### ❌ [계약 절대 금지 / 중개사고 고위험 사유]")
            for err in fatal_errors: 
                st.markdown(f"- **{err}**")
            st.markdown("---")
        else:
            st.success("### ✅ [공법상 입주 및 영업 기본 요건 적합]")
            st.markdown("---")
            
        if warnings:
            st.warning("### ⚠️ [주의 및 조건부 허용 가이드 / 세부 용도 변경 팁]")
            for w in warnings: 
                st.markdown(f"- {w}")
            st.markdown("---")
            
        if legal_actions:
            st.markdown("### 🛠 [실무 법적 조치 및 상세 가이드]")
            for act in legal_actions: 
                st.markdown(f"- {act}")

    with tab2:
        st.subheader("💰 상하수도 원인자부담금 시뮬레이션")
        unit_discharge_rates = {
            "동물위탁관리업": 0.08, "식육포장처리업": 0.20, "세차장": 0.35, "목욕장업": 0.30,
            "일반음식점": 0.18, "피트니스·헬스장": 0.12, "유흥주점": 0.25, "무도장 및 카지노업소": 0.25,
            "청소년게임제공업": 0.05, "생활숙박시설": 0.20, "펜션 및 휴양콘도미니엄": 0.20, "세탁소": 0.15,
        }
        rate = unit_discharge_rates.get(target_biz, 0.05)
        estimated_discharge = area * rate
        est_water_fee = estimated_discharge * 1823000
        est_sewage_fee = (estimated_discharge * 1910000) if estimated_discharge >= 10 else 0

        st.markdown(f"- 추정 일일 오수량: **{estimated_discharge:.1f} 톤(㎥/일)** (면적 {area}㎡ 기준)")
        st.markdown(f"- **상수도원인자부담금:** 약 **{est_water_fee:,.0f} 원**")
        if estimated_discharge >= 10:
            st.markdown(f"- **하수도원인자부담금:** 약 **{est_sewage_fee:,.0f} 원** *(10톤 이상 전량 부과)*")
        else:
            st.markdown("- **하수도원인자부담금:** ✅ **면제 대상** *(10톤 미만)*")
        st.info("💡 양산시 수도조례에 따라 실제 부과 금액은 상이할 수 있습니다.")

    with tab3:
        st.subheader("⚡ 현실적인 계약전력 및 승압 진단")
        if "피트니스" in target_biz or "헬스장" in target_biz or "제조업" in target_biz or "세차장" in target_biz:
            base_kw, kw_per_sqm, max_cap = 15.0, 0.08, 60.0
        elif "음식점" in target_biz or "카페" in target_biz or "제과점" in target_biz or "세탁소" in target_biz:
            base_kw, kw_per_sqm, max_cap = 15.0, 0.06, 50.0
        else:
            base_kw, kw_per_sqm, max_cap = 5.0, 0.02, 25.0

        req_power = min(base_kw + (area * kw_per_sqm), max_cap)
        power_diff = req_power - current_power
        est_electric_fee = max(0, power_diff) * 110000

        st.markdown(f"- **현재 건물 계약전력:** `{current_power} kW`")
        st.markdown(f"- **권장 소요전력:** 약 `{req_power:.1f} kW`")

        if power_diff > 0:
            st.warning(f"⚠️ **[승압 필요]** 약 `{power_diff:.1f} kW` 추가 필요 (예상 표준시설부담금: 약 {est_electric_fee:,.0f}원)")
        else:
            st.success("✅ **[전기 용량 충분]**")

    with tab4:
        st.subheader("🧯 소방, 환경 및 위생 규제 요건 상세 심사")
        if "세차장" in target_biz:
            st.markdown("- **환경부 수질관리:** 수질오염방지시설 및 폐수배출시설 설치 허가·신고 필수.")
        elif "병원" in target_biz or "치과의원" in target_biz:
            st.markdown("- **의료폐기물:** 전문 처리업체 계약 필수.")
        else:
            st.markdown("- 일반 건축물 소방안전점검 기준 준수 대상.")

    with tab5:
        st.subheader("🚽 건물 정화조 용량 검토")
        est_dis = area * rate
        st.markdown(f"- 추정 일일 오수량: `{est_dis:.1f} 톤/일`")
        if est_dis >= 5.0 or "음식점" in target_biz or "세차장" in target_biz:
            st.warning("⚠️ 오수 발생량이 많으므로 건물 정화조 용량을 관리사무소에 반드시 확인하세요.")
        else:
            st.success("✅ 정화조 오수 부담 안정적")
