import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="상가·공장·특수 업종 통합 부동산 인허가 진단 엔진",
    layout="centered",
)

st.title("🏢 상가·공장·특수 업종 통합 부동산 인허가 진단 엔진")
st.markdown(
    "지번, 건축물 용도, 업종을 선택하여 건축법 및 관련 법령에 따른 입주 적합성을"
    " 상세 진단합니다."
)


# 1. 산단 파일 자동 연동 및 지번 기반 필터링 안전성 처리
@st.cache_data
def load_industrial_data():
  try:
    # industrial_complex.csv 파일 로드 (지번 및 산단 업종 코드 데이터 포함)
    return pd.read_csv("industrial_complex.csv")
  except FileNotFoundError:
    return pd.DataFrame()


df_industrial = load_industrial_data()

# 2. 사용자 입력 섹션 (사이드바 UI)
st.sidebar.header("🔍 진단 조건 입력")

# 지번 및 주소 입력 필드 (산단 연동의 핵심 기준점)
input_address = st.sidebar.text_input(
    "대상지 주소 또는 지번 입력", "예: 경남 양산시 산막동 ..."
)

# 업종 리스트 (청소년게임제공업, 축산물가공업 포함)
industry_list = [
    "소매점 (일반 상가)",
    "음식점 / 카페",
    "학원 / 교습소",
    "PC방 / 게임제공업",
    "청소년게임제공업 (인형뽑기방·오락실)",
    "제2종근생 제조업 (소규모 공방 등)",
    "축산물가공업 (식품제조·가공)",
    "일반 제조업 (공장등록 대상)",
    "창고 및 물류시설",
]

selected_industry = st.sidebar.selectbox("진단할 업종 선택", industry_list)

building_use = st.sidebar.selectbox(
    "현재 건축물대장상 용도",
    [
        "제1종근린생활시설",
        "제2종근린생활시설",
        "문화 및 집회시설",
        "판매시설",
        "업무시설",
        "공장",
        "창고시설",
        "기타/불명",
    ],
)

area = st.sidebar.number_input(
    "전용 면적 (㎡)", min_value=1.0, max_value=10000.0, value=85.0
)

st.sidebar.divider()
st.sidebar.subheader("🏭 산업단지(지구) 지번·업종 자동 연동")

has_industrial_complex = st.sidebar.checkbox("산업단지(지구) 내 위치 여부")

matched_industrial_rows = pd.DataFrame()
selected_industrial_code = ""

if has_industrial_complex:
  if not df_industrial.empty:
    # 사용자가 입력한 지번/주소 키워드로 산단 데이터에서 매칭 검색 수행
    if input_address and input_address != "예: 경남 양산시 산막동 ...":
      # 주소나 지번 컬럼이 포함된 경우를 가정하여 검색 필터링
      search_term = input_address.split()[-1]  - Last part (e.g., 지번 or 동/리)
      matched_industrial_rows = df_industrial[
          df_industrial.astype(str)
          .apply(lambda row: row.str.contains(search_term, case=False))
          .any(axis=1)
      ]

    if not matched_industrial_rows.empty:
      st.sidebar.success(
          f"✨ 지번 연동 성공: {len(matched_industrial_rows)}개의 허용 업종/필지"
          " 코드가 조회되었습니다."
      )
      # 코드가 주루룩 뜨는 셀렉트박스 또는 멀티/싱글 셀렉트 구성
      display_column = (
          matched_industrial_rows.columns[1]
          if len(matched_industrial_rows.columns) > 1
          else matched_industrial_rows.columns[0]
      )
      selected_industrial_item = st.sidebar.selectbox(
          "조회된 허용 업종 코드 및 내역 선택",
          matched_industrial_rows[display_column].tolist(),
      )
      selected_industrial_code = str(selected_industrial_item)
    else:
      st.sidebar.warning(
          "입력하신 지번과 일치하는 산단 데이터가 없습니다. 전체 목록에서"
          " 선택하거나 코드를 직접 입력하세요."
      )
      selected_industrial_code = st.sidebar.text_input(
          "산단 업종분류 코드 직접 입력", ""
      )
  else:
    st.sidebar.warning(
        "industrial_complex.csv 파일을 찾을 수 없습니다. 코드를 직접 입력해"
        " 주세요."
    )
    selected_industrial_code = st.sidebar.text_input(
        "산단 업종분류 코드 직접 입력", ""
    )

# 3. 전기용량 현실화 산식 (업종별 표준 부하 밀도 반영)
def calculate_power_limit(industry, area_val):
  if "제조업" in industry or "축산물" in industry or "창고" in industry:
    return round(area_val * 0.15, 1)
  else:
    return round(area_val * 0.10, 1)


est_power = calculate_power_limit(selected_industry, area)

# 4. 업종별 맞춤형 상세 진단 엔진
st.divider()
st.subheader("📋 상세 법적 진단 리포트")

is_suitable = True
legal_basis = []
violation_reasons = []
solutions = []
checkpoints = []

# --- [산단 지번 연동 데이터 검토 로직] ---
if has_industrial_complex:
  legal_basis.append(
      "산업집적활성화 및 공장설립에 관한 법률 (산단 관리기본계획)"
  )
  checkpoints.append(
      "산업단지 내 위치하므로 관리기관(한국산업단지공단 등)의 입주 계약 및"
      " 관리기본계획상 업종 제한 부합 여부 확인 필수."
  )
  if selected_industrial_code:
    checkpoints.append(
        f"선택/매칭된 산단 업종 코드/내역: {selected_industrial_code}"
    )

# --- [업종별 세부 판정 및 상세 설명 로직] ---

if selected_industry == "청소년게임제공업 (인형뽑기방·오락실)":
  legal_basis.append(
      "게임산업진흥에 관한 법률, 건축법 시행령 [별표 1], 교육환경 보호에 관한"
      " 법률"
  )
  if building_use not in ["제2종근린생활시설", "문화 및 집회시설"]:
    is_suitable = False
    violation_reasons.append(
        f"현재 건축물 용도({building_use})는 청소년게임제공업 입주가 불가한"
        " 용도입니다."
    )
    solutions.append(
        "건축물대장상 용도를 '제2종근린생활시설(게임제공업)' 또는 '문화 및"
        " 집회시설'로 변경해야 합니다."
    )
  else:
    solutions.append(
        "건축물 용도 측면은 적합하나, 정화구역 거리 제한을 반드시 확인해야"
        " 합니다."
    )
  checkpoints.append(
      "학교경계 직선거리 200m 이내인 경우 교육환경보호위원회 심의 대상이 되어"
      " 영업 허가가 거부될 수 있으므로 관할 교육청 사전 확인 필수."
  )
  checkpoints.append(
      "지자체 조례에 따른 주거지역 내 야간 영업 제한 및 소음 규제 기준 확인."
  )

elif selected_industry == "축산물가공업 (식품제조·가공)":
  legal_basis.append(
      "축산물 위생관리법, 건축법 시행령 제3조의5 [별표 1], 물환경보전법,"
      " 대기환경보전법"
  )
  if "제2종근생" in building_use and area < 500:
    is_suitable = False
    violation_reasons.append(
        "제2종근생 제조업(500㎡ 미만)이라 하더라도 축산물가공업은 정식 인허가"
        " 및 오폐수·환경오염 유발 배출시설 설치 대상에 해당할 확률이 높아"
        " 제2종근생 입주가 원칙적으로 제한됩니다."
    )
    solutions.append(
        "일반 근린생활시설 건축물이 아닌 '공장' 용도의 건축물 또는"
        " 공업지역(산업단지 등) 내 전용 건축물로 계약해야 합니다."
    )
  else:
    solutions.append(
        "공장 용도 건축물일 경우 축산물가공업 허가 요건(HACCP 기준, 급수"
        " 시설, 오폐수 처리 등)을 충족해야 합니다."
    )
  checkpoints.append(
      "배출시설 설치 허가·신고 대상 여부 및 폐수 배출량에 따른 하수도"
      " 원인자부담금 발생 여부 확인 필수."
  )
  checkpoints.append(
      "식품위생법 및 축산물 위생관리법에 따른 시설기준(작업장 분리, 위생"
      " 설비) 충족 여부 점검."
  )

elif "제2종근생 제조업" in selected_industry:
  legal_basis.append("건축법 시행령 제3조의5 [별표 1] 제19호 및 관련 지자체 조례")
  if area >= 500:
    is_suitable = False
    violation_reasons.append(
        f"전용 면적({area}㎡)이 500㎡ 이상이므로 제2종근린생활시설(제조업소)"
        " 기준을 초과하였습니다."
    )
    solutions.append(
        "면적을 500㎡ 미만으로 분할하거나, '공장' 용도의 건축물로 계약해야"
        " 합니다."
    )
  else:
    solutions.append(
        "면적 요건(500㎡ 미만)은 충족하나, 악취·소음·폐수 등 대기/수질"
        " 배출시설 해당 여부를 반드시 체크해야 합니다."
    )
  checkpoints.append(
      "지자체 조례에 따라 주거지역 내 입주 가능한 제조업 업종 제한(예: 특정"
      " 업종 제한)이 있으므로 시/군/구청 해당 과에 사전 문의 필수."
  )

elif selected_industry == "소매점 (일반 상가)":
  legal_basis.append(
      "건축법 시행령 [별표 1] 제3호(제1종근린생활시설) 또는 제4호(제2종근린생활시설)"
  )
  if area > 1000:
    is_suitable = False
    violation_reasons.append(
        f"전용 면적({area}㎡)이 1,000㎡ 이상인 경우 단순 제1/2종 근생 소매점이"
        " 아니라 '판매시설(백화점, 대형마트 등)'로 분류됩니다."
    )
    solutions.append(
        "건축물 용도를 '판매시설'로 변경하거나 1,000㎡ 미만으로 면적을 조정해야"
        " 합니다."
    )
  else:
    solutions.append(
        "바닥면적 1,000㎡ 미만의 소매점은 제1종 또는 제2종 근생으로 입주"
        " 가능합니다."
    )
  checkpoints.append(
      "유통산업발전법상 대규모점포 규제 대상 여부 및 식품 판매 시 추가 위생"
      " 신고 여부 확인."
  )

elif selected_industry == "음식점 / 카페":
  legal_basis.append(
      "건축법 시행령 [별표 1] 제3호/제4호, 식품위생법 시행령, 하수도법"
  )
  if building_use not in [
      "제1종근린생활시설",
      "제2종근린생활시설",
      "판매시설",
      "문화 및 집회시설",
  ]:
    is_suitable = False
    violation_reasons.append(
        f"현재 건축물 용도({building_use})는 일반음식점이나 휴게음식점 입주가"
        " 불가합니다."
    )
    solutions.append(
        "건축물대장 용도를 근린생활시설(음식점)로 변경해야 하며, 정화용량"
        " 산정 검토가 필요합니다."
    )
  else:
    solutions.append(
        "용도상 가능하나, 정화조 용량이 업종별 1인당 오수 발생량을 초과하는지"
        " 확인해야 합니다."
    )
  checkpoints.append(
      "정화조 용량 초과 시 정화조 증설 공사 또는 오수돌림비(원인자부담금)"
      " 발생 가능성 체크."
  )
  checkpoints.append(
      "지하층 또는 2층 이상일 경우 하수도법에 따른 배수설비 및 앙카설치"
      " 규정 확인."
  )

elif selected_industry == "학원 / 교습소":
  legal_basis.append(
      "학원의 설립·운영 및 과외교습에 관한 법률, 건축법 시행령 [별표 1], 소방시설법"
  )
  if building_use not in ["제2종근린생활시설", "교육연구시설"]:
    is_suitable = False
    violation_reasons.append(
        f"현재 건축물 용도({building_use})는 학원/교습소 용도로 부적합합니다."
    )
    solutions.append(
        "건축물 용도를 '제2종근린생활시설(학원)' 또는 '교육연구시설'로 용도"
        " 변경해야 합니다."
    )
  else:
    solutions.append(
        "용도상 적합하나, 면적 및 층수에 따른 소방시설(피난계단, 스프링클러"
        " 등) 설치 요건을 충족해야 합니다."
    )
  checkpoints.append(
      "학원 면적 합계가 일정 규모 이상이거나 특정 층수(예: 지하층, 3층 이상"
      " 일정 면적 이상)일 경우 소방완비증명서 발급 필수."
  )
  checkpoints.append(
      "강의실 면적당 수용 인원 기준 및 학교정화구역 유해업소 정화거리 규정"
      " 동시 확인."
  )

elif selected_industry == "PC방 / 게임제공업":
  legal_basis.append(
      "게임산업진흥에 관한 법률, 건축법 시행령 [별표 1], 다중이용업소의 안전관리에"
      " 관한 특별법"
  )
  if building_use not in ["제2종근린생활시설", "문화 및 집회시설"]:
    is_suitable = False
    violation_reasons.append(
        f"현재 건축물 용도({building_use})는 PC방 입주가 불가능합니다."
    )
    solutions.append(
        "건축물 용도를 '제2종근린생활시설' 또는 '문화 및 집회시설'로 변경해야"
        " 합니다."
    )
  else:
    solutions.append(
        "건축물 용도는 적합하나 다중이용업소 소방 안전 기준을 반드시 충족해야"
        " 합니다."
    )
  checkpoints.append(
      "다중이용업소 완비증명서 발급 대상이므로 비상구, 피난통로 폭, 창문 규격"
      " 등 소방서 사전 실사 대비 필수."
  )

elif selected_industry == "일반 제조업 (공장등록 대상)":
  legal_basis.append(
      "산업집적활성화 및 공장설립에 관한 법률, 건축법 시행령 [별표 1] 제17호(공장)"
  )
  if building_use != "공장":
    is_suitable = False
    violation_reasons.append(
        f"현재 건축물 용도({building_use})는 공장 등록이 불가능한 일반"
        " 건축물입니다."
    )
    solutions.append(
        "반드시 건축물 용도가 '공장'으로 되어 있는 건물이나 계획관리지역 내"
        " 승인된 제조시설, 혹은 산업단지(공업지역) 내로 입주해야 합니다."
    )
  else:
    solutions.append(
        "공장 용도이므로 관할 지자체에 공장등록신청 및 환경오염 물질 배출"
        " 협의를 진행하면 됩니다."
    )
  checkpoints.append(
      "건축물 허가 면적 및 사용하려는 기계·기구의 마력수(또는 전력"
      " 용량)에 따른 공장등록 가능 여부 확인."
  )

elif selected_industry == "창고 및 물류시설":
  legal_basis.append(
      "건축법 시행령 [별표 1] 제18호(창고시설), 물류시설의 개발 및 운영에 관한"
      " 법률"
  )
  if building_use not in ["창고시설", "공장"]:
    is_suitable = False
    violation_reasons.append(
        f"현재 건축물 용도({building_use})는 창고 및 물류시설로 부적합합니다."
    )
    solutions.append("건축물 용도를 '창고시설'로 변경해야 합니다.")
  else:
    solutions.append("창고 용도 건축물로서 물품 보관 및 물류 작업에 적합합니다.")
  checkpoints.append(
      "진입도로 폭이 대형 화물차(1톤~11톤 이상) 통행에 지장이 없는지 도로"
      " 조건 확인 필수."
  )

else:
  legal_basis.append("건축법 시행령 [별표 1] 용도별 건축물의 종류")
  solutions.append(
      "선택하신 업종에 대한 기본 건축물 용도 및 지자체 조례 제한 사항을"
      " 확인하세요."
  )
  checkpoints.append("관할 시·군·구청 허가 담당 부서에 사전 방문 또는 유선 문의.")

# --- [결과 화면 출력] ---
if is_suitable:
  st.success("✅ **[적합 검토]** 현재 조건에서 입주 가능성이 높습니다.")
else:
  st.error("❌ **[부적합 / 조건부 검토]** 법적 제한 사항 또는 보완이 필요합니다.")

st.markdown(f"**📌 진단 대상지:** {input_address}")

st.markdown("### 📜 법적 근거 및 상세 분석")
for b in legal_basis:
  st.write(f"- **관련 법령:** {b}")

if violation_reasons:
  st.markdown("### ⚠️ 위반 및 제한 사유")
  for v in violation_reasons:
    st.write(f"- {v}")

st.markdown("### 💡 해결 대안 및 실무 조치 가이드")
for s in solutions:
  st.write(f"- {s}")

st.markdown("### 📌 실무 필수 체크포인트")
for c in checkpoints:
  st.write(f"- {c}")

st.info(
    f"⚡ **추정 필요 전기용량 산식 결과:** 약 **{est_power} kW** (면적 비례 표준"
    " 부하 밀도 적용)"
)
