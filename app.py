import os
import re
import sqlite3
import datetime
import pandas as pd
import requests
import streamlit as st

# 1. 페이지 기본 설정 (세로형 중심 배치)
st.set_page_config(page_title="부동산 전 업종 완벽 통합 진단 시뮬레이터 Pro", layout="centered")

st.title("🛡 부동산 전 업종 완벽 통합 법적 진단 시뮬레이터 Pro")
st.markdown("국토계획법, 건축법, 교육환경보호법, 양산시 도시계획/건축 조례 및 개별 인허가법 기반의 전수 크로스 체크 규제 진단 툴")

st.markdown("---")

# Kakao REST API 키 (지도 및 주소 좌표 정제용)
KAKAO_REST_API_KEY = "0a51d12c463757bc7dc14c62a99b0a85"

# 로컬 SQLite DB 파일 경로
LOCAL_DB_PATH = "building_data.db"


# -----------------------------------------------------------------------------
# 📁 [양산시 모든 지역 CSV 파일(표제부/지역지구구역/산단) 자동 로드 및 통합 로직]
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="📂 폴더 내 양산시 모든 CSV 파일 및 산단 데이터를 자동 연동 중입니다...")
def load_all_local_csvs():
    """
    현재 실행 폴더 안의 모든 .csv 파일(표제부, 지역지구구역, 산단 등)을 찾아 인코딩에 맞춰 자동으로 불러오고 통합합니다.
    """
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        return None, []

    loaded_dfs = []
    file_list = []

    for file in csv_files:
        for enc in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
            try:
                df = pd.read_csv(file, encoding=enc, low_memory=False)
                df.columns = df.columns.str.strip()
                df['_출처파일'] = file
                loaded_dfs.append(df)
                file_list.append(file)
                break
            except Exception:
                continue

    if loaded_dfs:
        try:
            combined_df = pd.concat(loaded_dfs, ignore_index=True)
            return combined_df, file_list
        except Exception:
            return loaded_dfs[0], file_list

    return None, []

df_parcels, loaded_csv_files = load_all_local_csvs()

# 상단 연동 안내 문구 간소화
if loaded_csv_files:
    st.success(f"✅ **[양산시 로컬 CSV 데이터 자동 연동 완료]** 총 {len(loaded_csv_files)}개 CSV 파일 (건축물 표제부 및 지역지구구역) 연동 완료")
else:
    st.info("💡 폴더 내에 CSV 파일이 없습니다. 양산시 지번/건축물/지역지구구역/산단 CSV 파일을 폴더에 위치시켜 주세요.")


# -----------------------------------------------------------------------------
# 🛠 [데이터 정제, 코드 매핑 및 자동 선택 보완 함수]
# -----------------------------------------------------------------------------
# 건축물대장 주용도 데이터베이스
general_building_uses = [
    "제1종근린생활시설",
    "제2종근린생활시설",
    "문화및집회시설",
    "판매시설",
    "운수시설",
    "의료시설",
    "교육연구시설",
    "운동시설",
    "업무시설",
    "숙박시설",
    "위락시설",
    "공장",
    "창고시설",
    "자동차관련시설",
    "동물관련시설",
    "자원순환관련시설",
    "단독/다세대/아파트(주택류)",
    "나대지(건축물없음)"  # 나대지 추가
]

# 용도지역 목록
zoning_options = [
    "제1종전용주거지역", "제2종전용주거지역", "제1종일반주거지역", "제2종일반주거지역", "제3종일반주거지역",
    "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역",
    "전용공업지역", "일반공업지역", "준공업지역",
    "보전녹지지역", "자연녹지지역", "계획관리지역",
    "생산녹지지역", "보전관리지역", "생산관리지역", "농림지역", "자연환경보전지역"
]

# 양산시 도시계획 조례 기준 원칙 상한선 데이터베이스 (건폐율, 용적률)
yangsan_zoning_limits_base = {
    "제1종전용주거지역": {"bcv": 50, "far": 100},
    "제2종전용주거지역": {"bcv": 40, "far": 150},
    "제1종일반주거지역": {"bcv": 60, "far": 200},
    "제2종일반주거지역": {"bcv": 60, "far": 220},
    "제3종일반주거지역": {"bcv": 50, "far": 250},
    "준주거지역": {"bcv": 70, "far": 400},
    "중심상업지역": {"bcv": 80, "far": 1300},
    "일반상업지역": {"bcv": 80, "far": 1000},
    "근린상업지역": {"bcv": 70, "far": 800},
    "유통상업지역": {"bcv": 70, "far": 700},
    "전용공업지역": {"bcv": 70, "far": 250},
    "일반공업지역": {"bcv": 70, "far": 300},
    "준공업지역": {"bcv": 70, "far": 350},
    "보전녹지지역": {"bcv": 20, "far": 80},
    "생산녹지지역": {"bcv": 20, "far": 100},
    "자연녹지지역": {"bcv": 20, "far": 100},
    "보전관리지역": {"bcv": 20, "far": 80},
    "생산관리지역": {"bcv": 20, "far": 80},
    "계획관리지역": {"bcv": 40, "far": 100},
    "농림지역": {"bcv": 20, "far": 80},
    "자연환경보전지역": {"bcv": 20, "far": 80},
}

def calculate_dynamic_limits(zoning, all_districts_text, target_biz):
    """
    양산시 도시계획 조례(제55조~제62조)에 근거하여 해당 필지의 복합적인 
    용도지구/구역 중첩 상태와 희망 업종을 분석하여 실질 건폐율/용적률 상한을 계산합니다.
    """
    if zoning not in yangsan_zoning_limits_base:
        return None, None, "미등록 용도지역"

    base_bcv = yangsan_zoning_limits_base[zoning]["bcv"]
    base_far = yangsan_zoning_limits_base[zoning]["far"]
    
    final_bcv = base_bcv
    final_far = base_far
    reasons = []

    is_urban_area = "주거" in zoning or "상업" in zoning or "공업" in zoning or "녹지" in zoning
    all_text_clean = str(all_districts_text).replace(" ", "")

    # 1. 특례 및 완화 (우선 적용되는 강행/특례 규정)
    
    # 산업단지 특례 (제55조 22항 및 제60조 1항 단서)
    if "산업단지" in all_text_clean or "농공단지" in all_text_clean:
        if "공업" in zoning:
            final_bcv = 80  # 제56조 6호: 공업지역 내 국가/일반/첨단/준산업단지 80%
            if zoning == "전용공업지역": final_far = 300
            elif zoning == "일반공업지역": final_far = 350
            elif zoning == "준공업지역": final_far = 400
            reasons.append("산업단지 특례(공업지역) 적용")
        elif "농공단지" in all_text_clean and not is_urban_area:
            final_bcv = 70
            final_far = 150
            reasons.append("농공단지 특례(도시외지역) 적용")
            
    # 취락지구 완화 (제56조 1호)
    if "취락지구" in all_text_clean:
        final_bcv = max(final_bcv, 60)
        reasons.append("취락지구 건폐율 60% 완화")

    # 수산자원보호구역 특례 (제56조 3호, 제61조 2호)
    if "수산자원보호구역" in all_text_clean:
        final_bcv = 40
        final_far = 80
        reasons.append("수산자원보호구역 특례")

    # 자연공원 특례 (제56조 4호, 제61조 3호)
    if "자연공원" in all_text_clean:
        final_bcv = 60
        final_far = 100
        reasons.append("자연공원 특례")

    # 개발진흥지구 완화 (제56조 2호, 제61조 1호)
    if "개발진흥지구" in all_text_clean:
        if not is_urban_area:
            final_bcv = max(final_bcv, 40)
            final_far = max(final_far, 100)
            if zoning == "계획관리지역" and "산업유통개발진흥지구" in all_text_clean:
                final_bcv = 60
                reasons.append("계획관리지역 내 산업·유통개발진흥지구 건폐율 60% 완화")
            else:
                reasons.append("도시외지역 개발진흥지구 특례")
        elif zoning == "자연녹지지역":
            final_bcv = max(final_bcv, 30)
            reasons.append("자연녹지지역 내 개발진흥지구 건폐율 30% 완화")

    # 방화지구 완화 (제58조 1항)
    if "방화지구" in all_text_clean and zoning in ["준주거지역", "일반상업지역", "근린상업지역"]:
        final_bcv = 80
        reasons.append(f"{zoning} 내 방화지구 건폐율 80% 완화")

    # 방재지구 완화 (제58조 6항, 제60조 4항 - 재해저감대책 시)
    if "방재지구" in all_text_clean:
        reasons.append("방재지구 내 재해저감대책 수립 시 건폐율 120%, 용적률 140% 상향 가능")

    # 업종 기반 특례 (전통시장, 주유소 등)
    if "전통시장" in target_biz or "상점가" in target_biz:
        if zoning in ["제1종일반주거지역", "제2종일반주거지역", "제3종일반주거지역", "준주거지역", "준공업지역"]:
            final_bcv = max(final_bcv, 70)
            if "주거" in zoning: final_far = 500
            if "공업" in zoning: final_far = 400
            reasons.append("전통시장 및 상점가 특례 완화")
        elif "상업" in zoning:
            final_bcv = max(final_bcv, 90)
            reasons.append("전통시장 및 상점가 상업지역 건폐율 90% 완화")
            
    if "주유소" in target_biz or "세차장" in target_biz:
        if zoning == "자연녹지지역":
            final_bcv = max(final_bcv, 30)
            reasons.append("자연녹지지역 주유소/충전소 건폐율 30% 완화")

    bcv_str = f"{final_bcv}%"
    far_str = f"{final_far}%"
    
    if reasons:
        reason_txt = " + ".join(reasons)
        return bcv_str, far_str, f"조례 특례 적용: {reason_txt}"
    else:
        return bcv_str, far_str, "양산시 조례 원칙 적용"

def get_building_restriction_info(zoning, all_districts_text):
    """
    양산시 도시계획 조례 제31조~제37조에 따른 건축제한 및 예외 규정을 동적으로 판별합니다.
    """
    restrictions = []
    
    if not zoning:
        return []

    # [조례 제31조] 용도지역별 건축제한 (원칙 표기)
    base_restrictions = {
        "제1종전용주거지역": "단독주택 및 양호한 주거환경을 위한 시설 위주로 허용 (조례 별표1). 일반 상가 및 유흥시설 건축 불가.",
        "제2종전용주거지역": "공동주택 중심 양호한 주거환경 보호 목적 (조례 별표2).",
        "제1종일반주거지역": "저층주택 및 근린생활시설 건축 가능 (조례 별표3). 소음·악취 유발 공장 제한.",
        "제2종일반주거지역": "중층주택 중심 정주환경 보호. 유흥/위락시설 건축 차단 (조례 별표4).",
        "제3종일반주거지역": "고층 공동주택 밀집지역으로 대규모 인파 유입 시설 제한 (조례 별표5).",
        "준주거지역": "주거와 상업 기능 혼재. 일부 숙박/위락시설 제한 (조례 별표6).",
        "중심상업지역": "업무/상업 중심지. 대부분 업종 허용되나 주차장/소방 요건 충족 필요 (조례 별표7).",
        "일반상업지역": "일반적인 판매/서비스/위락 시설 허용 지역 (조례 별표8).",
        "근린상업지역": "주거지역 인접 상업지구. 대형 유흥/위락 업종 제한 가능성 있음 (조례 별표9).",
        "전용공업지역": "중화학 공장 전용 구역. 일반 근린생활/주거/상업시설 건축 원천 금지 (조례 별표11).",
        "일반공업지역": "공장 및 지식산업센터 위주. 대형 상업/숙박시설 제한 (조례 별표12).",
        "준공업지역": "경공업 및 주거/상업 복합. 아파트형 공장 지원시설 비율 제한 적용 (조례 별표13).",
        "보전녹지지역": "자연환경 보전 목적. 건축 및 영업 행위 극도 제한 (조례 별표14).",
        "생산녹지지역": "농업적 생산을 위해 개발 유보. 농업 관련 시설 위주 허용 (조례 별표15).",
        "자연녹지지역": "제한적 개발 허용. 성장관리방안 유무에 따라 입점 심사 차등 (조례 별표16).",
        "보전관리지역": "자연환경 및 산림 보전 목적. 제한적 범위 내 시설만 허용 (조례 별표17).",
        "생산관리지역": "농림/어업 생산 보전 목적이나 농업 관련 가공시설 등 일부 허용 (조례 별표18).",
        "계획관리지역": "도시지역 편입 예상지. 배출시설 기준 충족 시 공장/근생 허용폭이 넓음 (조례 별표19).",
        "농림지역": "농림업 진흥 목적. 농어가 주택 및 관련 창고 위주 허용 (조례 별표20).",
        "자연환경보전지역": "수자원/생태계 보전 목적. 건축 규제 최고 수위 (조례 별표21)."
    }
    
    if zoning in base_restrictions:
        restrictions.append(f"✅ **[원칙] {zoning} 건축제한**: {base_restrictions[zoning]}")

    all_text_clean = str(all_districts_text).replace(" ", "")

    # [조례 제32조] 용도지역에서의 건축제한 특례 (생산관리지역 + 농촌융복합시설)
    if "생산관리지역" in zoning and "농촌융복합" in all_text_clean: # 키워드가 있을 경우 예시
        restrictions.append("💡 **[조례 제32조 특례]** 생산관리지역이라도 '농촌융복합시설'로 인정받는 경우 휴게/일반음식점, 제과점, 전시장(박물관 등) 건축이 예외적으로 허용됩니다.")

    # [조례 제33조] 자연경관지구에서의 용도제한
    if "자연경관지구" in all_text_clean:
        restrictions.append("🚫 **[조례 제33조 규제] 자연경관지구 중첩**: 아파트, 제2종근생, 집회장, 판매/운수/숙박/위락/공장/창고/위험물/자동차/자원순환 시설의 건축이 원칙적으로 불가합니다.")

    # [조례 제35조] 특화경관지구에서의 용도제한
    if "특화경관지구" in all_text_clean:
        restrictions.append("🚫 **[조례 제35조 규제] 특화경관지구 중첩**: 공동주택, 대형 제1종근생(500㎡이상), 제2종근생, 관람장, 일반숙박, 공장, 창고 등의 건축이 강하게 제한됩니다.")

    # [조례 제36조] 시가지경관지구에서의 용도제한
    if "시가지경관지구" in all_text_clean:
        restrictions.append("🚫 **[조례 제36조 규제] 시가지경관지구 중첩**: 공장, 창고, 위험물저장, 자동차관련시설, 축사, 묘지시설 등의 건축을 할 수 없습니다.")

    # [조례 제37조] 전통경관지구에서의 용도제한
    if "전통경관지구" in all_text_clean:
        restrictions.append("🚫 **[조례 제37조 규제] 전통경관지구 중첩**: 공동주택, 제2종근생, 판매, 숙박, 위락, 공장, 대형창고(500㎡초과) 등의 건축이 금지됩니다.")

    # [조례 제49조] 중요시설물보호지구에서의 건축제한
    if "중요시설물보호지구" in all_text_clean:
        restrictions.append("🚫 **[조례 제49조 규제] 중요시설물보호지구 중첩**: 단독/공동주택, 종교시설, 위락시설, 공장, 노유자/수련시설, 창고 등의 건축이 금지됩니다.")

    # [조례 제51조] 특정용도제한지구에서의 건축제한
    if "특정용도제한지구" in all_text_clean:
        restrictions.append("🚫 **[조례 제51조 규제] 특정용도제한지구 중첩**: 안마시술소, 단란주점, 판매/의료(요양병원)/숙박/위락/공장/창고 및 장례식장 건축이 원천 차단됩니다.")

    # [조례 제51조의2] 복합용도지구 완화 특례
    if "복합용도지구" in all_text_clean:
        if "일반주거지역" in zoning:
            restrictions.append("💡 **[조례 제51조의2 완화] 복합용도지구 (주거)**: 일반주거지역이나 준주거지역 수준으로 허용 용도가 확대됩니다. (단, 안마시술소, 공장 등 일부는 여전히 제외)")
        elif "일반공업지역" in zoning:
            restrictions.append("💡 **[조례 제51조의2 완화] 복합용도지구 (공업)**: 일반공업지역이나 준공업지역 수준으로 허용 용도가 확대됩니다.")
        elif "계획관리지역" in zoning:
            restrictions.append("💡 **[조례 제51조의2 완화] 복합용도지구 (계획관리)**: 일반/휴게음식점, 제과점, 판매시설, 숙박시설, 유원시설업이 일부 허용될 수 있습니다.")

    return restrictions


def is_invalid_val(val):
    """0.0, NaN, None, 빈 문자열 등 무효 데이터를 필터링합니다."""
    if pd.isna(val):
        return True
    s = str(val).strip().lower()
    if s in ["", "nan", "none", "null", "0", "0.0", "0.00", "0.000"]:
        return True
    return False

def map_building_use(val_str):
    """
    03000과 같은 건축물대장 주용도 코드 및 키워드를 한글 주용도 명칭으로 자동 변환합니다.
    """
    if is_invalid_val(val_str):
        return None
    val_str = str(val_str).strip()

    # 숫자 형태의 코드 추출 (예: '03000' -> '03000')
    code_clean = re.sub(r'[^0-9]', '', val_str)
    if code_clean:
        if code_clean.startswith('01') or code_clean.startswith('1000'):
            return "단독/다세대/아파트(주택류)"
        elif code_clean.startswith('02') or code_clean.startswith('2000'):
            return "단독/다세대/아파트(주택류)"
        elif code_clean.startswith('03') or code_clean.startswith('3000'):
            return "제1종근린생활시설"
        elif code_clean.startswith('04') or code_clean.startswith('4000'):
            return "제2종근린생활시설"
        elif code_clean.startswith('05') or code_clean.startswith('5000'):
            return "문화및집회시설"
        elif code_clean.startswith('07') or code_clean.startswith('7000'):
            return "판매시설"
        elif code_clean.startswith('08') or code_clean.startswith('8000'):
            return "운수시설"
        elif code_clean.startswith('09') or code_clean.startswith('9000'):
            return "의료시설"
        elif code_clean.startswith('10'):
            return "교육연구시설"
        elif code_clean.startswith('13'):
            return "운동시설"
        elif code_clean.startswith('14'):
            return "업무시설"
        elif code_clean.startswith('15'):
            return "숙박시설"
        elif code_clean.startswith('16'):
            return "위락시설"
        elif code_clean.startswith('17'):
            return "공장"
        elif code_clean.startswith('18'):
            return "창고시설"
        elif code_clean.startswith('20'):
            return "자동차관련시설"
        elif code_clean.startswith('21'):
            return "동물관련시설"
        elif code_clean.startswith('22'):
            return "자원순환관련시설"

    # 텍스트 직접 포함 여부 매칭
    for b_use in general_building_uses:
        if b_use in val_str:
            return b_use

    # 키워드 2차 탐색
    if "1종근" in val_str or "제1종" in val_str: return "제1종근린생활시설"
    if "2종근" in val_str or "제2종" in val_str: return "제2종근린생활시설"
    if any(k in val_str for k in ["주택", "아파트", "다세대", "연립", "단독"]): return "단독/다세대/아파트(주택류)"
    if "공장" in val_str: return "공장"
    if "창고" in val_str: return "창고시설"
    if "자동차" in val_str: return "자동차관련시설"
    if any(k in val_str for k in ["동물", "식물"]): return "동물관련시설"
    if any(k in val_str for k in ["자원순환", "분뇨", "쓰레기"]): return "자원순환관련시설"
    if "숙박" in val_str: return "숙박시설"
    if "위락" in val_str: return "위락시설"
    if any(k in val_str for k in ["의료", "병원"]): return "의료시설"
    if any(k in val_str for k in ["교육", "학원"]): return "교육연구시설"
    if any(k in val_str for k in ["운동", "체육"]): return "운동시설"
    if "업무" in val_str: return "업무시설"
    if "판매" in val_str: return "판매시설"
    if "운수" in val_str: return "운수시설"
    if any(k in val_str for k in ["문화", "집회"]): return "문화및집회시설"

    return None

def map_zoning(val_str):
    """
    용도지역 약칭 및 데이터를 선택 가능한 용도지역 표준 명칭으로 자동 변환합니다.
    """
    if is_invalid_val(val_str):
        return None
    val_str = str(val_str).strip()

    for z_opt in zoning_options:
        if z_opt in val_str:
            return z_opt

    if "1종전용" in val_str: return "제1종전용주거지역"
    if "2종전용" in val_str: return "제2종전용주거지역"
    if "1종일반" in val_str: return "제1종일반주거지역"
    if "2종일반" in val_str: return "제2종일반주거지역"
    if "3종일반" in val_str: return "제3종일반주거지역"
    if "준주거" in val_str: return "준주거지역"
    if "중심상업" in val_str: return "중심상업지역"
    if "일반상업" in val_str: return "일반상업지역"
    if "근린상업" in val_str: return "근린상업지역"
    if "유통상업" in val_str: return "유통상업지역"
    if "전용공업" in val_str: return "전용공업지역"
    if "일반공업" in val_str: return "일반공업지역"
    if "준공업" in val_str: return "준공업지역"
    if "보전녹지" in val_str: return "보전녹지지역"
    if "자연녹지" in val_str: return "자연녹지지역"
    if "생산녹지" in val_str: return "생산녹지지역"
    if "계획관리" in val_str: return "계획관리지역"
    if "보전관리" in val_str: return "보전관리지역"
    if "생산관리" in val_str: return "생산관리지역"
    if "농림" in val_str: return "농림지역"
    if "자연환경" in val_str: return "자연환경보전지역"

    return None

def search_local_csv_and_db(address_str):
    """
    폴더에 포함된 모든 양산시 CSV(표제부 및 지역지구구역) 및 SQLite DB에서 유효한 주용도, 기타용도, 용도지역, 지구단위계획(1종/2종), 건폐율 및 용적률을 검색합니다.
    """
    found_purp = None
    found_etc_purp = None
    found_zoning = None
    found_district_plan = None
    found_bcv = None  # 건폐율
    found_far = None  # 용적률
    all_districts_text = ""

    if not address_str:
        return None, None, None, None, None, None, ""

    # 주소 키워드 토큰화 (예: '중부동 410-1' -> ['중부동', '410-1'])
    clean_addr = re.sub(r'[^\w\s-]', '', address_str).strip()
    tokens = [t for t in clean_addr.split() if t not in ['경상남도', '양산시', '경남', '양산']]

    # 1. 통합 CSV 데이터프레임 내 검색
    if df_parcels is not None and not df_parcels.empty:
        cols = df_parcels.columns.tolist()
        addr_cols = [c for c in cols if any(k in c.lower() for k in ['대지위치', '소재지', '주소', '지번주소', '위치', '지번'])]

        matched_rows = pd.DataFrame()
        
        if addr_cols:
            # 1차: 토큰 기반 정밀 검색 (동/리/읍/면 + 지번 복합)
            for a_col in addr_cols:
                col_str = df_parcels[a_col].fillna('').astype(str)
                mask = pd.Series(True, index=df_parcels.index)
                for token in tokens:
                    if len(token) > 0:
                        mask = mask & col_str.str.contains(re.escape(token), na=False)
                
                sub_matched = df_parcels[mask]
                if not sub_matched.empty:
                    matched_rows = pd.concat([matched_rows, sub_matched])

            # 2차 유연 검색: 지번 번호(본번-부번) 및 동/리 포함 검색
            if matched_rows.empty:
                num_match = re.search(r'(\d+)(?:-(\d+))?', address_str)
                dong_match = re.search(r'([가-힣]+(?:동|리|읍|면))', address_str)
                
                if num_match:
                    main_no = num_match.group(1)
                    sub_no = num_match.group(2) if num_match.group(2) else ""
                    num_str = f"{main_no}-{sub_no}" if sub_no else main_no
                    
                    for a_col in addr_cols:
                        col_str = df_parcels[a_col].fillna('').astype(str)
                        mask = col_str.str.contains(r'\b' + re.escape(num_str) + r'\b', na=False) | col_str.str.contains(re.escape(num_str), na=False)
                        if dong_match:
                            mask = mask & col_str.str.contains(dong_match.group(1), na=False)
                        
                        sub_matched = df_parcels[mask]
                        if not sub_matched.empty:
                            matched_rows = pd.concat([matched_rows, sub_matched])

        if not matched_rows.empty:
            matched_rows = matched_rows.drop_duplicates()

            all_text_arr = [str(x) for x in matched_rows.values.flatten() if pd.notna(x)]
            all_districts_text = " ".join(all_text_arr)

            # 건축물 주용도 추출
            purp_cols = [c for c in cols if any(k in c.lower() for k in ['주용도코드명', '주용도명', '주용도', '건축물용도', '용도']) and '기타' not in c]
            for p_col in purp_cols:
                for val in matched_rows[p_col].dropna().astype(str):
                    if not is_invalid_val(val):
                        found_purp = val.strip()
                        break
                if found_purp:
                    break

            # 건축물 기타용도 추출 (표제부 CSV 연동)
            etc_purp_cols = [c for c in cols if any(k in c.lower() for k in ['기타용도', '기타용도명', '기타용도코드명', 'etcpurpscdnm'])]
            for e_col in etc_purp_cols:
                for val in matched_rows[e_col].dropna().astype(str):
                    if not is_invalid_val(val):
                        found_etc_purp = val.strip()
                        break
                if found_etc_purp:
                    break

            # 용도지역 추출
            zoning_cols = [c for c in cols if any(k in c.lower() for k in ['용도지역코드명', '용도지역명', '용도지역', '지역지구명', '지역지구', '구역명', '지역구분', '지목', '구분'])]
            for z_col in zoning_cols:
                for val in matched_rows[z_col].dropna().astype(str):
                    if not is_invalid_val(val):
                        mapped_z = map_zoning(val)
                        if mapped_z:
                            found_zoning = mapped_z
                            break
                        elif not found_zoning:
                            found_zoning = val.strip()
                if found_zoning and map_zoning(found_zoning):
                    break

            # 건폐율 추출
            bcv_cols = [c for c in cols if any(k in c.lower() for k in ['건폐율', 'bldcovrt', 'bld_cov_rt'])]
            for b_col in bcv_cols:
                for val in matched_rows[b_col].dropna().astype(str):
                    if not is_invalid_val(val):
                        val_str = val.strip()
                        found_bcv = val_str + "%" if not val_str.endswith("%") else val_str
                        break
                if found_bcv:
                    break

            # 용적률 추출
            far_cols = [c for c in cols if any(k in c.lower() for k in ['용적률', '용적율', 'measrt', 'meas_rt', 'totarearat'])]
            for f_col in far_cols:
                for val in matched_rows[f_col].dropna().astype(str):
                    if not is_invalid_val(val):
                        val_str = val.strip()
                        found_far = val_str + "%" if not val_str.endswith("%") else val_str
                        break
                if found_far:
                    break

            # 지구단위계획(제1종/제2종) 전체 셀 검색
            if "1종지구단위계획" in all_districts_text or "제1종지구단위계획" in all_districts_text:
                found_district_plan = "제1종지구단위계획"
            elif "2종지구단위계획" in all_districts_text or "제2종지구단위계획" in all_districts_text:
                found_district_plan = "제2종지구단위계획"
            elif "지구단위계획" in all_districts_text:
                dp_match = re.search(r'([가-힣0-9a-zA-A]*지구단위계획[가-힣0-9a-zA-A]*)', all_districts_text)
                found_district_plan = dp_match.group(1) if dp_match else "지구단위계획구역"

    # 2. 로컬 SQLite DB 백업 검색
    if (not found_purp or not found_zoning or not found_etc_purp or not found_bcv or not found_far) and os.path.exists(LOCAL_DB_PATH):
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='building_info'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(building_info)")
                db_cols = [col[1] for col in cursor.fetchall()]
                
                db_purp_col = next((c for c in db_cols if any(k in c.lower() for k in ['주용도', 'mainpurpscdnm', '용도명', '건축물용도']) and '기타' not in c), None)
                db_etc_purp_col = next((c for c in db_cols if any(k in c.lower() for k in ['기타용도', 'etcpurpscdnm'])), None)
                db_zoning_col = next((c for c in db_cols if any(k in c.lower() for k in ['용도지역', '지역구분', 'prposarea', '지목'])), None)
                db_bcv_col = next((c for c in db_cols if any(k in c.lower() for k in ['건폐율', 'bldcovrt', 'bld_cov_rt'])), None)
                db_far_col = next((c for c in db_cols if any(k in c.lower() for k in ['용적률', '용적율', 'measrt', 'meas_rt'])), None)

                num_match = re.search(r'(\d+)(?:-(\d+))?', address_str)
                if num_match:
                    main_no = num_match.group(1)
                    sub_no = num_match.group(2) if num_match.group(2) else "0"
                    bun_z = main_no.zfill(4)
                    ji_z = sub_no.zfill(4)

                    cursor.execute("SELECT * FROM building_info WHERE (번 = ? OR 번 = ?) AND (지 = ? OR 지 = ?) LIMIT 1",
                                   (main_no, bun_z, sub_no, ji_z))
                    row = cursor.fetchone()
                    if row:
                        row_dict = dict(zip(db_cols, row))
                        if not found_purp and db_purp_col and not is_invalid_val(row_dict.get(db_purp_col)):
                            found_purp = str(row_dict[db_purp_col]).strip()
                        if not found_etc_purp and db_etc_purp_col and not is_invalid_val(row_dict.get(db_etc_purp_col)):
                            found_etc_purp = str(row_dict[db_etc_purp_col]).strip()
                        if not found_zoning and db_zoning_col and not is_invalid_val(row_dict.get(db_zoning_col)):
                            found_zoning = str(row_dict[db_zoning_col]).strip()
                        if not found_bcv and db_bcv_col and not is_invalid_val(row_dict.get(db_bcv_col)):
                            val_str = str(row_dict[db_bcv_col]).strip()
                            found_bcv = val_str + "%" if not val_str.endswith("%") else val_str
                        if not found_far and db_far_col and not is_invalid_val(row_dict.get(db_far_col)):
                            val_str = str(row_dict[db_far_col]).strip()
                            found_far = val_str + "%" if not val_str.endswith("%") else val_str
                        
                        row_str = " ".join([str(v) for v in row if v is not None])
                        all_districts_text += " " + row_str
                        if not found_district_plan:
                            if "1종지구단위계획" in row_str or "제1종지구단위계획" in row_str:
                                found_district_plan = "제1종지구단위계획"
                            elif "2종지구단위계획" in row_str or "제2종지구단위계획" in row_str:
                                found_district_plan = "제2종지구단위계획"
                            elif "지구단위계획" in row_str:
                                found_district_plan = "지구단위계획구역"
            conn.close()
        except Exception:
            pass

    return found_purp, found_zoning, found_district_plan, found_etc_purp, found_bcv, found_far, all_districts_text


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

st.markdown("---")

# 3. 대상 부동산 기본 팩트 입력
st.subheader("📝 2. 대상 부동산 기본 팩트 및 지번 입력")

property_type = st.radio("중개 대상물 형태 선택", ["상가 / 일반 건축물", "산업단지 내 공장 (지번 조회)"], key="main_property_type_radio")

# 지번 및 층수 입력 필드
col_addr1, col_addr2 = st.columns([2, 1])
with col_addr1:
    input_jibun = st.text_input("📍 대상 건물 지번 입력 (예: 경상남도 양산시 중부동 410 또는 물금읍 범어리)", placeholder="전체 주소 또는 지번을 입력하세요", key="main_input_jibun")
with col_addr2:
    floor_num = st.number_input("건물 층수 (지하층 음수)", min_value=-5, max_value=50, value=1, key="main_floor_num")

# 세션 상태 초기화
if 'main_zoning_select' not in st.session_state:
    st.session_state["main_zoning_select"] = "제2종일반주거지역"
if 'main_bld_use_select' not in st.session_state:
    st.session_state["main_bld_use_select"] = "제1종근린생활시설"
if 'district_plan_info' not in st.session_state:
    st.session_state["district_plan_info"] = "해당없음 / 미지정"
if 'etc_purp_info' not in st.session_state:
    st.session_state["etc_purp_info"] = "해당없음 / 미등록"
if 'bcv_info' not in st.session_state:
    st.session_state["bcv_info"] = "정보없음"
if 'far_info' not in st.session_state:
    st.session_state["far_info"] = "정보없음"
if 'zoning_reason_info' not in st.session_state:
    st.session_state["zoning_reason_info"] = ""
if 'zoning_restrictions_info' not in st.session_state:
    st.session_state["zoning_restrictions_info"] = []

# -----------------------------------------------------------------------------
# 🎯 [양산시 로컬 CSV + 카카오 맵 정제 기반 통합 정밀 연동 로직]
# -----------------------------------------------------------------------------
if st.button("🔍 지번 정제 및 실제 용도지역/건축물대장 조회 (로컬 CSV 통합 연동)", key="api_lookup_btn"):
    if not input_jibun:
        st.warning("⚠ 조회할 지번을 입력해주세요.")
    else:
        with st.spinner("카카오맵으로 주소를 정제하고 연동된 로컬 CSV 파일에서 데이터를 조회 중입니다..."):
            try:
                # Step 1: 카카오맵 API를 통해 지도 위치 정제
                url = "https://dapi.kakao.com/v2/local/search/address.json"
                headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
                params = {"query": input_jibun}
                
                kakao_res = requests.get(url, headers=headers, params=params, timeout=5)
                
                if kakao_res.status_code == 200 and kakao_res.json().get('documents'):
                    doc = kakao_res.json()['documents'][0]
                    exact_address = doc.get('address_name', '')
                    lat = float(doc['y'])
                    lon = float(doc['x'])
                    
                    st.success(f"📍 **카카오맵 주소 정제 완료:** {exact_address}")
                    st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=16)

                    # Step 2: 연동된 양산시 모든 로컬 CSV 파일 및 DB에서 데이터 자동 조회
                    real_main_purp, real_zoning, real_district_plan, real_etc_purp, real_bcv, real_far, all_districts_text = search_local_csv_and_db(input_jibun)

                    # 스마트 매칭 및 선택상자(Dropdown) 자동 동기화 (용도지역)
                    matched_z = map_zoning(real_zoning)
                    
                    if matched_z:
                        st.session_state["main_zoning_select"] = matched_z
                        st.success(f"✅ **[용도지역 자동 선택 완료]** `{matched_z}` (조회 데이터: {real_zoning})")
                    else:
                        if real_zoning and not is_invalid_val(real_zoning):
                            st.info(f"📋 **[조회된 용도지역]**: `{real_zoning}` → 목록에 정확히 일치하는 항목이 없어 직접 선택해 주세요.")
                        else:
                            st.info("💡 연동 데이터에 용도지역 정보가 없거나 미등록 필지입니다. 용도지역 목록에서 선택해 주세요.")

                    # 조례상 건축제한 동적 산출 (조례 제31조~제51조 분석)
                    current_sel_zoning = st.session_state.get("main_zoning_select")
                    restriction_list = get_building_restriction_info(current_sel_zoning, all_districts_text)
                    st.session_state["zoning_restrictions_info"] = restriction_list

                    # 주용도 또는 기타용도를 기준으로 스마트 매칭 (나대지 예외 처리 포함)
                    matched_bld = None
                    if real_main_purp and not is_invalid_val(real_main_purp):
                        matched_bld = map_building_use(real_main_purp)
                    elif real_etc_purp and not is_invalid_val(real_etc_purp):
                        matched_bld = map_building_use(real_etc_purp)
                        
                    is_empty_land = False
                    if not matched_bld and (not real_main_purp or is_invalid_val(real_main_purp)):
                        # 건물이 없는 경우 '나대지'로 처리
                        matched_bld = "나대지(건축물없음)"
                        is_empty_land = True
                        st.session_state["main_bld_use_select"] = matched_bld
                        st.success("✅ **[건축물 주용도 자동 선택 완료]** 대장에 건축물 정보가 없어 `나대지(건축물없음)`로 자동 설정되었습니다.")
                    elif matched_bld:
                        st.session_state["main_bld_use_select"] = matched_bld
                        disp_src = real_main_purp if real_main_purp else f"기타용도({real_etc_purp})"
                        st.success(f"✅ **[건축물 주용도 자동 선택 완료]** `{matched_bld}` (조회 데이터: {disp_src})")
                    else:
                        if real_main_purp and not is_invalid_val(real_main_purp):
                            st.info(f"📋 **[조회된 주용도 코드/원문]**: `{real_main_purp}` → 목록에서 가장 가까운 용도를 선택해 주세요.")
                        else:
                            st.info("💡 연동 데이터에 건축물 주용도 정보가 없거나 미등록 필지입니다. 목록에서 수동 선택해 주세요.")

                    # Step 3: 기타용도 확인 및 상태 저장
                    if not is_empty_land and real_etc_purp and not is_invalid_val(real_etc_purp):
                        st.session_state["etc_purp_info"] = real_etc_purp
                        st.success(f"🏷️ **[건축물 기타용도 확인]** `{real_etc_purp}`")
                    else:
                        st.session_state["etc_purp_info"] = "해당없음 / 미등록"

                    # Step 4: 건폐율 / 용적률 조례 심층 분석 (완화/특례 자동 적용)
                    target_b = st.session_state.get("main_target_biz_select", "")
                    
                    zoning_limit_text = ""
                    if current_sel_zoning:
                        m_bcv, m_far, reason = calculate_dynamic_limits(current_sel_zoning, all_districts_text, target_b)
                        if m_bcv:
                            st.session_state["zoning_reason_info"] = reason
                            zoning_limit_text = f" (조례상 최대한도 - 건폐율: {m_bcv} / 용적률: {m_far})"
                    
                    # 건물 존재 여부에 따른 표시 분기
                    if not is_empty_land and real_bcv and not is_invalid_val(real_bcv) and real_far and not is_invalid_val(real_far):
                        st.session_state["bcv_info"] = real_bcv
                        st.session_state["far_info"] = real_far
                        st.success(f"📐 **[현재 건축물 건폐율/용적률 확인]** 건폐율: `{real_bcv}` / 용적률: `{real_far}`\n\n💡 {zoning_limit_text}\n- 적용 근거: {st.session_state['zoning_reason_info']}")
                    else:
                        # 건물이 없는 나대지인 경우 선택된 용도지역의 조례 한도 적용
                        if is_empty_land and current_sel_zoning and m_bcv:
                            st.session_state["bcv_info"] = f"나대지 (조례 한도: {m_bcv})"
                            st.session_state["far_info"] = f"나대지 (조례 한도: {m_far})"
                            st.success(f"📐 **[나대지 신축 가능 한도]** 양산시 조례상 최대한도 - 건폐율: `{m_bcv}` / 용적률: `{m_far}`\n\n- 적용 근거: {st.session_state['zoning_reason_info']}")
                        else:
                            st.session_state["bcv_info"] = "정보없음"
                            st.session_state["far_info"] = "정보없음"
                            st.info("💡 건축물대장상 건폐율 및 용적률 정보가 없습니다. 나대지이거나 미기재된 상태일 수 있습니다.")

                    # Step 5: 지구단위계획 (제1종/제2종 등) 정보 자동 감지 및 상태 저장
                    if real_district_plan:
                        st.session_state["district_plan_info"] = real_district_plan
                        st.success(f"🏗️ **[지구단위계획 확인]** `{real_district_plan}` 구역 지정 필지입니다.")
                    else:
                        st.session_state["district_plan_info"] = "해당없음 / 미지정"
                        st.info("💡 일반 지구단위계획 미지정 필지입니다.")

                else:
                    st.error("⚠️ 주소를 찾을 수 없습니다. 정확한 양산시 지번(예: 양산시 중부동 410)을 입력하세요.")
            except Exception as e:
                st.error(f"로컬 CSV 연동 및 조회 중 오류가 발생했습니다: {e}")

# 선택 박스: 용도지역과 건축물대장 주용도가 자동 매칭 시 바로 반영됨
st.markdown("---")
col_z1, col_z2 = st.columns(2)
with col_z1:
    zoning = st.selectbox(
        "토지 용도지역 (자동 감지 또는 수동 선택)", 
        zoning_options, 
        key="main_zoning_select"
    )
with col_z2:
    bld_use = st.selectbox(
        "건축물대장 주용도 (자동 감지 또는 수동 선택)", 
        general_building_uses, 
        key="main_bld_use_select"
    )

# 건축물대장 및 지구단위계획/기타용도/건폐율/용적률 상태 표시 박스
current_dp = st.session_state.get("district_plan_info", "해당없음 / 미지정")
current_etc = st.session_state.get("etc_purp_info", "해당없음 / 미등록")
current_bcv = st.session_state.get("bcv_info", "정보없음")
current_far = st.session_state.get("far_info", "정보없음")
current_reason = st.session_state.get("zoning_reason_info", "")

# UI 동적 업데이트를 위한 실시간 조례 적용 (나대지일 때 수동으로 용도지역 변경 시 상태 즉시 반영)
if bld_use == "나대지(건축물없음)" and zoning in yangsan_zoning_limits_base:
    # 수동 변경 시 원칙 기준 표시
    current_bcv = f"나대지 (조례 한도: {yangsan_zoning_limits_base[zoning]['bcv']}%)"
    current_far = f"나대지 (조례 한도: {yangsan_zoning_limits_base[zoning]['far']}%)"

st.info(f"📋 **[현재 설정 상태]:** 용도지역(`{zoning}`) | 주용도(`{bld_use}`) | 기타용도(`{current_etc}`) | 건폐율(`{current_bcv}`) | 용적률(`{current_far}`) | 지구단위계획(`{current_dp}`)")

# [양산시 도시계획 조례] 건축 제한 규정 자동 표시 영역
restriction_logs = st.session_state.get("zoning_restrictions_info", [])
if restriction_logs:
    with st.expander("🏛️ **양산시 도시계획 조례 (제31조~제51조) 건축 제한 요약 보기**", expanded=True):
        for log in restriction_logs:
            st.markdown(log)

col_f1, col_f2 = st.columns(2)
with col_f1:
    area = st.number_input("바닥면적 / 전용면적 (㎡)", min_value=0.0, value=100.0, help="해당 업종이 실제로 사용할 면적", key="main_area_input")
with col_f2:
    has_school_zone = st.checkbox("🎓 학교환경위생정화구역 저촉 여부", value=False, key="main_school_zone_check")

# 산단 및 지역 지번별 자동 조회 변수
selected_parcel_row = None
auto_detected_code = ""
auto_detected_name = ""

if property_type == "산업단지 내 공장 (지번 조회)":
    st.markdown("---")
    st.subheader("🏭 산단 및 지역 지번별 허용 업종코드 자동 조회")
    if df_parcels is not None and not df_parcels.empty:
        cols = df_parcels.columns.tolist()
        jibun_col = next((c for c in cols if any(k in c.lower() for k in ['지번', '소재지', '주소', '대지위치'])), cols[0])
        road_col = next((c for c in cols if '도로' in c.lower()), cols[1] if len(cols) > 1 else jibun_col)

        if 'ind_search_kw' not in st.session_state:
            st.session_state.ind_search_kw = ""

        search_kw = st.text_input("🔍 산단 내 지번 또는 도로명 검색", placeholder="예: 어곡동 865-23 또는 865", key="ind_search_input_field")
        
        if search_kw != st.session_state.ind_search_kw:
            st.session_state.ind_search_kw = search_kw

        clean_kw = search_kw.replace(" ", "")
        
        s_jibun = df_parcels[jibun_col].fillna('').astype(str).str.replace(" ", "")
        s_road = df_parcels[road_col].fillna('').astype(str).str.replace(" ", "")

        if clean_kw:
            f_df = df_parcels[
                s_jibun.str.contains(clean_kw, na=False) | 
                s_road.str.contains(clean_kw, na=False)
            ]
        else:
            f_df = df_parcels
        
        if len(f_df) > 0:
            parcel_options = f_df[jibun_col].fillna('').astype(str).unique().tolist()
            sel_addr = st.selectbox("조회된 필지(지번) 선택", parcel_options, key="ind_parcel_selectbox_field")
            selected_parcel_row = f_df[f_df[jibun_col].fillna('').astype(str) == sel_addr].iloc[0]
            
            code_col = next((c for c in cols if '코드' in c or '업종' in c), cols[2] if len(cols) > 2 else '')
            name_col = next((c for c in cols if '명' in c or '품목' in c), cols[3] if len(cols) > 3 else '')
            
            auto_detected_code = str(selected_parcel_row.get(code_col, ''))
            auto_detected_name = str(selected_parcel_row.get(name_col, ''))
            st.success(f"🎯 **[지번 매칭 완료]** `{sel_addr}` (허용 업종코드/명칭: {auto_detected_code} {auto_detected_name})")
        else:
            st.warning("⚠ 일치하는 지번 또는 도로명이 없습니다. 검색어를 다시 확인해주세요.")
    else:
        st.warning("⚠️ 연동된 CSV 파일이 존재하지 않거나 로드되지 않았습니다.")

st.markdown("---")
st.subheader("🎯 3. 임차인 세부 희망 업종 및 건물 물리적 조건 선택")

comprehensive_biz_dict = {
    "🐶 반려동물 관련 영업": [
        "동물위탁관리업", "동물미용업", "동물생산업·판매업", "동물장묘업 및 동물병원"
    ],
    "🍽 일반 음식점 및 카페·디저트": [
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
    "🏋 스포츠, 레저 및 운동시설": [
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

col_b1, col_b2 = st.columns(2)
with col_b1:
    biz_category = st.selectbox("희망 업종 대분류", list(comprehensive_biz_dict.keys()), key="main_biz_category_select")
with col_b2:
    target_biz = st.selectbox("세부 희망 업종 선택", comprehensive_biz_dict[biz_category], key="main_target_biz_select")

# 임차 세부 시설 및 건축물 물리적 조건 선택
current_power = st.number_input("현재 호실 계약전력 (kW)", min_value=1.0, value=10.0, step=1.0, key="main_current_power_input")

submitted = st.button("🚀 종합 법적 진단 리포트 생성", type="primary", key="main_submit_btn")

if submitted:
    st.markdown("---")
    
    fatal_errors = []
    warnings = []
    legal_actions = []

    # 나대지 신축 가이드라인 특례 추가
    if bld_use == "나대지(건축물없음)":
        warnings.append(
            f"🚧 **[나대지 신축 검토]** 해당 부지는 현재 건축물이 없는 나대지 상태입니다. "
            f"'{target_biz}' 업종을 위한 신축 시, 해당 용도지역(`{zoning}`)의 양산시 조례상 건폐율/용적률 한도 및 도로 접도 조건, 건축선 후퇴 등을 관할 건축과와 필히 사전 협의해야 합니다."
        )

    # 지구단위계획 특약 안내 추가
    dp_state = st.session_state.get("district_plan_info", "")
    if dp_state and dp_state != "해당없음 / 미지정":
        legal_actions.append(
            f"🏗️ **[지구단위계획 지정 필지 - {dp_state}]** 해당 지번은 **{dp_state}** 지정 구역입니다. "
            f"지구단위계획 구역 내에서는 일반 용도지역상 허용 업종이더라도 **양산시 지구단위계획 결정도서 및 허용/권장/불허 용도 지침**이 우선 적용되므로 관할 관청(도시개발과/건축과)에 개별 지침을 반드시 교차 확인하세요. (근거: 국토의 계획 및 이용에 관한 법률 제52조)"
        )

    # 1. 용도지역 제한 검증 (국토계획법 제76조)
    if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
        prohibited_list = zoning_restrictions[zoning]["prohibited"]
        for p in prohibited_list:
            if p in target_biz or p in biz_category or (p == "위락시설" and target_biz in ["무도장 및 카지노업소", "유흥주점", "단란주점"]):
                fatal_errors.append(
                    f"[국토계획법 제76조 및 동법 시행령 제71조 별표 위반] '{zoning}' 지역에서는 국토의 계획 및 이용에 관한 법률에 따라 "
                    f"'{target_biz}'의 입점 및 영업이 법적으로 원천 금지되어 있습니다. "
                    f"💡 **해결 대안:** 해당 용도지역 내에서는 허용되지 않으므로, 상업지역 등 해당 업종이 허용되는 다른 입지로 물건을 변경해야 합니다."
                )

    # 3. 학교정화구역 검증 (교육환경 보호에 관한 법률 제9조)
    if has_school_zone:
        if any(kw in target_biz for kw in ["유흥주점", "단란주점", "PC방", "노래연습장", "숙박", "당구장", "청소년게임제공업", "인형뽑기방", "무도장", "카지노"]):
            fatal_errors.append(
                f"[교육환경 보호에 관한 법률 제9조 위반] 본 물건지는 학교환경위생정화구역(교육환경보호구역) 내에 위치하고 있어 '{target_biz}'의 영업이 원칙적으로 금지됩니다. "
                f"💡 **해결 대안:** 절대보호구역인 경우 영업이 절대 불가능하며, 상대보호구역인 경우 관할 양산교육지원청 교육환경보호위원회 심의를 통과해야만 허가 가능합니다."
            )

    # 4. 건축법 주용도 및 면적별 진단 로직 (건축법 제19조 및 동법 시행령 별표 1) + 개별법 종합
    if property_type == "상가 / 일반 건축물" and bld_use != "나대지(건축물없음)":
        
        if "세탁소" in target_biz:
            if bld_use != "제1종근린생활시설":
                warnings.append(
                    f"[세탁소 입점 대안 및 용도변경 가이드 - 건축법 제19조] "
                    f"현재 건축물대장 주용도가 **'{bld_use}'**이므로 그대로는 세탁소 영업을 할 수 없습니다. "
                    f"💡 **[합법화 대안]** 관할 관청(양산시 건축과)에 **'건축물 표시변경(또는 용도변경)'**을 신청하여 주용도를 **'제1종근린생활시설'**로 변경하시면 합법적으로 입점 가능합니다. \n"
                    f"※ 실무 체크포인트: 대기환경보전법상 일정 용량 이상의 드라이클리닝 장비 사용 시 배출시설 신고 대상이며, 하수도법에 따른 정화조 용량 증설 요건을 건물 관리소에 반드시 확인하세요."
                )
            else:
                legal_actions.append("👕 **[세탁소 적합]** 건축물대장 주용도가 '제1종근린생활시설'로 완벽하게 부합합니다. (단, 드라이클리닝 용제 규제 및 대기배출시설 신고 여부 확인)")

        elif "동물위탁관리업" in target_biz: # 애견호텔, 유치원 등
            if area >= 300.0:
                if bld_use != "동물관련시설":
                    warnings.append(
                        f"[동물위탁시설(300㎡이상) 합법화 대안 - 동물보호법 및 건축법 시행령] 면적 300㎡ 이상 동물위탁시설은 건축물대장 주용도가 **'동물관련시설'**로 기재되어 있어야 영업 등록이 가능합니다. (현재: {bld_use}, 면적: {area}㎡)\n\n"
                        f"💡 **[실무 체크포인트 및 대안]**\n"
                        f"1. **용도변경 필수:** 건축법 제19조에 따라 기존 용도에서 '동물관련시설'로 정식 용도변경 허가 절차를 거쳐야 합니다.\n"
                        f"2. **시설 기준 충족:** 동물보호법에 따른 이중문, 방음설비, 환기시설, 격리실 등을 도면에 반영하여 용도변경 심사를 통과해야 합니다."
                    )
                else:
                    legal_actions.append("🐶 **[동물관련시설 적합 - 300㎡ 이상]** 건축물대장 주용도가 '동물관련시설'로 적법하게 부합합니다. (동물보호법상 독립된 공간, 방음·방취 공사 시공 여부를 확인하세요.)")
            else: # 300 미만
                if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설"]:
                    warnings.append(
                        f"[동물위탁시설(300㎡미만) 합법화 대안 - 건축법 시행령] 300㎡ 미만은 **'제2종근린생활시설'**(또는 제1종)에서 가능하나 현재 주용도({bld_use})로는 불가합니다. \n\n"
                        f"💡 **[합법화 대안]**\n"
                        f"1. **면적 합산 주의:** 건물 내 다른 동물관련영업장 면적을 합산해 300㎡가 넘으면 전체가 '동물관련시설'로 간주되니 합산 면적을 필히 확인하세요.\n"
                        f"2. **표시변경 신고:** 합산 면적이 300㎡ 미만이라면 **'제2종근린생활시설'**로 대장 기재내용 표시변경을 신청하여 입점할 수 있습니다."
                    )
                else:
                    legal_actions.append(f"🐶 **[근린생활시설 적합 - 300㎡ 미만]** 주용도({bld_use}) 요건에 부합합니다. (단, 건물 내 타 동물시설 합산 면적이 300㎡ 미만인지 반드시 교차 검증하세요.)")
        
        elif "동물미용업" in target_biz or "동물생산업·판매업" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설"]:
                warnings.append(
                    f"[동물미용/판매업 합법화 대안 - 건축법 시행령] 해당 업종은 **'제1·2종 근린생활시설'** 또는 **'동물관련시설'**이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 건축물 **표시변경**을 통해 주용도를 근린생활시설로 변경한 뒤 입점하세요. (동물보호법에 따른 소독장비, 격리실 구비 요건을 충족해야 합니다.)"
                )
            else:
                legal_actions.append("🐾 **[동물미용/판매업 적합]** 건축물 용도에 적합합니다. 동물보호법 시설기준(격리실, 급수시설 등) 준수가 요구됩니다.")

        elif "일반음식점" in target_biz or "휴게음식점" in target_biz or "제과점" in target_biz:
            is_huge = "일반" not in target_biz and area >= 300.0 # 휴게, 제과점 중 300이상
            required_use = "제2종근린생활시설" if "일반음식점" in target_biz or is_huge else "제1종근린생활시설"
            
            if ("일반음식점" in target_biz and bld_use not in ["제2종근린생활시설", "판매시설", "숙박시설"]) or (not "일반음식점" in target_biz and bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "판매시설"]):
                warnings.append(
                    f"[음식·휴게업 합법화 대안 - 식품위생법 제37조 / 건축법 제19조] 현재 건축물대장 주용도({bld_use})에서는 영업 신고증 발급이 불가합니다.\n\n"
                    f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                    f"1. **시설군 요건:** 일반음식점은 반드시 **'제2종근린생활시설'** 이상이어야 하며, 휴게/제과점은 300㎡ 미만 시 1종, 이상 시 2종 근생이어야 합니다.\n"
                    f"2. **다중이용업소 소방필증:** 영업장 면적이 지하층 66㎡ 이상이거나 지상 2층 이상 100㎡ 이상인 경우, **'다중이용업소의 안전관리에 관한 특별법'**의 적용을 받아 완강기, 비상구 등 소방시설완비증명서를 반드시 발급받아야 합니다.\n"
                    f"3. **정화조/주차장:** 표시변경(용도변경) 신청 시 건물 전체 정화조 용량 초과분 및 주차 대수 증가분을 반드시 해결해야 인허가가 납니다."
                )
            else:
                legal_actions.append(
                    f"🍽 **[음식점 창업 적합]** 식품위생법에 따른 위생교육, 수질검사 성적서 구비. (단, 지하 66㎡ 또는 2층 이상 100㎡ 이상 시 다중이용업소 소방완비증명서 발급 의무)"
                )

        elif "식육판매업" in target_biz: # 정육점
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설"]:
                warnings.append(
                    f"[식육판매업 합법화 대안 - 축산물 위생관리법 제21조] 주용도가 제1종 또는 제2종 근린생활시설이어야 영업 신고가 가능합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 관할 지자체에 **표시변경**을 통해 주용도를 **'제1종 또는 제2종 근린생활시설'**로 변경해야 합니다."
                )
            else:
                legal_actions.append("🥩 **[식육판매업 적합]** 냉장·냉동 쇼케이스 구비 및 계약전력(전기용량) 확인 필수.")

        elif "유흥주점" in target_biz or "단란주점" in target_biz or "무도장 및 카지노업소" in target_biz:
            req_use = "위락시설" if "단란" not in target_biz or area >= 150 else "제2종근린생활시설"
            
            if ("단란" in target_biz and area < 150 and bld_use not in ["제2종근린생활시설", "위락시설"]) or (req_use == "위락시설" and bld_use != "위락시설"):
                fatal_errors.append(
                    f"[건축법 위반 / 입점 제한 - 건축법 시행령 별표1] 유흥주점 및 무도장은 반드시 주용도가 **'위락시설'**이어야 하며, 단란주점은 150㎡ 미만일 때만 제2종근생이 가능합니다. (현재 주용도: {bld_use}, 면적: {area}㎡)\n\n"
                    f"💡 **[치명적 실무 체크포인트]** 일반 상가건물을 '위락시설'로 용도변경하는 것은 건축법상 주차 대수 및 소방 기준이 매우 가혹하여 현실적으로 불가능에 가깝습니다. 처음부터 대장상 주용도가 **'위락시설'**로 허가난 매물만 중개/계약해야 합니다."
                )
            else:
                legal_actions.append(
                    f"🍺 **[위락/유흥시설 적합]** 대장상 주용도 요건에 부합합니다.\n"
                    f"💡 [주의] 유흥주점은 지방세법상 '고급오락장'으로 분류되어 취득세 및 재산세 중과세(약 10% 이상)가 부과될 수 있으므로 임대인과의 세금 부담 특약을 반드시 체결하세요. (다중이용업소 소방완비증명서 필수)"
                )
        
        elif "일반주점·맥주집" in target_biz:
            if bld_use not in ["제2종근린생활시설", "위락시설", "판매시설"]:
                warnings.append(
                    f"[일반주점 합법화 대안 - 식품위생법 시행령 제21조] 주용도가 **'제2종근린생활시설(일반음식점)'** 이상이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 관할 관청에 건축물 **표시변경**을 신청하여 주용도를 '제2종근린생활시설'로 변경해야 주류 판매가 동반된 음식점 영업 신고가 가능합니다."
                )
            else:
                legal_actions.append("🍻 **[일반주점 적합]** 식품위생법상 일반음식점 영업신고 대상. (다중이용업소 해당 여부 소방 점검 필수)")

        elif "식육포장처리업" in target_biz or "식육가공업" in target_biz or "식품제조·가공업" in target_biz or "금속가공제품 제조업" in target_biz or "인쇄소 및 출판업" in target_biz:
            if bld_use != "공장":
                if bld_use in ["제2종근린생활시설", "제1종근린생활시설"] and area < 500.0:
                    warnings.append(
                        f"[제조업소(근생) 합법화 실무 가이드 - 건축법 시행령 별표1] 현재 주용도가 근린생활시설이고 면적({area}㎡)이 500㎡ 미만이므로 '공장'이 아니더라도 **합법 입점 가능성이 매우 높습니다!**\n\n"
                        f"💡 **[건축물대장 세부 표기 추가 필수]** 단, 대장에 단순히 근린생활시설로만 되어 있다면 지자체 민원을 통해 대장 괄호 안에 **'(제조업소)'** 또는 **'(수리점)'**으로 구체적인 세부 용도를 기재하는 **'표시변경'** 절차를 거쳐야 지자체 공장등록 및 영업허가증 발급이 완벽하게 안전해집니다. (대기환경·물환경보전법에 따른 배출시설 설치 면제 대상인지 필히 검토 요망)"
                    )
                else:
                    warnings.append(
                        f"[공장 입점 대안 및 용도변경 가이드 - 산집법 제16조] 해당 제조업/가공업은 원칙적으로 대장상 주용도가 **'공장'**이어야 합니다. (현재: {bld_use}, 면적: {area}㎡)\n\n"
                        f"💡 **[합법화 대안]** 면적이 500㎡ 미만인 소규모 제조업의 경우, 건물을 **'제2종근린생활시설(제조업소)'**로 표시변경을 신청하면 공장이 아니어도 합법 입점이 가능합니다. 단, 환경법상 배출시설 허가 대상이 되는 오염물질을 배출한다면 근생 입주가 불가능합니다."
                    )
            else:
                legal_actions.append("🏭 **[공장 내 가공 적합 - 산집법 제16조]** 산집법에 따른 공장등록 및 환경법(수질/대기/소음·진동) 배출시설 허가 여부 서류를 검토하세요.")

        elif "냉장·냉동창고" in target_biz or "일반 물류창고" in target_biz:
            if bld_use not in ["창고시설"]:
                warnings.append(
                    f"[창고시설 합법화 대안 - 건축법 시행령 별표1] 주용도가 **'창고시설'**이어야 물류/보관업 영위가 원활합니다. (현재: {bld_use})\n\n"
                    f"💡 **[합법화 대안 및 실무 체크포인트]**\n"
                    f"1. **용도변경:** 건축물대장 주용도를 '창고시설'로 **용도변경 허가(또는 신고)**를 받아야 합니다. 창고 시설은 소방(스프링클러 등) 및 도로 폭(대형 화물차 진출입 확보) 기준 심사가 매우 엄격합니다.\n"
                    f"2. 물류창고업 등록제도에 따라 바닥면적 1,000㎡ 이상인 경우 관할 시·도지사에게 등록 의무가 있습니다."
                )
            else:
                legal_actions.append("📦 **[창고업 적합]** 대형 화물 차량 진출입을 위한 도로 접도 요건 및 소방 설비 점검을 확인하세요.")

        elif "고물상 및 폐기물재활용시설" in target_biz:
            if bld_use != "자원순환관련시설":
                warnings.append(
                    f"[자원순환시설 대안 - 폐기물관리법 제25조] 주용도가 **'자원순환관련시설'**이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 고물상은 폐기물관리법 적용 대상이며 님비(NIMBY) 시설로 분류되어 일반 상업/주거 용지에서는 용도변경 허가가 사실상 불가합니다. 자원순환관련시설로 정식 허가가 이미 난 부지나 공장지역으로 이전해야 합니다."
                )
            else:
                legal_actions.append("♻️ **[자원순환시설 적합]** 폐기물관리법에 따른 재활용업 인허가 및 주변 환경민원 발생 소지를 면밀히 체크하세요.")

        elif "병원" in target_biz or "요양병원" in target_biz:
            if bld_use != "의료시설":
                warnings.append(
                    f"[병원급 의료시설 합법화 대안 - 의료법 제33조] 30개 이상의 병상을 갖춘 '병원' 급 시설은 주용도가 반드시 **'의료시설'**이어야 합니다. (현재: {bld_use})\n\n"
                    f"💡 **[합법화 대안 및 실무 체크포인트]**\n"
                    f"일반 상가를 '의료시설'로 용도변경 신청할 수는 있으나, 소방(자동화재탐지설비, 스프링클러, 피난설비) 및 주차장 확보 기준, 피난용 승강기 설치 등 요건이 극도로 까다롭습니다. 건축사와의 사전 협의가 필수적입니다."
                )
            else:
                legal_actions.append("🏥 **[의료시설 적합]** 의료법 및 소방법에 따른 노유자/의료시설 전용 피난계단, 휠체어 램프, 스프링클러 및 의료폐기물 처리 요건 충족 필수.")

        elif "치과의원" in target_biz or "한의원" in target_biz:
            if bld_use not in ["제1종근린생활시설", "의료시설"]:
                warnings.append(
                    f"[의원급 합법화 대안 - 의료법 제33조] 의원(입원실 없음, 또는 소규모)은 주용도가 **'제1종근린생활시설'**(또는 의료시설)이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 관할 관청에 **건축물 표시변경**을 신청하여 주용도를 '제1종근린생활시설(의원)'로 변경하면 보건소 개설 신고 및 영업이 가능합니다."
                )
            else:
                legal_actions.append("🩺 **[의원급 적합]** 보건소 개설 신고 대상이며, 방사선 장치(X-ray 등) 사용 시 안전관리 요건을 충족해야 합니다.")

        elif "피트니스·헬스장" in target_biz or "수영장 및 볼링장" in target_biz:
            if area >= 500.0:
                if bld_use != "운동시설":
                    warnings.append(
                        f"[운동시설(500㎡이상) 합법화 대안 - 건축법 시행령 별표1] 건축법상 해당 용도(체력단련장)로 쓰이는 동일 건축물 내 바닥면적 합계가 500㎡ 이상이므로, 건축물대장상 주용도가 **'운동시설'**로 기재되어 있어야만 영업 허가(신고)가 가능합니다. (현재 주용도: {bld_use})\n\n"
                        f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                        f"1. **합산 면적 주의:** 본 호실 면적({area}㎡)만 계산하는 것이 아니라, 해당 건물 내 다른 헬스장, PT샵 등이 있다면 그 면적까지 모두 합산해야 합니다. 총합이 500㎡를 초과하면 전체가 '운동시설' 기준을 따르게 됩니다.\n"
                        f"2. **부대 규제 부담:** '운동시설'로 분류되면 **장애인 편의시설**(경사로, 전용 화장실, 엘리베이터 접근성 등) 설치 의무가 발생하고, 소방 안전 기준이 제2종 근린생활시설에 비해 훨씬 까다로워집니다.\n"
                        f"3. **용도변경 절차:** 관할 지자체 건축과를 통해 기존 용도({bld_use})에서 **'운동시설(5군 영업시설군)'**로 정식 용도변경 허가(또는 신고) 절차를 거쳐야 합법적인 입점이 가능합니다."
                    )
                else:
                    legal_actions.append(
                        "🏋️ **[운동시설 적합 - 500㎡ 이상]** 건축물대장 주용도가 '운동시설'로 적법하게 부합합니다. \n"
                        "💡 건물 내 다른 체육시설 면적을 합산하더라도 이미 상위군인 '운동시설'이므로 면적 초과 문제는 발생하지 않습니다. 바닥 하중 안전성 검토 및 장애인 편의시설 유지 여부를 확인하세요."
                    )
            else: # 500.0 미만
                if bld_use not in ["제2종근린생활시설", "운동시설"]:
                    warnings.append(
                        f"[체력단련장(500㎡미만) 합법화 대안 - 건축법 시행령 별표1] 바닥면적 합계가 500㎡ 미만일 경우 건축물대장 주용도가 **'제2종근린생활시설'** 또는 그 상위인 **'운동시설'**이어야 합니다. (현재 주용도: {bld_use})\n\n"
                        f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                        f"1. **면적 합산 주의:** 입력하신 면적({area}㎡)이 500㎡ 미만이더라도, 건물 내 다른 헬스장/PT샵 면적을 합산하여 500㎡가 넘는다면 상위 군인 '운동시설'로 용도변경해야 합니다.\n"
                        f"2. **용도변경 절차:** 건물 내 합산 면적이 500㎡ 미만이라면 장애인시설 의무 등 까다로운 규제를 피할 수 있습니다. 기존 용도({bld_use})에서 **'제2종근린생활시설'**로 건축물 표시변경(또는 용도변경) 절차를 진행하시면 적법한 입점이 가능합니다.\n"
                        f"3. **유의 사항:** 태권도장, 탁구장 등은 500㎡ 미만 시 '제1종근린생활시설'이지만, **헬스장(체력단련장)은 반드시 '제2종근린생활시설'**로 기재되어야 합니다."
                    )
                else:
                    if bld_use == "운동시설":
                        legal_actions.append(
                            "🏋️ **[하위 용도로의 입점 특례 - 500㎡ 미만]** 현재 대장상 주용도는 상위 시설군인 '운동시설'이며, 입점 면적은 500㎡ 미만 제2종 근생 기준에 해당합니다. 상위 용도 공간에 하위 용도 시설이 들어가는 것이므로 **건축물대장 기재내용 변경(표시변경)** 신고만으로 합법적 입점이 가능합니다."
                        )
                    else:
                        legal_actions.append(
                            "🏋️ **[제2종 근린생활시설 적합 - 500㎡ 미만]** 건축물대장 주용도(제2종근린생활시설)와 면적 요건이 완벽하게 부합합니다. \n"
                            "💡 단, 건물 내 다른 헬스장/PT샵의 면적을 모두 합산했을 때 500㎡를 초과하지 않는지 반드시 추가 확인하시기 바랍니다."
                        )

        elif "스크린골프장" in target_biz or "당구장" in target_biz:
            if bld_use not in ["제2종근린생활시설", "운동시설"]:
                warnings.append(
                    f"[스크린골프/당구장 합법화 대안 - 체육시설법 제10조] 500㎡ 미만은 **제2종근린생활시설**, 이상은 **운동시설**이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 체육시설업 신고를 위해 건축물대장을 확인 후 면적 요건에 맞게 **표시변경 또는 용도변경**을 진행하세요. 실내 골프연습장의 경우 다중이용업소 특별법에 따른 소방 기준 적용 대상입니다."
                )
            else:
                legal_actions.append("⛳ **[스크린골프/당구장 적합]** 체육시설업 신고 기준에 부합합니다. 층고 높이, 방음 시공 및 소방 완비증명서 대상 여부를 점검하세요.")

        elif "학원" in target_biz or "직업훈련소" in target_biz:
            if area >= 500.0:
                if bld_use != "교육연구시설":
                    warnings.append(
                        f"[학원(500㎡이상) 합법화 대안 - 건축법 시행령 별표1] 동일 건물 내 해당 용도로 쓰이는 바닥면적 합계가 500㎡ 이상인 학원은 주용도가 반드시 **'교육연구시설'**이어야 합니다. (현재: {bld_use}, 면적: {area}㎡)\n\n"
                        f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                        f"1. **용도변경 필수:** 관할 건축과를 통해 '교육연구시설(6군)'로 정식 용도변경 허가(또는 신고)를 득해야 양산교육지원청 학원 설립 인가가 나옵니다.\n"
                        f"2. **학원법 제5조 (유해업소 혼재 금지) ★치명적 주의★:** 동일 건물 내에 단란주점, 유흥주점, 안마시술소 등 유해업소가 단 1개라도 존재한다면 **학원 설립이 원천 금지**됩니다. 계약 전 건축물대장 및 실제 입점 상가를 전체 전수조사해야 합니다. (단, 연면적 1,650㎡ 이상 대형 상가의 경우 층이나 이격 거리에 따른 예외 허용 조항이 있으니 교육청 사전 질의 필수)"
                    )
                else:
                    legal_actions.append(
                        "📚 **[교육연구시설 적합 - 500㎡ 이상]** 건축물대장상 '교육연구시설'로 적합합니다.\n"
                        "💡 **[학원법 유해업소 혼재 확인 필수]** 건물 내에 유흥주점, 단란주점 등 유해업소가 없는지 교차 확인하시고, 피난계단(직통계단 2개소) 및 교육청 조례상 강의실 최소면적 요건을 확인하세요."
                    )
            else: # 500.0 미만
                if bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                    warnings.append(
                        f"[학원(500㎡미만) 합법화 대안 - 건축법 시행령 별표1] 바닥면적 합계가 500㎡ 미만일 경우 건축물대장 주용도가 **'제2종근린생활시설'** 또는 **'교육연구시설'**이어야 합니다. (현재: {bld_use})\n\n"
                        f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                        f"1. **면적 합산 주의:** 건물 내 다른 학원 면적을 합산해 500㎡를 넘기면 상위 군인 '교육연구시설'로 용도변경해야 합니다.\n"
                        f"2. **표시변경 절차:** 500㎡ 미만 요건 충족 시, 기존 용도를 **'제2종근린생활시설(학원)'**로 표시변경 신고하여 입점합니다.\n"
                        f"3. **유해업소 혼재 금지 (학원법):** 건물 내 단란주점 등 유해업소 존재 여부를 반드시 확인하세요. 존재 시 학원 인가가 불가능할 수 있습니다."
                    )
                else:
                    legal_actions.append(
                        "📚 **[학원업 적합 - 500㎡ 미만]** 대장상 주용도가 부합합니다. \n"
                        "💡 건물 내 타 학원 합산 면적이 500㎡를 초과하지 않는지, 유해업소(유흥주점 등)가 동일 건물 내에 없는지(학원법 제5조) 최종 확인하세요."
                    )

        elif "독서실 및 스터디카페" in target_biz:
            if bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                warnings.append(
                    f"[독서실/스카 합법화 대안 - 건축법 시행령] 면적에 따라 **'제2종근린생활시설'** 또는 **'교육연구시설'**이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 관할 건축과에 **표시변경**을 신청하여 주용도를 변경하세요. 독서실은 학원법의 적용을 받으며, 스터디카페는 휴게음식점업 등 다른 인허가와 결합될 수 있어 용도 판단 시 주의가 필요합니다."
                )
            else:
                legal_actions.append("📖 **[독서실/스카 적합]** 학원법 적용 대상(독서실) 여부에 따른 양산교육지원청 시설 기준 및 다중이용업소 소방필증 발급을 확인하세요.")

        elif "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz:
            if area >= 500.0:
                if bld_use not in ["문화및집회시설", "판매시설"]:
                    warnings.append(
                        f"[대형 PC방/노래방(500㎡이상) 합법화 대안 - 건축법 시행령] 동일 건물 내 바닥면적 합산 500㎡ 이상인 PC방/게임장 등은 더 이상 제2종근생이 아닌 **'판매시설'** 또는 **'문화및집회시설'**로 분류됩니다. (현재: {bld_use})\n\n"
                        f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                        f"1. **강력한 규제 적용:** 판매/문화집회 시설로 용도변경 시 주차장 폭증, 장애인 편의시설, 구조안전(하중) 등 허가 기준이 막대하게 까다로워집니다.\n"
                        f"2. 다중이용업소 특별법에 따라 직통(피난)계단 2개소 이상 확보가 필수적입니다."
                    )
                else:
                    legal_actions.append("🕹️ **[대형 인터넷컴퓨터게임시설 적합]** 건축물대장상 대규모 영업 용도에 적합합니다. 학교환경위생정화구역 및 소방안전시설 요건을 철저히 검토하세요.")
            else:
                if bld_use not in ["제2종근린생활시설", "문화및집회시설", "판매시설"]:
                    warnings.append(
                        f"[PC방/노래연습장(500㎡미만) 합법화 대안 - 게임산업법 / 음악산업법] 500㎡ 미만 영업장은 주용도가 **'제2종근린생활시설'**이어야 합니다. (현재: {bld_use})\n\n"
                        f"💡 **[실무 체크포인트 및 합법화 대안]**\n"
                        f"1. 관할 관청에 **표시변경**을 신청하여 주용도를 '제2종근린생활시설'로 변경하면 합법 영업 허가(등록)가 가능합니다.\n"
                        f"2. 본 업종은 대표적인 **다중이용업소**입니다. 지하층 또는 지상 밀폐 구조일 경우 소방 방염/비상구/피난계단 심사가 매우 까다로우니 소방서 사전 협의가 권장됩니다."
                    )
                else:
                    legal_actions.append("🕹️ **[PC방/노래연습장 적합 - 500㎡ 미만]** 주용도 요건을 충족합니다. 양산교육지원청 상대정화구역 심의 여부 및 관할 소방서 완비증명서 발급 요건을 체크하세요.")

        elif "세차장" in target_biz:
            if bld_use != "자동차관련시설":
                warnings.append(
                    f"[세차장 합법화 대안 - 건축법 시행령 및 하수도법] 세차장업은 대장상 주용도가 반드시 **'자동차관련시설'**이어야 합니다. (현재: {bld_use})\n\n"
                    f"💡 **[합법화 대안 및 실무 체크포인트]**\n"
                    f"1. 관할 건축과에 '자동차관련시설'로 정식 **용도변경** 허가를 진행해야 합니다.\n"
                    f"2. 하수도법 및 물환경보전법에 따라 오수 및 폐수 정화시설(유수분리기 포함) 설치와 배출시설 허가가 선행되어야 영업증이 나옵니다."
                )
            else:
                legal_actions.append("🚗 **[세차장 적합]** 오수 정화시설, 유수분리기 적합 설치 여부 및 환경과 폐수배출시설 신고를 진행하세요.")

        elif "자동차정비공장" in target_biz or "자동차매매장" in target_biz:
            if bld_use != "자동차관련시설":
                warnings.append(
                    f"[카센터 / 정비소 합법화 및 표시변경 가이드 - 자동차관리법 제53조]\n"
                    f"자동차 정비공장/매매장은 원칙적으로 '자동차관련시설'이어야 합니다. (현재 주용도: {bld_use})\n\n"
                    f"💡 **[핵심 실무 꿀팁 (소규모 카센터 특례)]**\n"
                    f"만약 현재 건물의 주용도가 **'제2종근린생활시설'**이면서 대장 괄호 안에 **'(수리점)'** 등으로 세부 표기가 되어 있거나, 면적이 500㎡ 미만인 상가에서 관할 관청에 **'제2종근린생활시설 (수리점)'**으로 표시변경을 할 수 있다면, 굳이 자동차관련시설이 아니어도 소규모 카센터 영업이 합법적으로 허용됩니다!"
                )
            else:
                legal_actions.append("🔧 **[정비공장/매매장 적합]** 주용도가 '자동차관련시설'로 완벽하게 부합합니다. 오일/폐수 처리 시설 요건을 검토하세요.")

        elif "일반 숙박업" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 제한 - 공중위생관리법 제3조] 일반숙박업(모텔/호텔 등)은 주용도가 반드시 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use})\n\n"
                    f"💡 **[중요한 현실적 대안]** 일반 상가나 주택, 오피스 건물을 숙박시설로 용도변경하는 것은 양산시 조례, 주차장법, 소방법(스프링클러 완비), 정화조 용량 등 모든 면에서 법적으로 불가능에 가깝습니다. 처음부터 주용도가 **'숙박시설'**로 허가난 물건만을 중개/계약하셔야 합니다."
                )
            else:
                legal_actions.append("🏨 **[숙박업 적합]** 공중위생관리법에 따른 숙박업 영업신고 및 관할 소방서 소방시설완비증명서(방염필증 포함) 발급 필수 대상입니다.")

        elif "생활숙박시설" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 제한 - 건축법 시행령 별표1] 생활숙박시설(레지던스, 취사 가능 숙박업)은 반드시 주용도가 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use})\n"
                    f"💡 **[중요한 대안]** 주용도가 '숙박시설'로 최초 건축 허가된 물건만 취득 및 운영할 수 있습니다."
                )
            else:
                warnings.append(
                    "[주거용 불법 전용 규제 주의 - 건축법 제19조] 생활숙박시설은 공중위생관리법상 반드시 '숙박업' 신고를 하고 영리 목적으로 운영해야 합니다. 전입신고 후 일반 주거용으로 불법 사용할 경우 건축법상 이행강제금 부과 대상이 되므로 계약자에게 고지 필수입니다."
                )
                legal_actions.append("🏨 **[생활숙박시설 적합]** 위탁운영사 위탁계약 여부, 주차장 설치 기준, 소방 완비증명서 발급 여부를 확인하세요.")

        elif "오피스텔 에어비앤비" in target_biz:
            fatal_errors.append(
                "[형사 처벌 대상 / 불법 숙박영업 - 공중위생관리법 제3조 및 건축법 제19조] 오피스텔은 건축법상 '업무시설'로 분류되므로, 공중위생관리법에 따른 숙박업 합법 등록이 원천적으로 불가능합니다. 단기 임대가 아닌 에어비앤비 숙박 영업 시 형사고발 대상이 됩니다.\n\n"
                "💡 **해결 대안:** 에어비앤비 등 공유 숙박을 합법적으로 하려면 대장상 '생활숙박시설(레지던스)' 물건을 찾거나, 주택(단독/다세대/아파트)에서 '외국인관광 도시민박업'을 등록하셔야 합니다."
            )

        elif "외국인관광 도시민박업" in target_biz:
            if bld_use not in ["단독/다세대/아파트(주택류)"]:
                fatal_errors.append(
                    f"[관광진흥법 시행령 제2조 위반] 외국인관광 도시민박업은 사업자가 실제 거주하고 있는 주택(단독·다세대·연립·아파트)에서만 등록이 가능합니다. (상가/근생 불가) (현재 주용도: {bld_use})\n"
                    f"💡 **해결 대안:** 건축물대장상 용도가 '주택'으로 명시된 물건으로 한정하여 매물을 찾아야 합니다."
                )
            else:
                legal_actions.append("🏡 **[외국인관광 도시민박업 적합]** 관광진흥법에 따른 도시민박업 지정 신청 조건에 부합합니다. 외국어 안내 서비스 및 단독 소방안전시설(일산화탄소 경보기 등) 기준 준수가 요구됩니다.")

        elif "펜션 및 휴양콘도미니엄" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 및 관련 규정 위반 - 관광진흥법 제3조] 펜션 및 휴양콘도미니엄은 주용도가 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use})\n"
                    f"💡 **해결 대안:** 대장상 숙박시설로 허가된 부지 및 건물만 계약/운영이 가능합니다."
                )
            else:
                warnings.append(
                    "[개별 인허가법 주의] 일반적인 펜션은 건축법상 '숙박시설' 용도 외에도 농어촌지역일 경우 '농어촌정비법'에 따른 농어촌민박업 등록 요건, 관광지일 경우 '관광진흥법'에 따른 사업 승인 요건을 개별적으로 충족해야 합니다."
                )
                legal_actions.append("🏡 **[펜션/콘도 적합]** 양산시 관련 부서(농정기획과 또는 문화관광과)에 인허가 가능 여부를 확인하고, 산지/농지 등 외곽 지역의 경우 개인 오수처리시설(정화조) 용량 및 상수도 인입 여부를 최우선 검토하세요.")

        elif "일반미용업·헤어샵" in target_biz or "네일아트 및 피부미용실" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설"]:
                warnings.append(
                    f"[미용업 합법화 대안 - 공중위생관리법 제3조] 주용도가 제1종 또는 제2종 근린생활시설이어야 영업 신고가 가능합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 관할 관청에 **표시변경**을 통해 주용도를 **'제1종 또는 제2종 근린생활시설'**로 변경 후 입점하세요."
                )
            else:
                legal_actions.append("💄 **[미용업 적합]** 공중위생관리법에 따른 시설 및 설비(소독장비, 분리된 조제실 등)를 갖추고 면허증을 보유하면 즉시 영업 신고가 가능합니다.")

        elif "목욕장업" in target_biz:
            if bld_use != "제2종근린생활시설":
                warnings.append(
                    f"[목욕장업 합법화 대안 - 공중위생관리법 제3조] 대중목욕탕 및 사우나는 주용도가 '제2종근린생활시설'이어야 합니다. (현재 주용도: {bld_use})\n"
                    f"💡 **[합법화 대안]** 관할 관청에 **표시변경**을 신청하여 주용도를 **'제2종근린생활시설'**로 변경해야 합니다."
                )
            else:
                legal_actions.append("♨️ **[목욕장업 적합]** 공중위생관리법에 따른 수질검사 성적서, 목욕장 욕조수/원수 기준 만족 여부 및 대규모 오수 발생에 따른 정화조 용량/하수도 원인자부담금 내역을 철저히 검증하세요.")

        elif "공인중개사사무소" in target_biz or "일반 법무사·행정사·세무사 사무소" in target_biz or "일반 기업체 오피스" in target_biz:
            if bld_use not in ["제2종근린생활시설", "업무시설", "제1종근린생활시설"]:
                warnings.append(
                    f"[사무소 합법화 대안 - 건축법 시행령 별표1] 주용도가 근린생활시설 또는 업무시설이어야 사업자등록 및 개설등록이 가능합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제1·2종 근린생활시설'** 또는 **'업무시설'**로 변경 후 입점하세요."
                )
            else:
                legal_actions.append("💼 **[사무소/오피스 입점 적합]** 건축법상 일반 업무 및 공인중개사법상 사무소 확보 요건에 완벽히 부합합니다.")

        elif "금융업소" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "업무시설"]:
                warnings.append(
                    f"[금융업소 합법화 대안 - 건축법 시행령] 은행 등 금융업소는 바닥면적 500㎡ 미만일 경우 제2종근생(또는 1종근생 일부), 이상일 경우 업무시설이어야 합니다. (현재: {bld_use})\n"
                    f"💡 **[합법화 대안]** 면적 규모에 맞추어 **표시변경** 또는 **용도변경** 절차를 진행하세요."
                )
            else:
                legal_actions.append("🏦 **[금융업소 적합]** 건축물대장상 입점에 적합합니다. ATM 등 중량 장비 설치에 대비한 바닥 하중 및 보안 네트워크 인입 가능 여부를 확인하세요.")

        else:
            legal_actions.append(f"✅ **[{target_biz} 적합성 검토 완료]** 입력된 건축물 주용도({bld_use}) 및 면적({area}㎡) 기준 일반적인 건축법·국토계획법 요건에 부합합니다. 단, 양산시 조례 및 개별 지침을 최종 확인하세요.")

    else: # 산업단지 내 공장
        if bld_use != "공장" and bld_use != "나대지(건축물없음)":
            fatal_errors.append(
                f"치명적 결격: 산업집적활성화 및 공장설립에 관한 법률(산집법) 제16조에 따라 산단 내 공장 등록을 위해서는 주용도가 무조건 **'공장'**이어야 합니다. (현재 주용도: {bld_use}) "
                f"💡 **해결 대안:** 다른 공장 물건을 선택해야 합니다."
            )
        
        if selected_parcel_row is not None:
            input_val = target_biz.strip().upper()
            code_match = input_val in auto_detected_code.upper() or any(c.strip() in input_val for c in auto_detected_code.split(','))
            name_match = input_val in auto_detected_name.upper() or any(w in auto_detected_name for w in target_biz.split())
            
            if target_biz and not code_match and not name_match:
                fatal_errors.append(
                    f"산단 관리기본계획 위반: 해당 지번의 한국산업단지공단(KICOX) 관리기본계획상 허용 업종코드/명칭(`{auto_detected_code} {auto_detected_name}`)에 임차인 희망 업종('{target_biz}')이 포함되지 않습니다. "
                    f"💡 **해결 대안:** 산집법 제38조에 따라 해당 지번에서는 입주계약 체결이 불가능합니다."
                )
            else:
                legal_actions.append("✅ **산단 입주계약 적합:** 한국산업단지공단 관리기본계획상 허용 업종 코드 및 명칭에 부합합니다.")

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 1. 상세 법적 리포트", "💰 2. 원인자부담금", "⚡ 3. 전기용량(승압)", "🧯 4. 소방·환경·위생", "🚽 5. 정화조·오수"
    ])

    # 리포트 다운로드용 텍스트 저장용 리스트
    report_text_lines = []
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    report_text_lines.append("==========================================================================")
    report_text_lines.append(f"  🛡 양산시 부동산 법률 규제 검토 및 위험 진단 보고서 (발행일: {today_str})")
    report_text_lines.append("==========================================================================")
    report_text_lines.append(f"📍 대상 지번: {input_jibun if input_jibun else '미입력'}")
    report_text_lines.append(f"🏢 선택 용도지역: {zoning} | 건축물 주용도: {bld_use} | 기타용도: {current_etc}")
    report_text_lines.append(f"📐 건폐율: {current_bcv} | 용적률: {current_far}")
    report_text_lines.append(f"🏗️ 지구단위계획 구역: {current_dp}")
    report_text_lines.append(f"🎯 임차 희망 업종: {target_biz} (면적: {area}㎡ / 층수: {floor_num}층)")
    report_text_lines.append("--------------------------------------------------------------------------\n")

    with tab1:
        st.subheader("📋 공법상 적합성 및 상세 법적 리포트")
        st.markdown("---")
        
        if fatal_errors:
            st.error("### ❌ [계약 절대 금지 / 중개사고 고위험 사유]")
            report_text_lines.append("[❌ 계약 절대 금지 사유]")
            for err in fatal_errors: 
                st.markdown(f"- **{err}**")
                report_text_lines.append(f"- {err}")
            st.markdown("---")
        else:
            st.success("### ✅ [공법상 입주 및 영업 기본 요건 적합]")
            report_text_lines.append("[✅ 기본 공법 요건: 적합]")
            st.markdown("---")
            
        if warnings:
            st.warning("### ⚠ [주의 및 필수 검토 / 용도변경·표시변경 합법화 대안 가이드]")
            report_text_lines.append("\n[⚠ 주의 및 용도변경 대안 가이드]")
            for w in warnings: 
                st.markdown(f"- {w}")
                report_text_lines.append(f"- {w}")
            st.markdown("---")
            
        if legal_actions:
            st.markdown("### 🛠 [실무 법적 조치 및 상세 가이드]")
            report_text_lines.append("\n[🛠️ 실무 법적 조치 가이드]")
            for act in legal_actions: 
                st.markdown(f"- {act}")
                report_text_lines.append(f"- {act}")

        # 다운로드 기능
        report_full_text = "\n".join(report_text_lines)
        st.download_button(
            label="📥 법적 검토 진단 리포트 파일 다운로드 (.txt)",
            data=report_full_text,
            file_name=f"양산시_부동산법률진단리포트_{input_jibun}_{today_str}.txt",
            mime="text/plain"
        )

    with tab2:
        st.subheader("💰 상하수도 원인자부담금 시뮬레이션 (하수도법 제61조)")
        unit_discharge_rates = {
            "동물위탁관리업": 0.08,
            "식육포장처리업": 0.20,
            "세차장": 0.35,
            "목욕장업": 0.30,
            "일반음식점": 0.18,
            "피트니스·헬스장": 0.12,
            "유흥주점": 0.25,
            "무도장 및 카지노업소": 0.25,
            "청소년게임제공업": 0.05,
            "생활숙박시설": 0.20,
            "펜션 및 휴양콘도미니엄": 0.20,
            "세탁소": 0.15,
        }
        rate = unit_discharge_rates.get(target_biz, 0.05)
        estimated_discharge = area * rate
        est_water_fee = estimated_discharge * 1823000
        est_sewage_fee = (estimated_discharge * 1910000) if estimated_discharge >= 10 else 0

        st.markdown(f"- 추정 일일 오수량: **{estimated_discharge:.1f} 톤(㎥/일)** (면적 {area}㎡ 기준, 환경부 고시 오수발생량 적용)")
        st.markdown(f"- **상수도원인자부담금:** 약 **{est_water_fee:,.0f} 원** *(양산시 수도 급수 조례 기준)*")
        if estimated_discharge >= 10:
            st.markdown(f"- **하수도원인자부담금:** 약 **{est_sewage_fee:,.0f} 원** *(하수도법 제61조: 일일 10톤 이상 발생 시 전량 부과 대상)*")
        else:
            st.markdown("- **하수도원인자부담금:** ✅ **면제 대상** *(하수도법상 10톤 미만)*")
        st.info("💡 양산시 하수도 사용 조례 및 상수도 원인자부담금 산정 조례 기준에 따라 정확한 부과액은 상하수도사업소 최종 확인이 필요합니다.")

    with tab3:
        st.subheader("⚡ 현실적인 계약전력 및 승압 진단 (전기사업법 및 한전 약관)")
        
        if "피트니스" in target_biz or "헬스장" in target_biz or "제조업" in target_biz or "공장" in target_biz or "식품제조" in target_biz or "식육포장" in target_biz or "무도장" in target_biz:
            base_kw = 15.0
            kw_per_sqm = 0.08 
            max_cap = 60.0
        elif "음식점" in target_biz or "카페" in target_biz or "제과점" in target_biz or "유흥주점" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz or "세탁소" in target_biz:
            base_kw = 15.0
            kw_per_sqm = 0.06
            max_cap = 50.0
        elif "청소년게임제공업" in target_biz:
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

        st.markdown(f"- **현재 호실 계약전력:** `{current_power} kW`")
        st.markdown(f"- **업종별 현실적 권장 소요전력:** 약 `{req_power:.1f} kW` (한전 기본공급약관 상가 부하 산정 기준)")

        if power_diff > 0:
            st.warning(f"⚠ **[승압 필요]** 현재 전력보다 약 `{power_diff:.1f} kW`의 추가 전력이 필요합니다.")
            st.markdown(f"- **예상 한전 표준시설부담금(참고용):** 약 **{est_electric_fee:,.0f} 원** *(한전 불입금 및 전기공사업체 시공비 별도)*")
        else:
            st.success("✅ **[전기 용량 충분]** 현재 계약전력으로 정상적인 영업 가동이 가능합니다.")

    with tab4:
        st.subheader("🧯 소방, 환경 및 위생 규제 요건 상세 심사")
        if "유흥주점" in target_biz or "단란주점" in target_biz or "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz or "무도장" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz:
            st.markdown("- **다중이용업소의 안전관리에 관한 특별법 제9조:** 소방시설완비증명서, 방염필증, 비상구 확보, 객실별 완강기 및 화재경보기 설치 의무 대상.")
        elif "병원" in target_biz or "치과의원" in target_biz or "한의원" in target_biz or "동물병원" in target_biz:
            st.markdown("- **폐기물관리법 제13조:** 감염성·의료폐기물 전용 보관함 및 전문 처리업체 위탁 계약 필수.")
        elif "세차장" in target_biz or "세탁소" in target_biz:
            st.markdown("- **물환경보전법 & 대기환경보전법:** 폐수배출시설 신고 및 세탁기기 용량별 대기 배출시설 신고 대상 여부 사전 확인 필수.")
        else:
            st.markdown("- 일반 건축물 소방시설법에 따른 피난구 유도등 및 소화기 설치 대상.")

    with tab5:
        st.subheader("🚽 건물 정화조 용량 검토 및 오수 발생량 (하수도법 제34조)")
        est_dis = area * rate
        st.markdown(f"- 추정 일일 오수량: `{est_dis:.1f} 톤/일`")
        if est_dis >= 5.0 or "음식점" in target_biz or "목욕장" in target_biz or "무도장" in target_biz or "숙박" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz or "세탁소" in target_biz:
            st.warning("⚠ **[정화조 용량 초과 주의]** 오수 발생량이 크거나 수질오염 유발 업종이므로, 건축물 전체 정화조 용량 및 청소 주기 초과 여부를 건물 관리사무소에 반드시 확인하세요.")
        else:
            st.success("✅ 정화조 오수 부담 안정적 (하수도법상 단독 정화조 용량 범위 내)")
