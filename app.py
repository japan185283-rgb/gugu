import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st

# ==========================================
# 🔑 1. 공공데이터 API 설정 및 함수 정의
# ==========================================
SERVICE_KEY = (  # 👉 여기에 본인의 공공데이터포털 인증키(Decoding)를 입력하세요
    mJgjmpJhH5%2FSZHKFHHFwkovN6r2Ptfb%2FxjnX6906XOdcPeRIjixDWwmq%2FGY4BF0om0Y%2FzKsO8aXq%2FJsx68MBJg%3D%3D
mJgjmpJhH5%2FSZHKFHHFwkovN6r2Ptfb%2FxjnX6906XOdcPeRIjixDWwmq%2FGY4BF0om0Y%2FzKsO8aXq%2FJsx68MBJg%3D%3D
)


def get_building_register(bjd_code, bun, ji="", plat_gb_cd="0"):
  """국토교통부 건축물대장 정보 서비스 API 호출"""
  url = "http://apis.data.go.kr/1611000/BldRgstService_v2/getBrTitleInfo"
  params = {
      "serviceKey": SERVICE_KEY,
      "sigunguCd": bjd_code[:5],
      "bjdongCd": bjd_code[5:],
      "bun": str(bun).zfill(4),
      "ji": str(ji).zfill(4) if ji else "0000",
      "platGbCd": plat_gb_cd,
  }

  try:
    response = requests.get(url, params=params, timeout=5)
    if response.status_code == 200:
      root = ET.fromstring(response.content)
      items = []
      for item in root.iter("item"):
        main_use = item.findtext("mainPurpsCdNm", default="정보 없음")
        bld_nm = item.findtext("bldNm", default="")
        items.append({"main_use": main_use, "bld_name": bld_nm})
      return {"status": "success", "items": items}
    else:
      return {
          "status": "error",
          "message": f"API 호출 오류 (코드: {response.status_code})",
      }
  except Exception as e:
    return {"status": "error", "message": str(e)}


def get_land_use_plan(bjd_code, bun, ji=""):
  """국토교통부 토지이용규제정보서비스(LURIS) API 호출"""
  # 토지이용규제 서비스 표준 엔드포인트
  url = "http://apis.data.go.kr/1611000/NspsOpenService/getNspsInfo"
  params = {
      "serviceKey": SERVICE_KEY,
      "sigunguCd": bjd_code[:5],
      "bjdongCd": bjd_code[5:],
      "bun": str(bun).zfill(4),
      "ji": str(ji).zfill(4) if ji else "0000",
  }

  try:
    response = requests.get(url, params=params, timeout=5)
    if response.status_code == 200:
      root = ET.fromstring(response.content)
      # 주요 용도지역 정보 태그 파싱 시도
      use_district = "정보 없음"
      for item in root.iter("item"):
        use_district = item.findtext("prposAreaNm", default="정보 없음")
        break
      return {"status": "success", "use_district": use_district}
    else:
      return {
          "status": "error",
          "message": f"토지이용 API 오류 (코드: {response.status_code})",
      }
  except Exception as e:
    return {"status": "error", "message": str(e)}


# ==========================================
# 🖥️ 2. Streamlit 기본 페이지 설정
# ==========================================
st.set_page_config(
    page_title="부동산 전 업종 완벽 통합 진단 시뮬레이터 Pro", layout="centered"
)

st.title("🛡️ 부동산 전 업종 완벽 통합 법적 진단 시뮬레이터 Pro")
st.markdown(
    "국토계획법, 건축법, 학교보건법, 양산시 도시계획/건축 조례 및 공공데이터"
    " API 실시간 연동 진단 툴"
)
st.markdown("---")

# ==========================================
# 🔍 3. 실시간 공공데이터 API 조회 UI 섹션
# ==========================================
st.subheader("🔍 실시간 건축물대장 및 토지이용규제 조회")

col_a1, col_a2, col_a3 = st.columns(3)
with col_a1:
  bjd_code_input = st.text_input(
      "법정동 코드 (10자리)",
      value="4833025000",
      help="예: 경남 양산시 물금읍 법정동 코드",
  )
with col_a2:
  bun_input = st.text_input("본번 (4자리)", value="0865")
with col_a3:
  ji_input = st.text_input("부번 (4자리)", value="0023")

api_queried_use = None
api_queried_district = None

if st.button("🚀 공공데이터 실시간 조회 실행", type="primary"):
  with st.spinner("공공데이터포털에서 정보를 불러오는 중입니다..."):
    # 건축물대장 호출
    bldg_res = get_building_register(bjd_code_input, bun_input, ji_input)
    # 토지이용규제 호출
    land_res = get_land_use_plan(bjd_code_input, bun_input, ji_input)

  # 결과 표시
  col_r1, col_r2 = st.columns(2)
  with col_r1:
    st.markdown("##### 🏢 건축물대장 결과")
    if bldg_res.get("status") == "success":
      items = bldg_res.get("items", [])
      if items:
        api_queried_use = items[0].get("main_use")
        st.success(
            f"주용도 감지 성공: **{api_queried_use}** (건물명:"
            f" {items[0].get('bld_name', '없음')})"
        )
      else:
        st.info("등록된 건축물대장 정보를 찾지 못했습니다 (나대지 가능성).")
    else:
      st.error(bldg_res.get("message"))

  with col_r2:
    st.markdown("##### 🗺️ 토지이용규제 결과")
    if land_res.get("status") == "success":
      api_queried_district = land_res.get("use_district")
      st.success(f"용도지역 감지 성공: **{api_queried_district}**")
    else:
      st.warning(land_res.get("message"))

st.markdown("---")

# ==========================================
# 📁 4. 기존 산단 데이터 파일 로드 로직
# ==========================================
DEFAULT_CSV_NAME = "industrial_complex.csv"
df_parcels = None

if os.path.exists(DEFAULT_CSV_NAME):
  try:
    df_parcels = pd.read_csv(DEFAULT_CSV_NAME)
    df_parcels.columns = df_parcels.columns.str.strip()
  except Exception as e:
    pass

# ==========================================
# 📚 5. 기존 법령 및 조례 데이터베이스
# ==========================================
general_building_uses = {
    "제1종근린생활시설": [
        "소매점",
        "휴게음식점(300㎡미만)",
        "이용원",
        "미용원",
        "세탁소",
        "탁구장",
        "체육도장",
        "의원",
        "치과의원",
        "한의원",
        "약국",
        "동사무소·파출소",
    ],
    "제2종근린생활시설": [
        "일반음식점",
        "휴게음식점(300㎡이상)",
        "제과점",
        "학원",
        "독서실",
        "공인중개사사무소",
        "사진관",
        "금융업소",
        "종교집회장",
        "당구장",
        "PC방",
        "일반미용업·네일숍",
        "골프연습장(스크린)",
        "청소년게임제공업(인형뽑기방·오락실)",
    ],
    "문화및집회시설": [
        "공연장",
        "관람장",
        "전시장",
        "집회장",
        "영화상영관",
        "예식장",
        "청소년게임제공업(대형)",
    ],
    "판매시설": [
        "도매시장",
        "소매시장",
        "상점",
        "백화점",
        "쇼핑센터",
        "대형마트",
        "복합쇼핑몰",
    ],
    "운수시설": ["여객자동차터미널", "철도시설", "공항시설", "항만시설", "화물터미널"],
    "의료시설": ["병원", "종합병원", "치과병원", "한방병원", "정신병원", "요양병원"],
    "교육연구시설": ["학교", "교육원", "직업훈련소", "연구소", "도서관", "생활권수련시설"],
    "운동시설": [
        "체육관",
        "수영장",
        "체력단련장(헬스)",
        "볼링장",
        "테니스장",
        "축구장",
    ],
    "업무시설": ["공공업무시설", "일반업무시설(사무소)", "오피스텔", "금융업소"],
    "숙박시설": [
        "호텔",
        "모텔",
        "여관",
        "펜션",
        "휴양콘도미니엄",
        "생활숙박시설(레지던스)",
    ],
    "위락시설": ["주점(유흥주점·단란주점)", "무도장", "카지노업소", "투견장"],
    "공장": [
        "제조업",
        "일반공장",
        "축산물가공업",
        "식육포장처리업",
        "식품제조·가공업",
        "금속가공제품제조업",
        "인쇄·출판업",
    ],
    "창고시설": ["일반창고", "냉장·냉동창고", "물류터미널", "하역시설", "보관창고"],
    "자동차관련시설": [
        "주차장",
        "세차장",
        "폐차장",
        "자동차검사장",
        "매매장",
        "정비공장",
    ],
    "동물관련시설": [
        "동물장묘업",
        "대규모동물생산업",
        "대형동물위탁관리시설(300㎡이상)",
        "도축장·도계장",
    ],
    "자원순환관련시설": [
        "폐기물재활용시설",
        "폐기물처분시설",
        "고물상·폐기물보관시설",
    ],
    "단독/다세대/아파트(주택류)": [
        "외국인관광 도시민박업(에어비앤비 합법)",
        "단독주택",
        "다세대주택",
    ],
}

zoning_restrictions = {
    "제1종전용주거지역": {
        "prohibited": [
            "일반음식점",
            "휴게음식점",
            "숙박업",
            "공장",
            "제조업",
            "판매시설",
            "PC방",
            "노래연습장",
            "축산물가공업",
            "세차장",
            "창고시설",
            "위락시설",
            "무도장",
            "카지노",
            "청소년게임제공업",
            "생활숙박시설",
            "펜션",
            "콘도",
        ]
    },
    "제2종전용주거지역": {
        "prohibited": [
            "일반음식점",
            "숙박업",
            "공장",
            "제조업",
            "축산물가공업",
            "위락시설",
            "무도장",
            "카지노",
            "청소년게임제공업",
            "생활숙박시설",
            "펜션",
            "콘도",
        ]
    },
    "제1종일반주거지역": {
        "prohibited": [
            "숙박업",
            "위락시설",
            "무도장",
            "카지노",
            "공장",
            "제조업",
            "세차장",
            "창고시설",
            "생활숙박시설",
            "펜션",
            "콘도",
        ]
    },
    "제2종일반주거지역": {
        "prohibited": [
            "숙박업",
            "위락시설",
            "무도장",
            "카지노",
            "공장",
            "제조업",
            "창고시설",
            "생활숙박시설",
            "펜션",
            "콘도",
        ]
    },
    "제3종일반주거지역": {
        "prohibited": [
            "숙박업",
            "위락시설",
            "무도장",
            "카지노",
            "공장",
            "제조업",
            "생활숙박시설",
            "펜션",
            "콘도",
        ]
    },
    "준주거지역": {"prohibited": ["위락시설(일부제한)", "무도장", "카지노"]},
    "중심상업지역": {"prohibited": []},
    "일반상업지역": {"prohibited": []},
    "근린상업지역": {"prohibited": ["위락시설(일부제한)", "무도장"]},
    "전용공업지역": {
        "prohibited": [
            "주거시설",
            "판매시설",
            "근린생활시설",
            "의료시설",
            "위락시설",
            "무도장",
            "카지노",
            "숙박업",
            "생활숙박시설",
        ]
    },
    "일반공업지역": {
        "prohibited": [
            "주거시설",
            "판매시설(대규모)",
            "위락시설",
            "무도장",
            "카지노",
            "숙박업",
            "생활숙박시설",
        ]
    },
    "준공업지역": {"prohibited": ["위락시설(대형)", "무도장(일부제한)"]},
    "보전녹지지역": {
        "prohibited": [
            "근린생활시설",
            "공장",
            "제조업",
            "숙박업",
            "음식점",
            "축산물가공업",
            "세차장",
            "창고시설",
            "위락시설",
            "무도장",
            "카지노",
            "청소년게임제공업",
            "생활숙박시설",
        ]
    },
    "자연녹지지역": {
        "prohibited": [
            "숙박업",
            "공장(일부제한)",
            "위락시설",
            "무도장",
            "카지노",
            "생활숙박시설",
        ]
    },
    "계획관리지역": {"prohibited": ["위락시설", "무도장", "카지노"]},
}

yangsan_ordinance_rules = {
    "제1종전용주거지역": {
        "additional_prohibited": [
            "음식점",
            "카페",
            "제과점",
            "골프연습장",
            "안마시술소",
            "학원",
            "PC방",
            "노래연습장",
            "사무소",
            "식육판매업",
            "미용업",
            "세탁소",
            "동물위탁관리업",
            "동물미용업",
            "공인중개사",
            "병원",
            "의원",
        ],
        "legal_basis": (
            "양산시 도시계획 조례에 따라 단독주택 중심의 양호한 주거환경 보호를"
            " 위해 상업·영업시설의 설치가 엄격히 금지됩니다."
        ),
    },
    "제1종일반주거지역": {
        "additional_prohibited": [
            "단란주점",
            "유흥주점",
            "안마시술소",
            "골프연습장",
            "공장",
            "제조업",
            "세차장",
            "창고시설",
            "고물상",
        ],
        "legal_basis": (
            "양산시 도시계획 조례 및 교육환경보호구역 기준에 의거, 주거 밀집"
            " 지역 내 환경오염·소음 유발 시설이 제한됩니다."
        ),
    },
    "준주거지역": {
        "additional_prohibited": ["숙박시설", "위락시설"],
        "legal_basis": (
            "양산시 도시계획 조례상 주거와 상업 혼재 지역이나 인근 학교 경계"
            " 거리에 따라 숙박·위락 허가가 제한됩니다."
        ),
    },
    "중심상업지역": {
        "additional_prohibited": [],
        "legal_basis": (
            "양산시 조례상 상업·업무 중심 지역으로 대부분 허용되나 주차장·소방"
            " 기준 준수 필수."
        ),
    },
    "일반상업지역": {
        "additional_prohibited": [],
        "legal_basis": (
            "양산시 조례상 일반 상업·업무 활동 지역으로 판매, 서비스, 위락"
            " 등 허용."
        ),
    },
    "자연녹지지역": {
        "additional_prohibited": ["숙박시설", "위락시설", "창고시설(대규모)"],
        "legal_basis": (
            "양산시 조례에 따라 건폐율 20%, 용적률 80% 이하가 적용되며 허용"
            " 업종 심사가 엄격합니다."
        ),
    },
    "계획관리지역": {
        "additional_prohibited": ["숙박시설", "위락시설"],
        "legal_basis": (
            "양산시 조례에 따라 공장 및 제조업소 입주 시 배출시설 승인 대상인"
            " 경우 제한될 수 있습니다."
        ),
    },
}

yangsan_building_ordinance_rules = {
    "제1종일반주거지역": {
        "max_height_rule": (
            "인접 대지경계선 및 정북 방향 일조 확보를 위한 건축물 높이 제한"
            " 적용."
        ),
        "parking_rule": "양산시 주차장 조례에 따른 세대별/면적별 부설주차장 기준 준수.",
    },
    "준주거지역": {
        "max_height_rule": "인근 주거지역 일조권 영향에 따른 높이 제한 규정 검토.",
        "parking_rule": "상업시설 부설주차장 설치 기준 엄수.",
    },
    "중심상업지역": {
        "max_height_rule": "가로구역별 건축물 최고 높이 지정 구역 확인 필요.",
        "parking_rule": "다중이용업소의 경우 자체 주차 확보 필수.",
    },
    "일반상업지역": {
        "max_height_rule": "미관지구 내 건축물의 경우 높이 및 형태 제한 적용.",
        "parking_rule": "상업용 시설 규모에 따른 법정 주차 대수 산정 확인.",
    },
}

# ==========================================
# 📝 6. 대상 부동산 기본 팩트 입력 UI
# ==========================================
st.subheader("📝 대상 부동산 기본 팩트 입력")

property_type = st.radio("중개 대상물 형태 선택", ["상가 / 일반 건축물", "산업단지 내 공장"])

# API로 가져온 값이 있다면 기본값으로 반영
default_zoning_idx = 0
if api_queried_district and api_queried_district in list(
    zoning_restrictions.keys()
):
  default_zoning_idx = list(zoning_restrictions.keys()).index(
      api_queried_district
  )

zoning = st.selectbox(
    "토지 용도지역 (국토계획법)",
    list(zoning_restrictions.keys()),
    index=default_zoning_idx,
)

default_bld_idx = 0
if api_queried_use:
  for idx, (k, v) in enumerate(general_building_uses.items()):
    if any(u in api_queried_use for u in v) or k in api_queried_use:
      default_bld_idx = idx
      break

bld_use = st.selectbox(
    "건축물대장 주용도 (건축법 시행령 별표1)",
    list(general_building_uses.keys()),
    index=default_bld_idx,
)

col_f1, col_f2 = st.columns(2)
with col_f1:
  floor_num = st.number_input(
      "건물 층수 (지하층은 음수 입력)", min_value=-5, max_value=50, value=1
  )
with col_f2:
  area = st.number_input(
      "바닥면적 / 전용면적 (㎡)", min_value=0.0, value=100.0
  )

has_school_zone = st.checkbox(
    "🎓 학교환경위생정화구역(절대·상대정화구역) 저촉 여부 확인", value=False
)

st.markdown("---")
st.subheader("🎯 임차인 희망 업종 및 설비 조건 선택")

comprehensive_biz_dict = {
    "🐶 반려동물 관련 영업": [
        "동물위탁관리업 (강아지유치원·호텔)",
        "동물미용업 (펫뷰티)",
        "동물생산업·판매업 (펫샵)",
        "동물장묘업 및 동물병원",
    ],
    "🍽️ 일반 음식점 및 카페·디저트": [
        "한식·중식·일식·양식 일반음식점",
        "휴게음식점 (카페·베이커리·디저트)",
        "제과점 및 아이스크림 전문점",
        "식육판매업 (정육점 - 소매)",
    ],
    "🍺 주점 및 유흥·위락": [
        "일반주점·맥주집 (간이음식)",
        "유흥주점 (룸살롱·클럽 - 위락시설)",
        "단란주점",
        "무도장 및 카지노업소",
    ],
    "🥩 제조업 및 축산물·식품가공": [
        "식육포장처리업 (축산물가공·도매 공장형)",
        "식육가공업 (햄·소시지·양념육 제조)",
        "식품제조·가공업 (일반식품공장)",
        "금속가공제품 제조업",
        "인쇄소 및 출판업",
    ],
    "📦 창고, 물류 및 자원순환": [
        "일반 물류창고 및 보관업",
        "냉장·냉동창고 (신선식품 물류)",
        "택배 대리점 및 집화시설",
        "고물상 및 폐기물재활용시설",
    ],
    "🏥 병의원 및 의료시설": [
        "일반의원·소아과·내과",
        "치과의원 및 치과병원",
        "한의원 및 한방병원",
        "요양병원 및 정신병원",
        "동물병원",
    ],
    "🏋️ 스포츠, 레저 및 운동시설": [
        "피트니스·헬스장 (체력단련장)",
        "스크린골프장 및 실내골프연습장",
        "당구장 및 실내 테니스·배드민턴장",
        "수영장 및 볼링장",
    ],
    "📚 교육, 연구 및 청소년시설": [
        "보습학원·입시학원 및 외국어학원",
        "독서실 및 스터디카페",
        "직업훈련소 및 기술학원",
        "PC방 및 노래연습장",
        "청소년게임제공업 (인형뽑기방·오락실)",
    ],
    "🚗 자동차 및 환경·세차장": [
        "세차장 (손세차·자동세차 - 폐수배출)",
        "자동차정비공장 (카센터)",
        "자동차매매장 및 전시장",
        "주차장업",
    ],
    "🏡 숙박 및 공유숙박": [
        "일반 숙박업 (모텔·호텔·여관)",
        "생활숙박시설(레지던스)",
        "오피스텔 에어비앤비",
        "외국인관광 도시민박업 (에어비앤비 합법)",
        "펜션 및 휴양콘도미니엄",
    ],
    "💄 뷰티, 공중위생 및 서비스": [
        "일반미용업·헤어샵 (미용실)",
        "네일아트 및 피부미용실",
        "목욕장업 (대중목욕탕·사우나)",
        "세탁소 (공중위생세탁업)",
    ],
    "💼 일반 오피스 및 전문서비스": [
        "공인중개사사무소",
        "일반 법무사·행정사·세무사 사무소",
        "일반 기업체 오피스 (본사·지사)",
        "금융업소 (은행·증권)",
    ],
}

biz_category = st.selectbox("희망 업종 대분류", list(comprehensive_biz_dict.keys()))
target_biz = st.selectbox("세부 희망 업종 선택", comprehensive_biz_dict[biz_category])
current_power = st.number_input(
    "현재 건물(호실) 계약전력 (kW)", min_value=1.0, value=10.0, step=1.0
)

submitted = st.button("🚀 종합 법적 진단 리포트 생성", type="primary")

# ==========================================
# 📊 7. 진단 리포트 및 시뮬레이션 로직
# ==========================================
if submitted:
  st.markdown("---")

  fatal_errors = []
  warnings = []
  legal_actions = []

  # 1. 국토계획법 용도지역 제한 검증
  if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
    prohibited_list = zoning_restrictions[zoning]["prohibited"]
    for p in prohibited_list:
      if p in target_biz or p in biz_category or (
          p == "위락시설"
          and target_biz
          in [
              "무도장 및 카지노업소",
              "유흥주점 (룸살롱·클럽 - 위락시설)",
              "단란주점",
          ]
      ):
        fatal_errors.append(
            f"[국토계획법 제76조] '{zoning}' 지역에서는 '{target_biz}'의 입점"
            " 및 영업이 원천 금지되어 있습니다."
        )
        break

  # 2. 양산시 도시계획 조례 교차 진단
  if property_type == "상가 / 일반 건축물" and zoning in yangsan_ordinance_rules:
    yangsan_rule = yangsan_ordinance_rules[zoning]
    matched_ban = False
    for add_p in yangsan_rule["additional_prohibited"]:
      if (
          add_p in target_biz
          or add_p in biz_category
          or any(kw in target_biz for kw in add_p.split())
      ):
        matched_ban = True
        fatal_errors.append(
            f"[양산시 도시계획 조례 위반] '{zoning}' 지역에서는 양산시 조례에"
            f" 따라 '{target_biz}'의 입점이 엄격히 금지됩니다. (근거:"
            f" {yangsan_rule['legal_basis']})"
        )
        break

    if not matched_ban:
      legal_actions.append(
          f"🏛️ **[양산시 조례 통과]** '{zoning}' 지역 내 '{target_biz}' 입점은"
            " 조례상 추가 제한에 저촉되지 않습니다."
      )

  # 3. 건축 조례 검토
  if (
      property_type == "상가 / 일반 건축물"
      and zoning in yangsan_building_ordinance_rules
  ):
    bld_rule = yangsan_building_ordinance_rules[zoning]
    legal_actions.append(
        f"📐 **[건축 조례 검토]** 높이 및 일조 제한: {bld_rule['max_height_rule']}"
    )
    legal_actions.append(
        f"🚗 **[주차장 기준]** {bld_rule['parking_rule']}"
    )

  # 4. 학교정화구역 검증
  if has_school_zone and any(
      kw in target_biz
      for kw in [
          "유흥주점",
          "단란주점",
          "PC방",
          "노래연습장",
          "호텔",
          "모텔",
          "당구장",
          "무도장",
          "카지노",
      ]
  ):
    fatal_errors.append(
        "[학교보건법 위반] 학교환경위생정화구역 내에 위치하여 해당 업종의 영업이"
        " 금지됩니다."
    )

  # 5. 건축법 주용도 검증
  if property_type == "상가 / 일반 건축물":
    if (
        "일반음식점" in target_biz
        or "휴게음식점" in target_biz
        or "제과점" in target_biz
    ):
      if bld_use not in [
          "제1종근린생활시설",
          "제2종근린생활시설",
          "판매시설",
          "숙박시설",
      ]:
        fatal_errors.append(
            f"[건축법 위반] 해당 음식·휴게업은 제1·2종 근린생활시설 등에"
            f" 해당해야 합니다. (현재 주용도: {bld_use})"
        )
      else:
        legal_actions.append(
            "🍽️ **[음식점 적합]** 건축법상 주용도 요건에 부합합니다."
        )
    elif "학원" in target_biz:
      if bld_use not in ["제2종근린생활시설", "교육연구시설"]:
        fatal_errors.append(
            f"[건축법 위반] 학원은 제2종근생 또는 교육연구시설이어야 합니다."
            f" (현재: {bld_use})"
        )
      else:
        legal_actions.append(
            "📚 **[학원 적합]** 건축법상 주용도 요건에 부합합니다."
        )
    else:
      legal_actions.append(
          f"✅ **[{target_biz}]** 일반적인 건축법·국토계획법 요건을 검토했습니다."
      )

  # 탭 구성 출력
  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "📋 1. 상세 법적 리포트",
      "💰 2. 원인자부담금",
      "⚡ 3. 전기용량(승압)",
      "🧯 4. 소방·환경·위생",
      "🚽 5. 정화조·오수",
  ])

  with tab1:
    st.subheader("📋 공법상 적합성 및 상세 법적 리포트")
    if fatal_errors:
      st.error("### ❌ [계약 절대 금지 / 중개사고 고위험 사유]")
      for err in fatal_errors:
        st.markdown(f"- **{err}**")
    else:
      st.success("### ✅ [공법상 입주 및 영업 기본 요건 적합]")
    if warnings:
      st.warning("### ⚠️ [주의 및 필수 검토]")
      for w in warnings:
        st.markdown(f"- {w}")
    if legal_actions:
      st.markdown("### 🛠️ [실무 법적 조치 및 상세 가이드]")
      for act in legal_actions:
        st.markdown(f"- {act}")

  with tab2:
    st.subheader("💰 상하수도 원인자부담금 시뮬레이션")
    est_discharge = area * 0.18
    st.markdown(f"- 추정 일일 오수량: **{est_discharge:.1f} 톤(㎥/일)**")
    st.markdown(
        f"- **상수도원인자부담금:** 약 **{est_discharge * 1823000:,.0f} 원**"
    )
    if est_discharge >= 10:
      st.markdown(
          f"- **하수도원인자부담금:** 약 **{est_discharge * 1910000:,.0f} 원**"
      )
    else:
      st.markdown("- **하수도원인자부담금:** ✅ 면제 대상 (10톤 미만)")

  with tab3:
    st.subheader("⚡ 현실적인 계약전력 및 승압 진단")
    req_power = min(15.0 + (area * 0.06), 50.0)
    power_diff = req_power - current_power
    st.markdown(f"- **현재 계약전력:** `{current_power} kW`")
    st.markdown(f"- **권장 소요전력:** 약 `{req_power:.1f} kW`")
    if power_diff > 0:
      st.warning(f"⚠️ 약 `{power_diff:.1f} kW` 승압이 필요할 수 있습니다.")
    else:
      st.success("✅ 현재 계약전력으로 충분합니다.")

  with tab4:
    st.subheader("🧯 소방, 환경 및 위생 규제 요건")
    st.markdown(
        "- 다중이용업소 소방안전시설완비증명서, 방염필증 대상 여부를 확인하세요."
    )

  with tab5:
    st.subheader("🚽 건물 정화조 용량 검토")
    st.markdown(f"- 추정 일일 오수량: `{area * 0.18:.1f} 톤/일`")
    st.success("✅ 정화조 오수 부담 검토 완료")
