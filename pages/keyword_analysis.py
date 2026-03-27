import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai

# --- [1. 화면 설정 및 스타일] ---
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")

# 글씨 크기 조절 및 배지 스타일 CSS
st.markdown("""
<style>
    .keyword-badge {
        display: inline-block;
        background-color: #f0f7ff;
        color: #007bff;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px !important;
        font-weight: 500;
        margin: 4px;
        border: 1px solid #cce5ff;
    }
    div[data-testid="stMarkdownContainer"] p { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정 및 보안 값 로드] ---
try:
    AD_CUSTOMER_ID = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    AD_API_KEY = str(st.secrets["AD_API_KEY"]).strip()
    AD_SECRET_KEY = str(st.secrets["AD_SECRET_KEY"]).strip()
    SEARCH_CLIENT_ID = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    SEARCH_CLIENT_SECRET = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"❌ 설정 로드 오류: {e}")
    st.stop()

# --- [3. 핵심 함수들] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    message = timestamp + "." + method + "." + uri
    h = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(h.digest()).decode('utf-8')
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': AD_API_KEY,
        'X-Customer': AD_CUSTOMER_ID,
        'X-Signature': signature
    }

def get_blog_count(keyword):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {"X-Naver-Client-Id": SEARCH_CLIENT_ID, "X-Naver-Client-Secret": SEARCH_CLIENT_SECRET}
    params = {"query": keyword, "display": 1}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
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
    child_words = ['아이', '가족', '초등학생', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']
    
    status_text = st.empty()
    target_list = keyword_list[:15]
    
    for idx, kw in enumerate(target_list):
        # 🔥 [강력 세척] 알파벳, 한글, 숫자, 공백 제외하고 전부 제거
        import re
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        
        # 만약 세척 후 빈 문자열이면 패스
        if not clean_kw:
            continue

        status_text.text(f"📊 분석 중 ({idx+1}/{len(target_list)}): {clean_kw}")
        
        # 네이버 규격: 키워드 사이의 공백은 유지하되 앞뒤는 없어야 함
        params = {'hintKeywords': clean_kw, 'showDetail': '1'}
        
        try:
            resp = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri), timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    def parse(v): return v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = parse(item['monthlyPcQcCnt']) + parse(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    if blog > 0:
                        is_child = any(cw in clean_kw for cw in child_words)
                        index = round((vol / blog * 100) * (1.8 if is_child else 1.0), 2)
                        results.append({'키워드': clean_kw, '총검색량': vol, '블로그수': blog, '블루오션지수': index, '추천': '👶' if is_child else ''})
            else:
                # 에러가 나면 어떤 '값' 때문에 났는지 확인용
                st.warning(f"⚠️ '{clean_kw}' 요청 실패: {resp.text}")
                
            time.sleep(0.4) # 안전하게 조금 더 쉽니다.
        except: continue
        
    status_text.empty()
    return pd.DataFrame(results)
# --- [4. 메인 화면 구성] ---
st.title("🤖 제미나이 x 네이버 꿀키워드 분석기")

if 'trend_list' not in st.session_state:
    st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 2])

with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "스포츠", "도서", "초등학생"])
    if st.button(f"✨ {category} 핫키워드 추출"):
        with st.spinner("제미나이 분석 중..."):
            st.session_state['trend_list'] = ask_gemini_keywords(f"육아 블로거를 위한 {category} 관련 인기 포스팅 키워드 5개")
            st.rerun()

    if st.session_state['trend_list']:
        st.divider()
        st.subheader("💡 제미나이 추천")
        for tk in st.session_state['trend_list']:
            st.markdown(f'<span class="keyword-badge"># {tk}</span>', unsafe_allow_html=True)

with col2:
    search_input = st.text_input("분석할 메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 블루오션 키워드 분석 시작"):
        if search_input:
            with st.spinner("데이터를 수집하고 분석하는 중입니다..."):
                keywords = ask_gemini_keywords(f"'{search_input}' 관련 네이버 블로그 세부 키워드 15개. 콤마로만 구분.")
                df = analyze_gemini_keywords(keywords)
                if not df.empty:
                    st.success("분석 완료!")
                    final_df = df.sort_values('블루오션지수', ascending=False).reset_index(drop=True)
                    final_df.index = final_df.index + 1
                    st.dataframe(final_df, use_container_width=True)
                    st.balloons()
                else:
                    st.error("분석 결과가 없습니다. API 설정을 다시 확인해주세요.")
