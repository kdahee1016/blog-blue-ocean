import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai

# --- [1. 스타일 설정] ---
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")
st.markdown("""
<style>
    .keyword-badge { display: inline-block; background-color: #f0f7ff; color: #007bff; padding: 4px 12px; border-radius: 12px; font-size: 14px !important; margin: 4px; border: 1px solid #cce5ff; }
    div[data-testid="stMarkdownContainer"] p { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정] ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(model_name)
    
    # 비밀값 로드
    AD_CUSTOMER_ID = str(st.secrets["AD_CUSTOMER_ID"])
    AD_API_KEY = str(st.secrets["AD_API_KEY"])
    AD_SECRET_KEY = str(st.secrets["AD_SECRET_KEY"])
    SEARCH_CLIENT_ID = str(st.secrets["SEARCH_CLIENT_ID"])
    SEARCH_CLIENT_SECRET = str(st.secrets["SEARCH_CLIENT_SECRET"])
except Exception as e:
    st.error(f"❌ 설정 오류: {e}")
    st.stop()

# --- [3. 핵심 함수: 네이버 인증 방식 정밀 수정] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    # 네이버 가이드에 맞춰 메시지 생성 방식을 더 엄격하게 수정
    message = timestamp + "." + method + "." + uri
    hash = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(hash.digest()).decode('utf-8')
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': AD_API_KEY,
        'X-Customer': AD_CUSTOMER_ID,
        'X-Signature': signature
    }

def get_blog_count(keyword):
    url = f"https://openapi.naver.com/v1/search/blog.json?query={keyword}&display=1"
    headers = {"X-Naver-Client-Id": SEARCH_CLIENT_ID, "X-Naver-Client-Secret": SEARCH_CLIENT_SECRET}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        return res.json().get('total', 0) if res.status_code == 200 else 0
    except: return 0

def ask_gemini_keywords(prompt):
    try:
        response = model.generate_content(prompt + " 답변은 설명 없이 키워드만 콤마(,)로 구분해서 나열해줘.")
        return [k.strip() for k in response.text.split(',') if k.strip()]
    except: return []

# --- [4. 데이터 분석 함수: 안정성 극대화] ---
def analyze_gemini_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    child_words = ['아이', '가족', '초등학생', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']
    
    status_text = st.empty()
    # 안정성을 위해 15개만 집중 분석 (성공하면 나중에 늘려보세요!)
    target_list = keyword_list[:15] 
    
    for idx, kw in enumerate(target_list):
        status_text.text(f"📊 분석 중 ({idx+1}/{len(target_list)}): {kw}")
        # 키워드에서 불필요한 공백/기호 제거
        clean_kw = kw.strip().replace("#", "").replace("[", "").replace("]", "")
        params = {'hintKeywords': clean_kw, 'showDetail': '1'} # biztpId 제거로 범용성 확보
        
        try:
            headers = get_header('GET', uri)
            resp = requests.get(BASE_URL + uri, params=params, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    p = lambda v: v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    
                    if blog > 0:
                        is_child = any(cw in clean_kw for cw in child_words)
                        index = round((vol / blog * 100) * (1.8 if is_child else 1.0), 2)
                        results.append({'키워드': clean_kw, '총검색량': vol, '블로그수': blog, '블루오션지수': index, '추천': '👶' if is_child else ''})
            else:
                # 에러 로그 출력 (문제가 생기면 화면에 에러 코드가 보일 겁니다)
                st.write(f"⚠️ {clean_kw}: 네이버 응답 오류({resp.status_code})")
                
            time.sleep(0.3) # 네이버 차단 방지용 넉넉한 대기 시간
        except Exception as e:
            continue
            
    status_text.empty()
    return pd.DataFrame(results)

# --- [5. 화면 구성] ---
st.title("🤖 제미나이 x 네이버 꿀키워드 (최종 보정판)")

if 'trend_list' not in st.session_state: st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 2])
with col1:
    category = st.selectbox("카테고리", ["국내여행", "해외여행", "스포츠", "도서", "초등학생"])
    if st.button(f"✨ {category} 트렌드"):
        st.session_state['trend_list'] = ask_gemini_keywords(f"육아 블로거를 위한 {category} 핫키워드 5개")
        st.rerun()
    if st.session_state['trend_list']:
        st.write("---")
        for tk in st.session_state['trend_list']:
            st.markdown(f'<span class="keyword-badge"># {tk}</span>', unsafe_allow_html=True)

with col2:
    search_input = st.text_input("메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 꿀키워드 분석 시작"):
        if search_input:
            with st.spinner("제미나이 키워드 생성 및 데이터 조회 중..."):
                keywords = ask_gemini_keywords(f"'{search_input}' 관련 네이버 블로그 꿀키워드 15개. 콤마로만.")
                df = analyze_gemini_keywords(keywords)
                if not df.empty:
                    st.success("분석 완료!")
                    st.dataframe(df.sort_values('블루오션지수', ascending=False), use_container_width=True)
                    st.balloons()
                else:
                    st.error("분석 결과가 없습니다. 네이버 API 키 설정을 다시 확인해주세요.")error("분석 결과가 없습니다. 다시 시도해 주세요.")
