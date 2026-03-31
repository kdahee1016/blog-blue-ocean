import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai
import re

# --- [1. 스타일 및 화면 설정] ---
st.set_page_config(page_title="제미나이 꿀키워드 분석기", layout="wide")
st.markdown("""
<style>
    .keyword-badge { display: inline-block; background-color: #f0f7ff; color: #007bff; padding: 4px 12px; border-radius: 12px; font-size: 14px !important; margin: 4px; border: 1px solid #cce5ff; }
    div[data-testid="stMarkdownContainer"] p { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정 및 모델 자동 탐색] ---
try:
    cust_id = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    ad_key = str(st.secrets["AD_API_KEY"]).strip()
    ad_secret = str(st.secrets["AD_SECRET_KEY"]).strip()
    s_id = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    s_secret = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()
    g_key = st.secrets["GEMINI_API_KEY"]

    genai.configure(api_key=g_key)
    # 모델 자동 탐색 (404 에러 방지)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(target_model)
except Exception as e:
    st.error(f"❌ 설정 로드 실패 (secrets.toml 확인 필요): {e}")
    st.stop()

# --- [3. 핵심 함수 정의] ---

def get_header(method, uri):
    """네이버 광고 API 인증 헤더 생성"""
    timestamp = str(int(time.time() * 1000))
    message = timestamp + "." + method + "." + uri
    h = hmac.new(ad_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(h.digest()).decode('utf-8')
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': ad_key,
        'X-Customer': cust_id,
        'X-Signature': signature
    }

def get_blog_count(keyword):
    """네이버 검색 API를 이용한 블로그 발행량 조회"""
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {"X-Naver-Client-Id": s_id, "X-Naver-Client-Secret": s_secret}
    try:
        res = requests.get(url, headers=headers, params={"query": keyword, "display": 1}, timeout=5)
        return res.json().get('total', 0) if res.status_code == 200 else 0
    except: return 0

def ask_gemini(prompt):
    """제미나이에게 키워드 추천 요청"""
    try:
        response = model.generate_content(prompt + " 답변은 다른 설명 없이 키워드만 콤마(,)로 구분해서 나열해줘.")
        if response and response.text:
            return [k.strip() for k in response.text.split(',') if k.strip()]
        return []
    except Exception as e:
        st.error(f"🤖 제미나이 응답 오류: {e}")
        return []

def analyze_keywords(keyword_list):
    """네이버 광고 API 데이터를 활용한 블루오션 지수 분석"""
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    status_text = st.empty()
    
    # 👶 육아 가중치 단어 (10살 아드님 맞춤형)
    child_words = ['아이', '아기', '가족', '초등', '체험', '교육', '박물관', '역사', '유적', '어린이', '제주']
    
    for idx, kw in enumerate(keyword_list[:15]):
        # [정밀 세척] 특수문자 제거
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        if not clean_kw: continue
        
        status_text.text(f"📊 분석 중 ({idx+1}/15): {clean_kw}")
        
        # 🔥 [11001 에러 해결 핵심]
        # 공백을 콤마(,)로 치환하여 네이버 API가 파라미터 오류를 내지 않게 합니다.
        hint_param = clean_kw.replace(" ", ",")
        params = {'hintKeywords': hint_param, 'showDetail': '1'}
        
        try:
            headers = get_header('GET', uri)
            resp = requests.get(BASE_URL + uri, params=params, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    # 검색량 추출 로직
                    def p(v): return v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    
                    # 블로그 지수 계산 (발행량)
                    blog = get_blog_count(clean_kw)
                    
                    # 블루오션 지수 계산 및 가중치 부여
                    is_child = any(cw in clean_kw for cw in child_words)
                    index = round((vol / (blog if blog > 0 else 1) * 100) * (1.8 if is_child else 1.0), 2)
                    
                    results.append({
                        '키워드': clean_kw, '총검색량': vol, '블로그수': blog, 
                        '블루오션지수': index, '추천': '👶' if is_child else ''
                    })
            else:
                # 에러 발생 시 상세 메시지 출력 (디버깅용)
                st.warning(f"⚠️ '{clean_kw}' 분석 건너뜀: {resp.text}")
            
            time.sleep(0.5)
        except: continue
        
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면 구성] ---
st.title("🤖 제미나이 x 네이버 꿀키워드 분석기")

if 'trends' not in st.session_state: st.session_state['trends'] = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("💡 카테고리 트렌드")
    cat = st.selectbox("주제 선택", ["국내여행", "해외여행", "초등학생", "맛집", "스포츠"])
    if st.button("✨ 트렌드 키워드 추출"):
        with st.spinner("제미나이 분석 중..."):
            res = ask_gemini(f"육아 블로거를 위한 {cat} 카테고리 핫키워드 5개")
            if res:
                st.session_state['trends'] = res
                st.rerun()
    
    if st.session_state['trends']:
        st.write("")
        for t in st.session_state['trends']:
            st.markdown(f'<span class="keyword-badge"># {t}</span>', unsafe_allow_html=True)

with col2:
    st.subheader("🚀 블루오션 키워드 발굴")
    target = st.text_input("메인 키워드 입력", placeholder="예: 제주
