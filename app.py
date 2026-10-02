import os
import re
import pandas as pd
import streamlit as st

# --- 1. 페이지 및 레이아웃 설정 ---
st.set_page_config(
    page_title="양산시 통합 부동산/건축물/용도지역 조회 시스템",
    page_icon="🏢",
    layout="wide"
)

# --- 2. 데이터 전처리 헬퍼 함수 ---
def clean_num_str(val):
    """Pandas가 숫자를 float(410.0)으로 읽었을 때 소수점(.0)을 제거하고 순수 문자열로 정제합니다."""
    if pd.isna(val):
        return ""
    return str(val).split('.')[0].strip()

# --- 3. CSV 데이터 자동 검색 및 통합 로딩 ---
@st.cache_data(show_spinner="양산시 전체 CSV 및 산단 데이터를 연동하는 중입니다...")
def load_all_local_csvs():
    """
    현재 작업 디렉토리 내의 모든 .csv 파일을 찾아 자동으로 통합합니다.
    """
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        return None, []

    loaded_dfs = []
    file_list = []

    for file in csv_files:
        # 다양한 한국어 인코딩 시도
        for enc in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
            try:
                df = pd.read_csv(file, encoding=enc, low_memory=False)
                df.columns = df.columns.str.strip() # 컬럼명 공백 제거
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
            return None, []
            
    return None, []

# --- 4. 지번 주소 분석 함수 ---
def parse_lot_address(address_str):
    """
    입력된 주소에서 읍/면/동/리와 본번-부번을 추출합니다.
    예: '물금읍 범어리 410-1' -> ('범어리', '410', '1')
    """
    address_str = address_str.strip()
    
    # 읍/면/동/리 추출
    dong_match = re.search(r'([가-힣]+(?:동|리|읍|면))', address_str)
    dong_name = dong_match.group(1) if dong_match else ""
    
    # 지번 (번-지) 추출
    num_match = re.search(r'(\d+)(?:-(\d+))?', address_str)
    main_no = num_match.group(1) if num_match else ""
    sub_no = num_match.group(2) if (num_match and num_match.group(2)) else "0"
    
    return dong_name, main_no, sub_no

# --- 5. CSV 데이터 기반 통합 검색 엔진 ---
def search_in_csv_data(df, raw_address):
    if df is None or df.empty or not raw_address.strip():
        return pd.DataFrame(), None, None, None

    dong_name, main_no, sub_no = parse_lot_address(raw_address)
    bun_str = clean_num_str(main_no)
    ji_str = clean_num_str(sub_no)
    
    cols = df.columns.tolist()
    
    # 컬럼 자동 감지
    addr_col = next((c for c in cols if any(k in c.lower() for k in ['대지위치', '소재지', '주소', '지번주소', '위치'])), None)
    purp_col = next((c for c in cols if any(k in c.lower() for k in ['주용도코드명', '주용도명', '주용도', '건축물용도', '용도'])), None)
    zoning_col = next((c for c in cols if any(k in c.lower() for k in ['용도지역코드명', '용도지역명', '용도지역', '지역구분', '지목', '구분'])), None)
    
    bun_col = next((c for c in cols if c in ['번', '지번', '본번']), None)
    ji_col = next((c for c in cols if c in ['지', '부번']), None)

    matched_rows = pd.DataFrame()

    # [1차 검색] 번, 지, 동/리 조건 정밀 검색
    if bun_col and bun_str:
        df_bun = df[bun_col].apply(clean_num_str)
        cond_bun = (df_bun == bun_str) | (df_bun == bun_str.zfill(4))
        
        if ji_col and ji_str != "0":
            df_ji = df[ji_col].apply(clean_num_str)
            cond_ji = (df_ji == ji_str) | (df_ji == ji_str.zfill(4))
            cond = cond_bun & cond_ji
        else:
            cond = cond_bun

        if addr_col and dong_name:
            cond = cond & df[addr_col].astype(str).str.contains(dong_name, na=False)

        matched_rows = df[cond]

    # [2차 검색] 전체 주소 텍스트 매칭
    if matched_rows.empty and addr_col:
        target_bun = f"{bun_str}-{ji_str}" if ji_str and ji_str != "0" else bun_str
        cond_text = df[addr_col].astype(str).str.contains(target_bun, na=False) if target_bun else pd.Series(True, index=df.index)
        
        if dong_name:
            cond_text = cond_text & df[addr_col].astype(str).str.contains(dong_name, na=False)
            
        matched_rows = df[cond_text]

    return matched_rows, purp_col, zoning_col, addr_col


# --- 6. UI 구성 ---
st.title("🏢 양산시 로컬 통합 데이터 매물/지번 조회")
st.caption("외부 API 없이 폴더 내 모든 양산시 지역 CSV 및 산단 데이터를 자동 연동하여 조회합니다.")

# 데이터 자동 로드
df_combined, loaded_files = load_all_local_csvs()

# 사이드바 데이터 상태 표시
with st.sidebar:
    st.header("📂 데이터 연동 현황")
    if loaded_files:
        st.success(f"총 {len(loaded_files)}개 CSV 파일 연동 완료")
        with st.expander("연동된 파일 목록 보기"):
            for f in loaded_files:
                st.write(f"- `{f}`")
    else:
        st.error("현재 폴더에 CSV 파일이 없습니다. CSV 파일을 넣어주세요.")

# 메인 검색 창
search_input = st.text_input(
    "지번 주소를 입력하세요",
    placeholder="예: 물금읍 범어리 410 또는 중부동 410-1",
    key="search_query"
)

if search_input:
    results, purp_col, zoning_col, addr_col = search_in_csv_data(df_combined, search_input)

    if not results.empty:
        st.subheader("🔎 조회 결과 요약")
        
        # 핵심 데이터 추출
        purp_val = results[purp_col].dropna().iloc[0] if purp_col and not results[purp_col].dropna().empty else "정보 없음"
        zoning_val = results[zoning_col].dropna().iloc[0] if zoning_col and not results[zoning_col].dropna().empty else "정보 없음"
        addr_val = results[addr_col].dropna().iloc[0] if addr_col and not results[addr_col].dropna().empty else search_input

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("소재지", str(addr_val))
        with col2:
            st.metric("건축물 주용도", str(purp_val))
        with col3:
            st.metric("용도지역/구분", str(zoning_val))

        st.divider()
        st.subheader("📋 상세 검색 데이터")
        st.dataframe(results, use_container_width=True)
    else:
        st.warning(f"'{search_input}'에 해당하는 데이터를 연동된 CSV 파일에서 찾지 못했습니다.")
        st.info("💡 **확인 사항:** 입력한 동/리와 지번이 정확한지, 관련 CSV 파일이 폴더 안에 존재하는지 확인해 주세요.")
# -----------------------------------------------------------------------------
# 💾 [양산시 전체 건축물대장 CSV 자동 스캔 & SQLite DB 통합 검색 로직]
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_all_yangsan_csv():
    """
    깃허브 루트 폴더에 존재하는 양산시 읍/면/동별 건축물대장 CSV 파일들을
    자동으로 탐색하고 하나로 통합하여 메모리에 캐싱합니다.
    """
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and ('건축물대장' in f or '48330' in f or f.startswith('01_'))]
    if not csv_files:
        return None
    
    dfs = []
    for file in csv_files:
        # 다양한 한글 인코딩(cp949, euc-kr, utf-8) 자동 시도
        for enc in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
            try:
                df = pd.read_csv(file, encoding=enc, low_memory=False)
                df.columns = df.columns.str.strip()
                dfs.append(df)
                break
            except Exception:
                continue

    if dfs:
        try:
            full_df = pd.concat(dfs, ignore_index=True)
            return full_df
        except Exception:
            return None
    return None

def search_local_sqlite_or_csv(sigungu_cd, bjdong_cd, main_no, sub_no, raw_address=""):
    """
    공공데이터 API 조회 실패 또는 미응답 시 
    깃허브 내 양산시 CSV 파일 통합 데이터 및 SQLite DB에서 지번으로 정밀 검색합니다.
    """
    found_purp = None
    found_zoning = None

    # 번/지 숫자 정제 (예: "0410" -> "410", "0000" -> "0")
    bun_int = str(int(main_no)) if main_no.isdigit() else main_no
    ji_int = str(int(sub_no)) if sub_no.isdigit() else sub_no
    bun_z = main_no.zfill(4)
    ji_z = sub_no.zfill(4)

    # 1차: 양산 전체 CSV 통합 데이터프레임 검색
    df_all = load_all_yangsan_csv()
    if df_all is not None:
        cols = df_all.columns.tolist()
        
        # 컬럼 매칭
        purp_col = next((c for c in cols if any(k in c.lower() for k in ['주용도코드명', '주용도', 'mainpurpscdnm', '용도명', '건축물용도'])), None)
        zoning_col = next((c for c in cols if any(k in c.lower() for k in ['용도지역코드명', '용도지역', '지역구분', 'prposarea', '지목', '지역지구명'])), None)
        addr_col = next((c for c in cols if any(k in c.lower() for k in ['대지위치', '소재지', '주소', '지번주소'])), None)

        matched_rows = pd.DataFrame()

        # 조건 A: 대지위치 텍스트 검색 (지번 숫자 결합)
        if addr_col and raw_address:
            # 주소에서 핵심 지번 숫자 추출 (예: "중부동 410-1" -> "410")
            num_parts = re.findall(r'\d+', raw_address)
            if num_parts:
                target_num = num_parts[0]
                matched_rows = df_all[df_all[addr_col].astype(str).str.contains(target_num, na=False)]

        # 조건 B: 시군구코드/법정동코드/번/지 검색
        if matched_rows.empty and '시군구코드' in cols and '법정동코드' in cols:
            cond = (df_all['시군구코드'].astype(str) == sigungu_cd) & (df_all['법정동코드'].astype(str) == bjdong_cd)
            if '번' in cols and '지' in cols:
                cond = cond & (df_all['번'].astype(str).isin([bun_int, bun_z])) & (df_all['지'].astype(str).isin([ji_int, ji_z]))
            matched_rows = df_all[cond]

        # 조건 C: PNU 매칭
        if matched_rows.empty and ('PNU' in cols or 'pnu' in cols):
            p_col = 'PNU' if 'PNU' in cols else 'pnu'
            pnu_target = f"{sigungu_cd}{bjdong_cd}"
            matched_rows = df_all[df_all[p_col].astype(str).str.startswith(pnu_target, na=False)]

        if not matched_rows.empty:
            row = matched_rows.iloc[0]
            if purp_col and pd.notna(row.get(purp_col)):
                found_purp = str(row[purp_col]).strip()
            if zoning_col and pd.notna(row.get(zoning_col)):
                found_zoning = str(row[zoning_col]).strip()

            if found_purp or found_zoning:
                return found_purp, found_zoning

    # 2차: building_data.db SQLite 검색 (기존 로직 유지)
    if os.path.exists(LOCAL_DB_PATH):
        try:
            conn = sqlite3.connect(LOCAL_DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='building_info'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(building_info)")
                cols = [col[1] for col in cursor.fetchall()]

                purp_col = next((c for c in cols if any(k in c.lower() for k in ['주용도', 'mainpurpscdnm', '용도명', '건축물용도'])), None)
                zoning_col = next((c for c in cols if any(k in c.lower() for k in ['용도지역', '지역구분', 'prposarea', '지목'])), None)

                conditions = []
                params = []

                if '시군구코드' in cols and '법정동코드' in cols:
                    conditions.append("시군구코드 = ? AND 법정동코드 = ?")
                    params.extend([sigungu_cd, bjdong_cd])
                    if '번' in cols and '지' in cols:
                        conditions.append("(번 IN (?, ?) AND 지 IN (?, ?))")
                        params.extend([bun_int, bun_z, ji_int, ji_z])
                elif 'PNU' in cols or 'pnu' in cols:
                    p_col = 'PNU' if 'PNU' in cols else 'pnu'
                    conditions.append(f"{p_col} LIKE ?")
                    params.append(f"{sigungu_cd}{bjdong_cd}%{bun_z}{ji_z}")

                if conditions:
                    where_clause = " WHERE " + " AND ".join(conditions)
                    cursor.execute(f"SELECT * FROM building_info {where_clause} LIMIT 1", params)
                    row = cursor.fetchone()
                    if row:
                        row_dict = dict(zip(cols, row))
                        if purp_col and row_dict.get(purp_col):
                            found_purp = str(row_dict[purp_col]).strip()
                        if zoning_col and row_dict.get(zoning_col):
                            found_zoning = str(row_dict[zoning_col]).strip()
            conn.close()
        except Exception:
            pass

    return found_purp, found_zoning


# 건축물대장 주용도 데이터베이스 (직관적인 표준 대분류 체계 유지)
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
    "단독/다세대/아파트(주택류)"
]

# 용도지역 목록
zoning_options = [
    "제1종전용주거지역", "제2종전용주거지역", "제1종일반주거지역", "제2종일반주거지역", "제3종일반주거지역",
    "준주거지역", "중심상업지역", "일반상업지역", "근린상업지역",
    "전용공업지역", "일반공업지역", "준공업지역",
    "보전녹지지역", "자연녹지지역", "계획관리지역"
]

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

# 양산시 도시계획 조례 및 건축 조례 기반 용도지역별 세부 업종 교차 진단 데이터베이스
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
st.subheader("📝 2. 대상 부동산 기본 팩트 및 지번 입력")

property_type = st.radio("중개 대상물 형태 선택", ["상가 / 일반 건축물", "산업단지 내 공장 (지번 조회)"], key="main_property_type_radio")

# 지번 및 층수 입력 필드
col_addr1, col_addr2 = st.columns([2, 1])
with col_addr1:
    input_jibun = st.text_input("📍 대상 건물 지번 입력 (예: 경상남도 양산시 중부동 410 또는 물금읍 범어리)", placeholder="전체 주소 또는 지번을 입력하세요", key="main_input_jibun")
with col_addr2:
    floor_num = st.number_input("건물 층수 (지하층 음수)", min_value=-5, max_value=50, value=1, key="main_floor_num")

# 세션 상태 초기화
if 'detected_zoning' not in st.session_state:
    st.session_state.detected_zoning = "제2종일반주거지역"

# -----------------------------------------------------------------------------
# 🎯 [카카오맵 API + 공공데이터 API + 깃허브 양산 CSV 로컬 DB 정밀 연동 로직]
# -----------------------------------------------------------------------------
if st.button("🔍 지번 정제 및 실제 용도지역/건축물대장 조회 (API & 양산 CSV 연동)", key="api_lookup_btn"):
    if not input_jibun:
        st.warning("⚠ 조회할 지번을 입력해주세요.")
    else:
        with st.spinner("카카오맵 API 주소 정제 및 양산시 건축물대장 CSV/API 데이터베이스 통합 조회 중..."):
            try:
                # Step 1: 카카오맵 API를 통해 정확한 지번, 법정동코드, PNU 추출
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

                    # 카카오맵 응답에서 PNU 고유 코드 구성요소 추출
                    address_info = doc.get('address', {})
                    b_code = address_info.get('b_code', '')              # 10자리 법정동코드
                    mountain_yn = address_info.get('mountain_yn', 'N')   # 산 여부
                    san_code = '2' if mountain_yn == 'Y' else '1'
                    main_no = address_info.get('main_address_no', '0').zfill(4)
                    sub_no = address_info.get('sub_address_no', '0').zfill(4)
                    
                    pnu = f"{b_code}{san_code}{main_no}{sub_no}"          # 19자리 PNU
                    
                    sigungu_cd = b_code[:5]
                    bjdong_cd = b_code[5:]
                    plat_gb_cd = '1' if mountain_yn == 'Y' else '0'

                    # Step 2: 공공데이터포털 건축물대장 API (표제부) 실제 주용도 조회
                    bld_api_url = "http://apis.data.go.kr/1613000/BldRnService_v2/getBrTitleInfo"
                    bld_params = {
                        'serviceKey': requests.utils.unquote(BUILDING_API_KEY),
                        'sigunguCd': sigungu_cd,
                        'bjdongCd': bjdong_cd,
                        'platGbCd': plat_gb_cd,
                        'bun': main_no,
                        'ji': sub_no,
                        'numOfRows': '5',
                        'pageNo': '1'
                    }
                    
                    real_main_purp = ""
                    try:
                        bld_res = requests.get(bld_api_url, params=bld_params, timeout=5)
                        if bld_res.status_code == 200:
                            root = ET.fromstring(bld_res.content)
                            items = root.findall('.//item')
                            if items:
                                main_purp_elem = items[0].find('mainPurpsCdNm')
                                if main_purp_elem is not None and main_purp_elem.text:
                                    real_main_purp = main_purp_elem.text.strip()
                    except Exception:
                        pass

                    # Step 3: 공공데이터포털 토지이용계획 API 실제 용도지역 조회
                    land_api_url = "http://apis.data.go.kr/1611000/nsdi/LandUseService/attr/getLandUseAttr"
                    land_params = {
                        'serviceKey': requests.utils.unquote(LAND_API_KEY),
                        'pnu': pnu,
                        'format': 'json',
                        'numOfRows': '10',
                        'pageNo': '1'
                    }
                    
                    real_zoning = ""
                    try:
                        land_res = requests.get(land_api_url, params=land_params, timeout=5)
                        if land_res.status_code == 200:
                            land_json = land_res.json()
                            field_list = land_json.get('landUses', {}).get('field', [])
                            for field in field_list:
                                prpos_area_nm = field.get('prposAreaDstrcCodeNm', '')
                                for z_opt in zoning_options:
                                    if z_opt in prpos_area_nm:
                                        real_zoning = z_opt
                                        break
                                if real_zoning:
                                    break
                    except Exception:
                        pass

                    # Step 4: [양산 CSV & 로컬 DB 교차 연동] API 조회 미응답/미등록 시 깃허브 양산 CSV 파일에서 정밀 검색
                    local_purp, local_zoning = search_local_sqlite_or_csv(sigungu_cd, bjdong_cd, main_no, sub_no, exact_address)

                    if not real_main_purp and local_purp:
                        real_main_purp = local_purp
                        st.info(f"💾 **[양산지역 CSV 연동 데이터]** 양산 건축물대장 CSV 파일에서 주용도를 불러왔습니다: `{local_purp}`")

                    if not real_zoning and local_zoning:
                        for z_opt in zoning_options:
                            if z_opt in local_zoning:
                                real_zoning = z_opt
                                break
                        if real_zoning:
                            st.info(f"💾 **[양산지역 CSV 연동 데이터]** 양산 건축물대장 CSV 파일에서 용도지역을 불러왔습니다: `{real_zoning}`")

                    # Step 5: 결과 자동 매칭 및 드롭다운 동기화
                    if real_zoning:
                        st.session_state["main_zoning_select"] = real_zoning
                        st.success(f"✅ **[용도지역 자동 매칭 완료]** 용도지역: `{real_zoning}`")
                    else:
                        st.info("💡 공공데이터 API 및 CSV 미등록 지역이므로 용도지역 목록에서 직접 선택해주세요.")

                    if real_main_purp:
                        matched_bld = None
                        for b_use in general_building_uses:
                            if b_use in real_main_purp or real_main_purp in b_use:
                                matched_bld = b_use
                                break
                        if matched_bld:
                            st.session_state["main_bld_use_select"] = matched_bld
                            st.success(f"✅ **[건축물대장 주용도 자동 매칭 완료]** 주용도: `{matched_bld}` ({real_main_purp})")
                        else:
                            st.info(f"📋 **[실제 건축물대장 주용도]**: `{real_main_purp}` (아래 목록에서 가장 가까운 항목 선택)")
                    else:
                        st.info("💡 공공데이터 API 및 CSV 미등록 필지이므로 주용도를 수동 선택해주세요.")

                else:
                    st.error("⚠️ 카카오맵 API에서 지번을 찾을 수 없습니다. 정확한 지번(예: 양산시 중부동 410)을 입력하세요.")
            except Exception as e:
                st.error(f"API 연동 및 데이터 조회 중 오류가 발생했습니다: {e}")

# 선택 박스: 용도지역과 건축물대장 주용도를 각각 독립적으로 선택 가능하도록 배치
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
        "건축물대장 주용도 (실제 대장 기재 내용과 일치하도록 직접 선택)", 
        general_building_uses, 
        key="main_bld_use_select"
    )

# 건축물대장 기타용도(부수용도) 표시 박스
st.info(f"📋 **[안내]:** 용도지역(`{zoning}`)과 건축물대장 주용도(`{bld_use}`)를 개별적으로 완벽하게 설정한 상태에서 아래 희망 업종과의 적합성을 정밀 교차 진단합니다.")

col_f1, col_f2 = st.columns(2)
with col_f1:
    area = st.number_input("바닥면적 / 전용면적 (㎡)", min_value=0.0, value=100.0, help="해당 업종이 실제로 사용할 면적", key="main_area_input")
with col_f2:
    has_school_zone = st.checkbox("🎓 학교환경위생정화구역 저촉 여부", value=False, key="main_school_zone_check")

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
            parcel_options = f_df[jibun_col].fillna('').astype(str).tolist()
            sel_addr = st.selectbox("조회된 필지(지번) 선택", parcel_options, key="ind_parcel_selectbox_field")
            selected_parcel_row = f_df[f_df[jibun_col].fillna('').astype(str) == sel_addr].iloc[0]
            
            code_col = '허용 업종코드' if '허용 업종코드' in df_parcels.columns else (df_parcels.columns[2] if len(df_parcels.columns) > 2 else '')
            name_col = '업종 명칭' if '업종 명칭' in df_parcels.columns else (df_parcels.columns[3] if len(df_parcels.columns) > 3 else '')
            
            auto_detected_code = str(selected_parcel_row.get(code_col, ''))
            auto_detected_name = str(selected_parcel_row.get(name_col, ''))
            st.success(f"🎯 **[지번 매칭 완료]** `{sel_addr}` (허용 업종코드: {auto_detected_code})")
        else:
            st.warning("⚠ 일치하는 지번 또는 도로명이 없습니다. 검색어를 다시 확인해주세요.")
    else:
        st.warning("⚠️ 산단 데이터 파일이 로드되지 않았습니다.")

st.markdown("---")
st.subheader("🎯 3. 임차인 세부 희망 업종 및 조건 선택")

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

biz_category = st.selectbox("희망 업종 대분류", list(comprehensive_biz_dict.keys()), key="main_biz_category_select")
target_biz = st.selectbox("세부 희망 업종 선택", comprehensive_biz_dict[biz_category], key="main_target_biz_select")
current_power = st.number_input("현재 건물(호실) 계약전력 (kW)", min_value=1.0, value=10.0, step=1.0, key="main_current_power_input")

submitted = st.button("🚀 종합 법적 진단 리포트 생성", type="primary", key="main_submit_btn")

if submitted:
    st.markdown("---")
    
    fatal_errors = []
    warnings = []
    legal_actions = []

    # 1. 용도지역 제한 검증 (국토계획법)
    if property_type == "상가 / 일반 건축물" and zoning in zoning_restrictions:
        prohibited_list = zoning_restrictions[zoning]["prohibited"]
        for p in prohibited_list:
            if p in target_biz or p in biz_category or (p == "위락시설" and target_biz in ["무도장 및 카지노업소", "유흥주점", "단란주점"]):
                fatal_errors.append(
                    f"[국토계획법 제76조 및 동법 시행령 별표] '{zoning}' 지역에서는 국토의 계획 및 이용에 관한 법률에 따라 "
                    f"'{target_biz}'의 입점 및 영업이 법적으로 원천 금지되어 있습니다. "
                    f"💡 **해결 대안:** 해당 용도지역 내에서는 허용되지 않으므로, 상업지역 등 해당 업종이 허용되는 다른 입지로 물건을 변경해야 합니다."
                )

    # 2. 양산시 도시계획 조례 교차 진단
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_ordinance_rules:
        yangsan_rule = yangsan_ordinance_rules[zoning]
        
        matched_ban = False
        for add_p in yangsan_rule["additional_prohibited"]:
            if add_p in target_biz or add_p in biz_category or any(kw in target_biz for kw in add_p.split()):
                matched_ban = True
                fatal_errors.append(
                    f"[양산시 도시계획 조례 규제 위반 / 계약 절대금지] 국토계획법상 가능하더라도, **양산시 도시계획 조례**에 따라 "
                    f"'{zoning}' 지역에서는 임차인께서 선택하신 **'{target_biz}'**의 입점 및 건축허가가 법적으로 엄격히 금지됩니다. "
                    f"📜 **법적 근거:** {yangsan_rule['legal_basis']} "
                    f"💡 **해결 대안:** 양산시 조례 기준 위반에 해당하므로 본 물건은 계약할 수 없으며, 양산시 조례상 해당 업종이 허용되는 타 용도지역 상가 물건을 검토하세요."
                )
                break
        
        if not matched_ban:
            if zoning == "중심상업지역":
                warnings.append(
                    f"🏛️ **[양산시 도시계획 조례 크로스 체크 안내]** {yangsan_rule['legal_basis']} "
                    f"(💡 중심상업지역이라 '{target_biz}' 업종 자체는 허용되나, 실제 현장 실무 시 **주차장법 대수 기준 및 소방방재 시설 기준** 미달로 인한 허가 반려 사고가 빈번하므로 건축물대장 및 소방 동선을 반드시 실측·확인하세요.)"
                )
            else:
                legal_actions.append(
                    f"🏛 **[양산시 도시계획 조례 교차 검증 통과]** '{zoning}' 지역 내에서 **'{target_biz}'** 입점은 양산시 도시계획 조례상 추가 제한 규정에 저촉되지 않으며 법적 근거가 확보됩니다. "
                    f"(기준 근거: {yangsan_rule['legal_basis']})"
                )

    # 2-1. 양산시 건축 조례상 높이, 일조권 및 주차장 기준 검토
    if property_type == "상가 / 일반 건축물" and zoning in yangsan_building_ordinance_rules:
        bld_rule = yangsan_building_ordinance_rules[zoning]
        legal_actions.append(
            f"📐 **[양산시 건축 조례 동시교차 검증 - 높이 및 일조]** {bld_rule['max_height_rule']}"
        )
        legal_actions.append(
            f"🚗 **[양산시 건축 조례 동시교차 검증 - 주차장 기준]** {bld_rule['parking_rule']}"
        )

    # 3. 학교정화구역 검증 (학교보건법)
    if has_school_zone:
        if any(kw in target_biz for kw in ["유흥주점", "단란주점", "PC방", "노래연습장", "숙박", "당구장", "청소년게임제공업", "인형뽑기방", "무도장", "카지노"]):
            fatal_errors.append(
                f"[학교보건법 제6조 위반] 본 물건지는 학교환경위생정화구역 내에 위치하고 있어 '{target_biz}'의 영업이 원칙적으로 금지됩니다. "
                f"💡 **해결 대안:** 절대정화구역인 경우 영업이 절대 불가능하며, 상대정화구역인 경우 관할 양산교육지원청 학교환경위생정화위원회 심의를 통과해야만 허가 가능합니다."
            )

    # 4. 건축법 주용도 및 면적별 진단 로직
    if property_type == "상가 / 일반 건축물":
        if "세탁소" in target_biz:
            if bld_use != "제1종근린생활시설":
                warnings.append(
                    f"[세탁소 입점 대안 및 용도변경 가이드] "
                    f"현재 건축물대장 주용도가 **'{bld_use}'**이므로 그대로는 세탁소 영업을 할 수 없습니다. "
                    f"💡 **[합법화 대안]** 관할 관청(민원실/건축과)에 **'건축물 표시변경(또는 용도변경)'**을 신청하여 주용도를 **'제1종근린생활시설(세탁소)'**로 변경하시면 합법적으로 입점 및 영업이 가능합니다. (단, 건물 전체의 허용 용도 한도 및 정화조 용량 확인 필수)"
                )
            else:
                legal_actions.append("👕 **[세탁소 적합]** 건축물대장 주용도가 '제1종근린생활시설'로 완벽하게 부합합니다. (드라이클리닝 장비 사용 시 대기배출시설 신고 여부 확인)")

        elif "동물위탁관리업" in target_biz:
            if area >= 300.0 and bld_use != "동물관련시설":
                warnings.append(
                    f"[동물위탁시설(300㎡이상) 합법화 대안] 면적 300㎡ 이상 동물위탁시설은 주용도가 '동물관련시설'이어야 합니다. (현재: {bld_use}, 면적: {area}㎡) "
                    f"💡 **[합법화 대안]** 건축법 제19조에 따라 건축물대장 주용도를 **'동물관련시설'**로 정식 **용도변경 허가**를 받아야 입점할 수 있습니다."
                )
            elif area < 300.0 and bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설"]:
                warnings.append(
                    f"[동물위탁시설(300㎡미만) 합법화 대안] 300㎡ 미만은 제1·2종근린생활시설에서 가능하나 현재 주용도({bld_use})로는 불가합니다. "
                    f"💡 **[합법화 대안]** 건축물 **표시변경(제1종 또는 제2종 근린생활시설)**을 신청하여 대장상 용도를 변경하면 입점할 수 있습니다."
                )
            else:
                legal_actions.append("🐶 **[반려동물 영업 적합 검토]** 주용도 요건에 부합합니다. 독립된 공간(이중문), 방음·방취 공사 시공 여부를 확인하세요.")
        
        elif "동물미용업" in target_biz or "동물생산업·판매업" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설"]:
                warnings.append(
                    f"[동물미용/판매업 합법화 대안] 해당 업종은 제1·2종 근린생활시설 또는 동물관련시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 건축물 **표시변경**을 통해 주용도를 **'제1종근린생활시설'** 또는 **'제2종근린생활시설'**로 변경한 뒤 입점하세요."
                )
            else:
                legal_actions.append("🐾 **[동물미용/판매업 적합]** 동물보호법 시설기준(격리실 등) 준수 필수.")

        elif "일반음식점" in target_biz or "휴게음식점" in target_biz or "제과점" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "판매시설", "숙박시설"]:
                warnings.append(
                    f"[음식·휴게업 합법화 대안] 현재 건축물대장 주용도({bld_use})에서는 음식점 영업이 불가합니다. "
                    f"💡 **[합법화 대안]** 건물 전체의 정화조 용량과 주차 대수가 허용하는 범위 내에서, 관할 관청에 **'건축물 표시변경(제2종근린생활시설 - 일반음식점)'**을 신청하여 대장상 용도를 변경하면 합법 허가를 받을 수 있습니다."
                )
            else:
                legal_actions.append("🍽️ **[음식점 창업 적합]** 식품위생법에 따른 위생교육, 지하층 직통계단 및 그리스 트랩 설치 여부 확인.")

        elif "식육판매업" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설"]:
                warnings.append(
                    f"[식육판매업 합법화 대안] 주용도가 제1종 또는 제2종 근린생활시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제1종 또는 제2종 근린생활시설'**로 변경 후 입점 가능합니다."
                )
            else:
                legal_actions.append("🥩 **[식육판매업 적합]** 냉장·냉동 쇼케이스 구비 필수.")

        elif "유흥주점" in target_biz or "단란주점" in target_biz or "무도장 및 카지노업소" in target_biz:
            if bld_use != "위락시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 제한] 유흥·단란주점 및 무도장·카지노업소는 반드시 주용도가 **'위락시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **[중요한 현실적 대안]** 일반 상가나 근린생활시설 건물은 구조상 '위락시설'로 용도변경이 **사실상 불가능하거나 허용되지 않는 경우가 대부분**입니다. 따라서 처음부터 주용도가 **'위락시설'**로 허가된 건물 물건으로 계약하셔야 합니다."
                )
            else:
                legal_actions.append("🍺 **[위락시설 적합]** 취득세 중과세 및 소방안전시설완비증명서 발급 여부를 확인하세요.")
        
        elif "일반주점·맥주집" in target_biz:
            if bld_use not in ["제2종근린생활시설", "위락시설", "판매시설"]:
                warnings.append(
                    f"[일반주점 합법화 대안] 주용도가 '제2종근린생활시설(일반음식점)' 이상이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 관할 관청에 **표시변경**을 신청하여 주용도를 **'제2종근린생활시설'**로 맞추어야 영업이 가능합니다."
                )
            else:
                legal_actions.append("🍻 **[일반주점 적합]** 식품위생법상 일반음식점 허가 대상.")

        elif "식육포장처리업" in target_biz or "식육가공업" in target_biz or "식품제조·가공업" in target_biz or "금속가공제품 제조업" in target_biz or "인쇄소 및 출판업" in target_biz:
            if bld_use != "공장":
                if bld_use == "제2종근린생활시설" and area < 500.0:
                    warnings.append(
                        f"[제2종근생 제조업 합법화 실무 가이드] 현재 주용도가 '제2종근린생활시설'이고 면적({area}㎡)이 500㎡ 미만이므로 **합법 입점 가능성이 높습니다!** "
                        f"💡 **[건축물대장 세부 표기 추가 방법]** 단, 대장에 단순히 '제2종근생'으로만 되어 있다면 관할 지자체 건축과에 방문하시거나 민원을 통해 대장 괄호 안에 **'제2종근린생활시설 (제조업소)'** 또는 **'(수리점)'**으로 구체적인 세부 용도를 기재하는 **'표시변경'**을 거치면 완벽하게 안전한 합법 상태가 됩니다. (단, 오폐수·대기 배출시설 비대상 확인 필수)"
                    )
                else:
                    warnings.append(
                        f"[제조업소 입점 대안 및 용도변경 가이드] 해당 제조업·가공업은 원칙적으로 '공장' 주용도가 필요합니다. (현재: {bld_use}, 면적: {area}㎡) "
                        f"💡 **[합법화 대안]** 면적 500㎡ 미만 소규모 제조업소·수리점의 경우, 주용도가 **'제2종근린생활시설'**인 상가를 구하여 관할 관청에 **'제2종근린생활시설 (제조업소)'**로 표시변경을 신청하면 공장이 아니어도 합법적으로 들어갈 수 있습니다. 단, 배출시설 설치 승인 대상인 경우 입주가 불가합니다."
                    )
            else:
                legal_actions.append("🏭 **[공장 내 가공 적합]** 산집법 및 환경법상 배출시설 허가 여부를 검토하세요.")

        elif "냉장·냉동창고" in target_biz or "일반 물류창고" in target_biz:
            if bld_use != "창고시설":
                warnings.append(
                    f"[창고시설 합법화 대안] 주용도가 '창고시설'이어야 원활합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 건축물대장 주용도를 **'창고시설'**로 **용도변경 허가**를 받거나, 처음부터 창고시설로 허가된 물건을 계약하는 것을 권장합니다."
                )
            else:
                legal_actions.append("📦 **[창고업 적합]** 1톤 이상 화물차 진출입 도로 및 적재 하중 확인.")

        elif "고물상 및 폐기물재활용시설" in target_biz:
            if bld_use != "자원순환관련시설":
                warnings.append(
                    f"[자원순환시설 대안] 주용도가 '자원순환관련시설'이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 자원순환관련시설로 정식 허가 및 용도변경이 가능한 부지/건물로 이전해야 합니다."
                )
            else:
                legal_actions.append("♻️ **[자원순환시설 적합]** 폐기물관리법에 따른 허가 확인.")

        elif "병원" in target_biz or "요양병원" in target_biz:
            if bld_use != "의료시설":
                warnings.append(
                    f"[병원급 의료시설 합법화 대안] 주용도가 '의료시설'이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 대형 건물의 경우 **'의료시설'**로 용도변경 승인을 받아야 하나, 소방 및 주차 기준이 매우 까다로우므로 전문 건축사와 사전 검토가 필수입니다."
                )
            else:
                legal_actions.append("🏥 **[의료시설 적합]** 소방시설 엄격 기준 충족 필수.")

        elif "치과의원" in target_biz or "한의원" in target_biz:
            if bld_use not in ["제1종근린생활시설", "의료시설"]:
                warnings.append(
                    f"[의원급 합법화 대안] 주용도가 제1종근린생활시설 또는 의료시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 관할 관청에 **표시변경**을 신청하여 주용도를 **'제1종근린생활시설(의원)'**로 변경하면 합법 운영이 가능합니다."
                )
            else:
                legal_actions.append("🩺 **[의원급 적합]** 진료실 및 소독시설 구비.")

        elif "동물병원" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "동물관련시설", "의료시설"]:
                warnings.append(
                    f"[동물병원 합법화 대안] 제1·2종 근린생활시설, 동물관련시설 또는 의료시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 근린생활시설 용도로 변경 후 입점하세요."
                )
            else:
                legal_actions.append("🐾 **[동물병원 적합]** 방사선 방어벽 설치 확인.")

        elif "피트니스·헬스장" in target_biz or "수영장 및 볼링장" in target_biz:
            if area >= 500.0 and bld_use != "운동시설":
                warnings.append(
                    f"[운동시설(500㎡이상) 합법화 대안] 500㎡ 이상 운동시설은 주용도가 '운동시설'이어야 합니다. (현재: {bld_use}, 면적: {area}㎡) "
                    f"💡 **[합법화 대안]** 건축법에 따라 **'운동시설'**로 정식 **용도변경 허가**를 받아야 합니다."
                )
            elif area < 500.0 and bld_use not in ["제2종근린생활시설", "운동시설"]:
                warnings.append(
                    f"[체력단련장(500㎡미만) 합법화 대안] 500㎡ 미만은 제2종근생 또는 운동시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제2종근린생활시설'**로 변경하면 됩니다."
                )
            else:
                legal_actions.append("🏋️ **[운동시설 적합]** 바닥 하중 안전성 검토 및 방진·방음 매트 시공 확인.")

        elif "스크린골프장" in target_biz or "당구장" in target_biz:
            if bld_use not in ["제2종근린생활시설", "운동시설"]:
                warnings.append(
                    f"[스크린골프/당구장 합법화 대안] 제2종근린생활시설 또는 운동시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제2종근린생활시설'**로 변경하세요."
                )
            else:
                legal_actions.append("⛳ **[스크린골프/당구장 적합]** 층고 높이 및 방음 시공 확인.")

        elif "학원" in target_biz or "직업훈련소" in target_biz:
            if area >= 500.0 and bld_use != "교육연구시설":
                warnings.append(
                    f"[학원(500㎡이상) 합법화 대안] 면적 500㎡ 이상 학원은 주용도가 '교육연구시설'이어야 합니다. (현재: {bld_use}, 면적: {area}㎡) "
                    f"💡 **[합법화 대안]** **교육연구시설**로 용도변경 허가를 받아야 합니다."
                )
            elif area < 500.0 and bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                warnings.append(
                    f"[학원(500㎡미만) 합법화 대안] 제2종근린생활시설 또는 교육연구시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제2종근린생활시설'**로 변경하세요."
                )
            else:
                legal_actions.append("📚 **[학원업 적합]** 강의실 면적 및 소방시설 확인.")

        elif "독서실 및 스터디카페" in target_biz:
            if bld_use not in ["제2종근린생활시설", "교육연구시설"]:
                warnings.append(
                    f"[독서실/스카 합법화 대안] 제2종근린생활시설 또는 교육연구시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제2종근린생활시설'**로 변경하세요."
                )
            else:
                legal_actions.append("📖 **[독서실/스카 적합]** 소방안전시설완비증명서 및 소음 방지 설비 확인.")

        elif "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz:
            if bld_use not in ["제2종근린생활시설", "문화및집회시설"]:
                warnings.append(
                    f"[PC방/노래연습장 합법화 대안] 주용도가 제2종근린생활시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 관할 관청에 **표시변경**을 신청하여 주용도를 **'제2종근린생활시설'**로 변경하면 합법 영업이 가능합니다."
                )
            else:
                legal_actions.append("🕹️ **[PC방/게임장 적합]** 학교정화구역 거리 및 다중이용업소 소방필증 확인.")

        elif "세차장" in target_biz:
            if bld_use != "자동차관련시설":
                warnings.append(
                    f"[세차장 합법화 대안] 주용도가 '자동차관련시설'이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** 건축물대장 주용도를 **'자동차관련시설'**로 정식 **용도변경**하고 폐수배출시설 승인을 받아야 합니다."
                )
            else:
                legal_actions.append("🚗 **[세차장 적합]** 오수 정화시설, 유수분리기 설치 여부 및 하수도법상 폐수배출시설 신고 필수.")

        elif "자동차정비공장" in target_biz or "자동차매매장" in target_biz:
            if bld_use != "자동차관련시설":
                warnings.append(
                    f"[카센터 / 수리점 합법화 및 표시변경 가이드] "
                    f"현재 건축물대장 주용도가 **'{bld_use}'**로 되어 있으나, "
                    f"💡 **[핵심 실무 꿀팁 및 대안]** 만약 현재 건물의 주용도가 **'제2종근린생활시설'**이면서 대장 괄호 안에 **'(수리점)'** 등으로 세부 표기가 되어 있거나, 관할 관청에 **표시변경**을 통해 **'제2종근린생활시설 (수리점)'** 또는 **'자동차관련시설'**로 등재할 수 있다면 카센터 및 소규모 수리점 영업이 **합법적으로 가능**합니다!"
                )
            else:
                legal_actions.append("🔧 **[정비공장 적합]** 주용도가 '자동차관련시설'로 완벽하게 부합합니다.")

        elif "일반 숙박업" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 제한] 일반숙박업은 주용도가 반드시 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **[중요한 대안]** 상가나 주택 건물은 숙박시설 용도변경이 법적으로 불가능하므로, 처음부터 주용도가 **'숙박시설'**인 건물 물건만 선택하셔야 합니다."
                )
            else:
                legal_actions.append("🏨 **[숙박업 적합]** 공중위생관리법에 따른 숙박업 영업신고 및 소방시설완비증명서 필수.")

        elif "생활숙박시설" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반 / 입점 제한] 생활숙박시설(레지던스)은 반드시 주용도가 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **[중요한 대안]** 주용도가 '숙박시설'로 허가된 물건만 취득 및 운영할 수 있습니다."
                )
            else:
                warnings.append(
                    "[주거용 사용 규제 주의] 생활숙박시설은 공중위생관리법상 '숙박업' 신고를 하고 운영해야 합니다. 주거용 불법 사용 시 이행강제금 부과 대상이 됩니다."
                )
                legal_actions.append("🏨 **[생활숙박시설 적합]** 위탁운영사 계약 여부 및 주차장 설치 기준 확인.")

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
                legal_actions.append("🏡 **[외국인관광 도시민박업 적합]** 도시민박업 지정 신청 및 소방안전기준 준수.")

        elif "펜션 및 휴양콘도미니엄" in target_biz:
            if bld_use != "숙박시설":
                fatal_errors.append(
                    f"[건축법 위반] 펜션 및 휴양콘도미니엄은 주용도가 **'숙박시설'**이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **해결 대안:** 숙박시설 주용도로 허가된 부지 및 건물만 계약 가능합니다."
                )
            else:
                warnings.append(
                    "[개별 인허가법 주의] 펜션은 건축법상 '숙박시설' 외에도 '농어촌정비법'(농어촌민박업) 또는 '관광진흥법'에 따른 별도 등록 요건을 충족해야 합니다."
                )
                legal_actions.append("🏡 **[펜션/콘도 적합]** 개인 오수처리시설 용량 검토 필수.")

        elif "일반미용업·헤어샵" in target_biz or "네일아트 및 피부미용실" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설"]:
                warnings.append(
                    f"[미용업 합법화 대안] 주용도가 제1종 또는 제2종 근린생활시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제1종 또는 제2종 근린생활시설'**로 변경 후 입점하세요."
                )
            else:
                legal_actions.append("💄 **[미용업 적합]** 공중위생관리법에 따른 면허증 보유 및 소독 장비 구비.")

        elif "목욕장업" in target_biz:
            if bld_use != "제2종근린생활시설":
                warnings.append(
                    f"[목욕장업 합법화 대안] 대중목욕탕 및 사우나는 주용도가 '제2종근린생활시설'이어야 합니다. (현재 주용도: {bld_use}) "
                    f"💡 **[합법화 대안]** 관할 관청에 **표시변경**을 신청하여 주용도를 **'제2종근린생활시설'**로 변경해야 합니다."
                )
            else:
                legal_actions.append("♨️ **[목욕장업 적합]** 수질검사 성적서 및 대형 정화조 용량 확보 필수.")

        elif "공인중개사사무소" in target_biz or "일반 법무사·행정사·세무사 사무소" in target_biz or "일반 기업체 오피스" in target_biz:
            if bld_use not in ["제2종근린생활시설", "업무시설"]:
                warnings.append(
                    f"[사무소 합법화 대안] 주용도가 제2종근린생활시설 또는 업무시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 주용도를 **'제2종근린생활시설'** 또는 **'업무시설'**로 변경 후 입점하세요."
                )
            else:
                legal_actions.append("💼 **[오피스 입점 적합]** 건축법상 사무소 용도에 부합합니다.")

        elif "금융업소" in target_biz:
            if bld_use not in ["제1종근린생활시설", "제2종근린생활시설", "업무시설"]:
                warnings.append(
                    f"[금융업소 합법화 대안] 제1·2종 근린생활시설 또는 업무시설이어야 합니다. (현재: {bld_use}) "
                    f"💡 **[합법화 대안]** **표시변경**을 통해 근린생활시설 또는 업무시설로 변경하세요."
                )
            else:
                legal_actions.append("🏦 **[금융업소 적합]** ATM 설치 시 바닥 하중 및 보안시설 확인.")

        else:
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

    # 탭 구성
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
            st.warning("### ⚠ [주의 및 필수 검토 / 용도변경·표시변경 합법화 대안 가이드]")
            for w in warnings: 
                st.markdown(f"- {w}")
            st.markdown("---")
            
        if legal_actions:
            st.markdown("### 🛠️ [실무 법적 조치 및 상세 가이드]")
            for act in legal_actions: 
                st.markdown(f"- {act}")

    with tab2:
        st.subheader("💰 상하수도 원인자부담금 시뮬레이션")
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

        st.markdown(f"- **현재 건물(호실) 계약전력:** `{current_power} kW`")
        st.markdown(f"- **업종별 현실적 권장 소요전력:** 약 `{req_power:.1f} kW` (상가/사무소 표준 부하 산정 기준)")

        if power_diff > 0:
            st.warning(f"⚠ **[승압 필요]** 현재 전력보다 약 `{power_diff:.1f} kW`의 추가 전력이 필요합니다.")
            st.markdown(f"- **예상 한전 표준시설부담금(참고용):** 약 **{est_electric_fee:,.0f} 원** *(한전 불입금 별도)*")
        else:
            st.success("✅ **[전기 용량 충분]** 현재 계약전력으로 정상적인 영업 가동이 가능합니다.")

    with tab4:
        st.subheader("🧯 소방, 환경 및 위생 규제 요건 상세 심사")
        if "유흥주점" in target_biz or "단란주점" in target_biz or "PC방" in target_biz or "노래연습장" in target_biz or "청소년게임제공업" in target_biz or "무도장" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz:
            st.markdown("- **다중이용업소 특별법 / 숙박시설 소방안전기준:** 소방시설완비증명서, 방염필증, 객실별 완강기 및 화재경보기 설치 의무 대상.")
        elif "병원" in target_biz or "치과의원" in target_biz or "한의원" in target_biz or "동물병원" in target_biz:
            st.markdown("- **의료폐기물:** 감염성·의료폐기물 전용 보관함 및 전문 처리업체 계약 필수.")
        elif "세차장" in target_biz or "세탁소" in target_biz:
            st.markdown("- **환경부 수질·대기관리:** 폐수배출시설 / 대기환경보전법에 따른 세탁기기 배출시설 설치 허가·신고 대상 여부 검토 필수.")
        else:
            st.markdown("- 일반 건축물 소방안전점검 기준 준수 대상.")

    with tab5:
        st.subheader("🚽 건물 정화조 용량 검토 및 오수 발생량")
        est_dis = area * rate
        st.markdown(f"- 추정 일일 오수량: `{est_dis:.1f} 톤/일`")
        if est_dis >= 5.0 or "음식점" in target_biz or "목욕장" in target_biz or "무도장" in target_biz or "숙박" in target_biz or "생활숙박시설" in target_biz or "펜션" in target_biz or "세탁소" in target_biz:
            st.warning("⚠️ 오수 발생량이 많거나 수질오염 유발 시설이므로, 건물 정화조 인용 초과 여부를 관리사무소에 반드시 확인하세요.")
        else:
            st.success("✅ 정화조 오수 부담 안정적")
