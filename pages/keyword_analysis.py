import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai

# --- [1. 스타일 및 화면 설정] ---
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")

# 글씨 크기를 14px로 강제 고정하는 CSS
st.markdown("""
<style>
    .keyword-badge {
        display: inline-block;
        background-color: #f0f7ff;
        color: #007bff;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 14px !important;
        font-weight: 500;
        margin: 3px;
        border: 1px solid #cce5ff;
    }
    div[data-testid="stInfo"] * { font-size: 14px !important; }
    div[data-testid="stMarkdownContainer"] p { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정 및 모델 자동 선택] ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_name)
    
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
except Exception as e:
    st.error(f"⚠️ 설정 확인 필요: {e}")
    st.stop()

# --- [3. 핵심 기능 함수들] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    message = "{}.{}.{}".format(timestamp, method, uri)
    hash = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(hash.digest()).decode('utf-8')
    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': AD_API_KEY, 'X-Customer': AD_CUSTOMER_ID, 'X-Signature': signature}

def get_blog_count(keyword):
    url = f"https://openapi.naver.com/v1/search/blog.json?query={keyword}&display=1"
    headers = {"X-Naver-Client-Id": SEARCH_CLIENT_ID, "X-Naver-Client-Secret": SEARCH_CLIENT_SECRET}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get('total', 0) if res.status_code == 200 else 0
    except: return 0

def ask_gemini_keywords(prompt):
    try:
        response = model.generate_content(prompt + " 답변은 설명 없이 키워드만 콤마(,)로 구분해서 나열해줘.")
        return [k.strip() for k in response.text.split(',') if k.strip()]
    except: return []

def analyze_gemini_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    
    # 👶 육아/역사/교육 가중치 단어
    child_words = ['아이', '가족', '초등', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']
    
    status_text = st.empty()
    for idx, kw in enumerate(keyword_list[:40]):
        status_text.text(f"📊 분석 중 ({idx+1}/{len(keyword_list[:40])}): {kw}")
        params = {'hintKeywords': kw, 'showDetail': '1', 'biztpId': '15'}
        try:
            resp = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    p = lambda v: v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(kw)
                    
                    if blog > 0:
                        is_child = any(cw in kw for cw in child_words)
                        bonus = 1.8 if is_child else 1.0
                        index = round((vol / blog * 100) * bonus, 2)
                        results.append({
                            '키워드': kw, '총검색량': vol, '블로그수': blog, 
                            '블루오션지수': index, '추천': '👶' if is_child else ''
                        })
            time.sleep(0.07)
        except: continue
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면 구성] ---
st.title("🤖 제미나이 x 네이버 분석기")

if 'trend_list' not in st.session_state: st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 2])

with col1:
    category = st.selectbox("카테고리", ["국내여행", "해외여행", "스포츠", "야구", "도서", "영화", "초등학생"])
    if st.button(f"✨ {category} 키워드 추출"):
        st.session_state['trend_list'] = ask_gemini_keywords(f"육아 블로거를 위한 {category} 카테고리 핫키워드 5개")
        st.rerun()

    if st.session_state['trend_list']:
        st.write("---")
        st.subheader("💡 제미나이 추천")
        for tk in st.session_state['trend_list']:
            st.markdown(f'<span class="keyword-badge"># {tk}</span>', unsafe_allow_html=True)

with col2:
    search_input = st.text_input("메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 꿀
