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

# 글씨 크기 조절을 위한 CSS (14px 고정)
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

# --- [2. API 설정 및 모델 자동 선택] ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 모델 목록 중 사용 가능한 것 자동 선택
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_name)
    
    # 네이버 API 키
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
except Exception as e:
    st.error(f"⚠️ 설정 확인 필요: {e}")
    st.stop()

# --- [3. 핵심 함수들] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    message = f"{timestamp}.{method}.{uri}"
    h = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(h.digest()).decode('utf-8')
    return {'Content-Type': 'application/json', 'X-Timestamp': timestamp, 'X-API-KEY': AD_API_KEY, 'X-Customer': AD_CUSTOMER_ID, 'X-Signature': signature}

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
        if response and response.text:
            return [k.strip() for k in response.text.split(',') if k.strip()]
    except: return []

def analyze_gemini_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    
    # 👶 가중치 단어 (10살 아들 맞춤형)
    child_words = ['아이', '가족', '초등학생', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']
    
    status_text = st.empty()
    # 💡 [변경] 너무 많으면 터지니까 알짜배기 20개만 집중 분석합니다.
    target_list = keyword_list[:20] 
    
    for idx, kw in enumerate(target_list):
        status_text.text(f"📊 분석 중 ({idx+1}/{len(target_list)}): {kw}")
        
        # 키워드에서 공백 제거 등 정제 (네이버 API 인식률 향상)
        clean_kw = kw.strip().replace("#", "")
        params = {'hintKeywords': clean_kw, 'showDetail': '1', 'biztpId': '15'}
        
        try:
            resp = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri), timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    # 입력한 키워드와 가장 유사한 데이터 찾기
                    item = data[0] 
                    def parse(v):
                        if isinstance(v, int): return v
                        return 5 if isinstance(v, str) and '<' in v else 0
                    
                    vol = parse(item['monthlyPcQcCnt']) + parse(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    
                    if blog > 0:
                        is_child = any(cw in clean_kw for cw in child_words)
                        bonus = 1.8 if is_child else 1.0
                        index = round((vol / blog * 100) * bonus, 2)
                        
                        results.append({
                            '키워드': clean_kw, '총검색량': vol, '블로그수': blog, 
                            '블루오션지수': index, '추천': '👶' if is_child else ''
                        })
            
            # 💡 [변경] 네이버 차단을 피하기 위해 쉬는 시간을 살짝 늘립니다.
            time.sleep(0.2) 
            
        except Exception as e:
            print(f"Error analyzing {kw}: {e}")
            continue
            
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 화면 구성] ---
st.title("🤖 제미나이 x 네이버 분석기 (육아 맞춤형)")

if 'trend_list' not in st.session_state: 
    st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 2])

with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "스포츠", "도서", "초등학생"])
    if st.button(f"✨ {category} 트렌드 확인"):
        st.session_state['trend_list'] = ask_gemini_keywords(f"육아 블로거를 위한 {category} 관련 포스팅 꿀키워드 5개")
        st.rerun()

    if st.session_state['trend_list']:
        st.divider()
        st.subheader("💡 제미나이 추천")
        for tk in st.session_state['trend_list']:
            st.markdown(f'<span class="keyword-badge"># {tk}</span>', unsafe_allow_html=True)

with col2:
    search_input = st.text_input("분석할 메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 블루오션 키워드 40개 분석 시작"):
        if search_input:
            with st.spinner("제미나이 추천 키워드 데이터 수집 중..."):
                keywords = ask_gemini_keywords(f"'{search_input}' 관련 네이버 블로그 세부 키워드 40개. 콤마로만 구분.")
                df = analyze_gemini_keywords(keywords)
                if not df.empty:
                    st.success("분석 완료!")
                    final_df = df.sort_values('블루오션지수', ascending=False).head(30).reset_index(drop=True)
                    final_df.index = final_df.index + 1
                    st.dataframe(final_df, use_container_width=True)
                    st.balloons()
                else:
                    st.error("분석 결과가 없습니다. 다시 시도해 주세요.")
