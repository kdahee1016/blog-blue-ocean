import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai

# --- [1. 스타일 정의 - 글씨 크기 진짜 진짜 줄이기] ---
# st.info 대신 st.write와 커스텀 HTML을 섞어서 글씨를 확 줄입니다.
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")

st.markdown("""
<style>
    /* 제미나이 추천 키워드 버튼 스타일 */
    .keyword-badge {
        display: inline-block;
        background-color: #e1f5fe;
        color: #01579b;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 14px !important; /* 글씨 크기 14px로 고정 */
        font-weight: 500;
        margin: 4px;
        border: 1px solid #b3e5fc;
    }
    /* 기존 st.info 강제 축소 */
    div[data-testid="stInfo"] * {
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정 및 모델 자동 선택] ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 사용 가능한 모델 자동 찾기
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_name)
    
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# --- [기존 함수들: get_header, get_blog_count, ask_gemini_keywords 등은 동일] ---
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
        response = model.generate_content(prompt + " 답변은 다른 설명 없이 키워드만 콤마(,)로 구분해서 나열해줘.")
        return [k.strip() for k in response.text.split(',') if k.strip()]
    except: return []

# --- [3. 데이터 분석 함수 보완 - 0건 방지] ---
def analyze_gemini_keywords(keyword_list, category_name):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    
    # 👶 육아/교육 블로거를 위한 핵심 가중치 단어 (10살 아드님 맞춤형)
    # 역사에 관심 많은 아드님을 위해 '역사', '유적' 등을 추가했습니다.
    child_words = ['아이', '가족', '초등', '체험', '교육', '박물관', '갈만한', '볼만한', '미술', '과학', '역사', '박물관', '어린이']
    
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
                        # ⭐ [가중치 부활] 아이/교육 관련 단어 포함 시 지수 1.8배 뻥튀기!
                        is_child_related = any(cw in kw for cw in child_words)
                        bonus = 1.8 if is_child_related else 1.0
                        
                        # 지수 계산 (검색량 / 블로그수 * 100 * 가중치)
                        index = round((vol / blog * 100) * bonus, 2)
                        
                        results.append({
                            '키워드': kw, 
                            '총검색량': vol, 
                            '블로그수': blog, 
                            '블루오션지수': index,
                            '비고': '👶추천' if is_child_related else '' # 가중치 붙은건 표시해줌
                        })
            time.sleep(0.06) # 네이버 서버 보호용
        except: continue
        
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면] ---
st.title("🤖 제미나이 x 네이버 분석기")

col1, col2 = st.columns([1, 2])

with col1:
    category = st.selectbox("카테고리", ["국내여행", "해외여행", "스포츠", "야구", "도서", "영화", "초등학생"])
    if st.button(f"✨ {category} 키워드 뽑기"):
        st.session_state['trend_list'] = ask_gemini_keywords(f"육아 블로거용 {category} 핫키워드 5개")
        st.rerun()

    if st.session_state.get('trend_list'):
        st.write("---")
        # st.info 대신 커스텀 HTML로 작게 출력!
        for tk in st.session_state['trend_list']:
            st.markdown(f'<span class="keyword-badge"># {tk}</span>', unsafe_allow_html=True)

with col2:
    search_input = st.text_input("메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 꿀키워드 분석 시작"):
        if search_input:
            with st.spinner("제미나이가 키워드를 선별하고 네이버 데이터를 조회 중입니다..."):
                # 프롬프트 구체화 (특수기호 빼달라고 요청)
                prompt = f"'{search_input}' 관련 네이버 블로그용 세부 키워드 40개. 콤마로만 구분, 특수문자 금지."
                keywords = ask_gemini_keywords(prompt)
                
                df = analyze_gemini_keywords(keywords, category)
                if not df.empty:
                    st.success("분
