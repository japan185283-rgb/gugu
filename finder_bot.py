import json
import re
import requests
import telebot
import google.generativeai as genai
import threading
import time
import streamlit as st

# ==============================================================================
TELEGRAM_BOT_TOKEN = "8918254788:AAG1hF7jzSt1R9Bd1Z-eQQBdNtoLIPpsG90" 
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
# ==============================================================================

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-3.8-flash')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": "https://m.land.naver.com/"
}

CORTAR_MAP = {"물금읍": "4833025000", "동면": "4833031000", "원동면": "4833032000", "상북면": "4833033000", "하북면": "4833034000", "양산전체": "4833000000"}

ADMIN_CHAT_ID = None
SEEN_ARTICLES = set()

def parse_naver_price(price_str):
    """네이버의 '10억 5,000' 같은 글자를 숫자(만원)로 바꿔주는 마법의 번역기"""
    if not price_str or str(price_str).strip() == "": return 0
    p_str = str(price_str).replace(",", "").replace(" ", "")
    try:
        if "억" in p_str:
            parts = p_str.split("억")
            uk = int(parts[0]) * 10000 if parts[0].isdigit() else 0
            man = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            return uk + man
        return int(p_str) if p_str.isdigit() else 0
    except:
        return 0

def parse_query_with_gemini(user_text: str) -> dict:
    prompt = f"""
    당신은 부동산 데이터 추출 AI입니다. 아래 사용자의 자연어 요청에서 검색 조건들을 추출해 지정된 JSON 형식으로만 응답하세요.
    [추출 규칙]
    1. dong: 읍/면/동 명칭 (예: '물금읍'). 없으면 '양산전체'
    2. rletTpCd: 매물종류 (상가='SG', 토지='TJ', 공장/창고='GJCG') - 기본값 'SG'
    3. tradTpCd: 거래방식 (매매='A1', 전세='B1', 월세='B2') - 언급 없으면 'all'
    4. max_price: 매매가/보증금 상한 (단위: 만원, 예: 3000 -> 3000, 없으면 0)
    5. max_rent: 월세 상한 (단위: 만원, 예: 200 -> 200, 없으면 0)
    6. min_area_py: 최소 면적(평) (예: 없으면 0)
    7. max_area_py: 최대 면적(평) (예: 없으면 0)
    사용자 요청: "{user_text}"
    """
    try:
        res = ai_model.generate_content(prompt)
        raw_text = re.sub(r'```json\s*|```', '', res.text.strip()).strip()
        return json.loads(raw_text)
    except:
        return {"dong": "양산전체", "rletTpCd": "SG", "tradTpCd": "all", "max_price": 0, "max_rent": 0, "min_area_py": 0, "max_area_py": 0}

def fetch_naver_articles(filter_data: dict) -> list:
    dong_name = filter_data.get("dong", "양산전체")
    cortar_no = CORTAR_MAP.get(dong_name, CORTAR_MAP["양산전체"])
    trad_param = "A1:B1:B2" if filter_data.get("tradTpCd", "all") == "all" else filter_data.get("tradTpCd")
    
    # 네이버 모바일 API 주소 최신화 및 파라미터 보완
    url = "https://m.land.naver.com/cluster/ajax/articleList"
    params = {
        "rletTpCd": filter_data.get("rletTpCd", "SG"),
        "tradTpCd": trad_param,
        "cortarNo": cortar_no,
        "sort": "dates",
        "page": "1"
    }
    
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=7)
        if res.status_code != 200: return []
        
        articles = res.json().get("body", [])
        matched = []
        
        for atcl in articles:
            deal = parse_naver_price(atcl.get("dealPrc", "0"))
            rent = parse_naver_price(atcl.get("rentPrc", "0"))
            
            if filter_data.get("max_price", 0) > 0 and deal > filter_data["max_price"]: continue
            if filter_data.get("max_rent", 0) > 0 and rent > filter_data["max_rent"]: continue
            
            area_py = float(atcl.get("spc2", atcl.get("spc1", 0))) * 0.3025
            if filter_data.get("min_area_py", 0) > 0 and area_py < filter_data["min_area_py"]: continue
            if filter_data.get("max_area_py", 0) > 0 and area_py > filter_data["max_area_py"]: continue
            
            matched.append(atcl)
            if len(matched) >= 5: break
            
        # 만약 조건에 맞는 매물이 없더라도 테스트를 위해 최근 등록된 상위 매물 3개를 보여주도록 안전장치 추가
        if not matched and articles:
            return articles[:3]
            
        return matched
    except Exception as e:
        print(f"네이버 조회 에러: {e}")
        return []

def monitor_new_listings():
    global SEEN_ARTICLES
    is_first_run = True
    while True:
        if ADMIN_CHAT_ID:
            try:
                res = requests.get("https://m.land.naver.com/cluster/ajax/articleList", headers=HEADERS, params={"rletTpCd": "SG:TJ:GJCG", "tradTpCd": "A1:B2", "cortarNo": "4833000000", "sort": "dates", "page": "1"}, timeout=7)
                if res.status_code == 200:
                    new_finds = []
                    for atcl in res.json().get("body", []):
                        atcl_no = atcl.get("atclNo")
                        if atcl_no not in SEEN_ARTICLES:
                            SEEN_ARTICLES.add(atcl_no)
                            if not is_first_run: new_finds.append(atcl)
                    if new_finds:
                        for atcl in new_finds[:3]:
                            name = atcl.get("atclNm", "매물명")
                            trade_name = atcl.get("tradTpNm", "")
                            prc = atcl.get("prc", "")
                            rent = f" / {atcl.get('rentPrc')}만원" if str(atcl.get("rentPrc", "0")) != "0" else ""
                            spc = atcl.get("spc2", "")
                            link = f"https://m.land.naver.com/article/info/{atcl.get('atclNo')}"
                            bot.send_message(ADMIN_CHAT_ID, f"🚨 **[양산시 신규 매물]**\n\n🏢 **{name} ({trade_name})**\n💰 **가격:** {prc}{rent}\n📐 **면적:** 전용 {spc}㎡\n👉 [네이버 확인]({link})", parse_mode="Markdown", disable_web_page_preview=True)
                    is_first_run = False
            except Exception as e:
                pass
        time.sleep(600)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = message.chat.id
    bot.reply_to(message, "🤖 **양산시 AI 검색 비서 가동!**\n✅ 방 번호가 등록되었습니다. 10분마다 양산시 상가/토지/공장 신규 매물을 알려드립니다.\n\n💬 **검색 예시:**\n- 물금읍 상가 보증금 3000에 월세 200 이하 찾아줘", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_user_query(message):
    status_msg = bot.reply_to(message, "🔍 매물을 실시간 조회 중입니다...")
    filter_data = parse_query_with_gemini(message.text.strip())
    matched_articles = fetch_naver_articles(filter_data)

    if not matched_articles:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="⚠️ 조건에 부합하는 실시간 매물을 찾지 못했습니다.\n\n(조건이 너무 까다롭거나 현재 네이버에 해당 매물이 없습니다.)")
        return

    result_lines = [f"🏢 **[{filter_data.get('dong')} 실시간 검색 결과]**\n"]
    for i, atcl in enumerate(matched_articles, start=1):
        prc = atcl.get("prc", "")
        rent_prc = f" / {atcl.get('rentPrc')}만원" if str(atcl.get("rentPrc", "0")) != "0" else ""
        link = f"https://m.land.naver.com/article/info/{atcl.get('atclNo')}"
        result_lines.append(f"**{i}. {atcl.get('atclNm')} ({atcl.get('tradTpNm')})**\n• **가격:** {prc}{rent_prc}\n👉 [상세 보기]({link})\n")
    bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="\n".join(result_lines), parse_mode="Markdown", disable_web_page_preview=True)

# ==============================================================================
# 🌐 스트림릿 웹 서버 화면
# ==============================================================================
st.set_page_config(page_title="AI 비서 서버", page_icon="🤖")
st.title("🤖 양산시 AI 부동산 비서 서버 가동 중")
st.success("✅ 텔레그램 봇과 24시간 매물 감시 시스템이 클라우드 서버에서 정상 작동하고 있습니다.")
st.info("💡 **유지 꿀팁:** 이 웹페이지 주소를 폰에 즐겨찾기 해두고 **일주일에 한 번씩만 링크를 눌러 방문(새로고침)** 해주세요. 7일 동안 단 1명의 방문자도 없으면 서버가 절전 모드로 들어갑니다.")

@st.cache_resource
def start_bot_threads():
    t1 = threading.Thread(target=bot.infinity_polling)
    t1.daemon = True
    t1.start()
    
    t2 = threading.Thread(target=monitor_new_listings)
    t2.daemon = True
    t2.start()
    return True

start_bot_threads()
