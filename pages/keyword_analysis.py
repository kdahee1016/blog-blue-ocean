import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai
import re # 특수문자 제거를 위해 추가

# --- [1. 스타일 및 화면 설정] ---
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")
st.markdown("""
<style>
    .keyword-badge { display: inline-block; background-color: #f0f7ff; color: #007bff; padding: 4px 12px; border-radius: 12px; font-size: 14px !important; margin: 4px; border: 1px solid #cce5ff; }
    div[data-testid="stMarkdownContainer"] p { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정] ---
try:
    AD_CUSTOMER_ID = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    AD_API_KEY = str(st.secrets["AD_API_KEY"]).strip()
    AD_SECRET_KEY = str(st.secrets["AD_SECRET_KEY"]).strip()
    SEARCH_CLIENT_ID = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    SEARCH_CLIENT_SECRET = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ 설정 오류: {e}")
    st.stop()

# --- [3. 핵심 함수들] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    message = timestamp + "." + method + "." + uri
    h = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(h.digest()).decode('utf-8')
    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': AD_API_KEY, 'X-Customer': AD_CUSTOMER_ID, 'X-Signature': signature}

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
        response = model.generate_content(prompt + " 답변은 다른 설명 없이 키워드만 콤마(,)로 구분해서 나열해줘.")
        return [k.strip() for k in response.text.split(',') if k.strip()]
    except: return []

def analyze_gemini_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    child_words = ['아이', '가족', '초등', '체험', '교육', '박물관', '역사', '유적', '어린이']
    
    status_text = st.empty()
    target_list = keyword_list[:10] # 진단을 위해 10개만 먼저 시도
    
    for idx, kw in enumerate(target_list):
        import re
        # 특수문자 제거 (11001 에러 방지)
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        if not clean_kw: continue

        status_text.text(f"📊 진단 분석 중 ({idx+1}/10): {clean_kw}")
        params = {'hintKeywords': clean_kw, 'showDetail': '1'}
        
        try:
            resp = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri), timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    p = lambda v: v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    
                    # 블로그 수가 0이라도 일단 지수 계산 진행 (나누기 0 방지)
                    bonus = 1.8 if any(w in clean_kw for w in child_words) else 1.0
                    index = round((vol / (blog if blog > 0 else 1) * 100) * bonus, 2)
                    results.append({'키워드': clean_kw, '총검색량': vol, '블로그수': blog, '블루오션지수': index, '추천': '👶' if bonus > 1.0 else ''})
            else:
                # 🚨 여기가 핵심! 네이버가 왜 거절했는지 에러 코드를 직접 보여줍니다.
                st.error(f"❌ 네이버 API 응답 오류 ({clean_kw}): {resp.status_code}")
                with st.expander("상세 에러 내용 보기"):
                    st.code(resp.text) # 이 내용을 복사해서 저에게 알려주세요!
                
            time.sleep(0.5)
        except Exception as e:
            st.warning(f"⚠️ 연결 실패: {e}")
            continue
            
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면 구성] ---
st.title("🤖 제미나이 x 네이버 꿀키워드 분석기")

if 'trend_list' not in st.session_state: st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 2])
with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "스포츠", "도서", "초등학생"])
    if st.button(f"✨ {category} 트렌드 확인"):
        st.session_state['trend_list'] = ask_gemini_keywords(f"육아 블로거를 위한 {category} 관련 인기 포스팅 키워드 5개")
        st.rerun()
    if st.session_state['trend_list']:
        st.divider()
        for tk in st.session_state['trend_list']:
            st.markdown(f'<span class="keyword-badge"># {tk}</span>', unsafe_allow_html=True)

with col2:
    search_input = st.text_input("분석할 메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 블루오션 분석 시작"):
        if search_input:
            with st.spinner("데이터 분석 중..."):
                keywords = ask_gemini_keywords(f"'{search_input}' 관련 네이버 블로그 세부 키워드 15개. 콤마로만 구분.")
                df = analyze_gemini_keywords(keywords)
                if not df.empty:
                    st.success("분석 완료!")
                    final_df = df.sort_values('블루오션지수', ascending=False).reset_index(drop=True)
                    final_df.index = final_df.index + 1
                    st.dataframe(final_df, use_container_width=True)
                    st.balloons()
                else:
                    st.error("분석 결과가 없습니다. API 설정을 확인해주세요.")
