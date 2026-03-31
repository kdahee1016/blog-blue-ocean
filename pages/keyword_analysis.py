import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai
import re

# --- [1. 화면 설정 및 스타일] ---
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")
st.markdown("""<style>.keyword-badge { display: inline-block; background-color: #f0f7ff; color: #007bff; padding: 4px 12px; border-radius: 12px; font-size: 14px !important; margin: 4px; border: 1px solid #cce5ff; }</style>""", unsafe_allow_html=True)

# --- [2. API 설정 및 모델 자동 찾기] ---
try:
    cust_id = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    ad_key = str(st.secrets["AD_API_KEY"]).strip()
    ad_secret = str(st.secrets["AD_SECRET_KEY"]).strip()
    s_id = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    s_secret = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()
    g_key = st.secrets["GEMINI_API_KEY"]

    genai.configure(api_key=g_key)
    
    # 🔥 [핵심 수정] 사용 가능한 모델을 리스트에서 자동으로 찾습니다.
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # gemini-1.5-flash가 있으면 쓰고, 없으면 리스트의 첫 번째 모델을 씁니다.
    target_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(target_model)
    
except Exception as e:
    st.error(f"❌ 설정 로드 실패: {e}")
    st.stop()

# --- [3. 함수 정의] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    message = timestamp + "." + method + "." + uri
    h = hmac.new(ad_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(h.digest()).decode('utf-8')
    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp, 'X-API-KEY': ad_key, 'X-Customer': cust_id, 'X-Signature': signature}

def get_blog_count(keyword):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {"X-Naver-Client-Id": s_id, "X-Naver-Client-Secret": s_secret}
    try:
        res = requests.get(url, headers=headers, params={"query": keyword, "display": 1}, timeout=5)
        return res.json().get('total', 0) if res.status_code == 200 else 0
    except: return 0

def ask_gemini(prompt):
    try:
        # 모델 응답 생성
        response = model.generate_content(prompt + " 답변은 다른 설명 없이 콤마(,)로만 구분해서 키워드만 나열해줘.")
        if response and response.text:
            return [k.strip() for k in response.text.split(',') if k.strip()]
        return []
    except Exception as e:
        st.error(f"🤖 제미나이 응답 오류: {e}")
        return []

def analyze_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    status_text = st.empty()
    
    # 👶 가중치 키워드 (10살 아드님 맞춤형)
    child_words = ['아이', '가족', '초등', '체험', '교육', '박물관', '역사', '유적', '어린이']
    
    for idx, kw in enumerate(keyword_list[:15]):
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        if not clean_kw: continue
        status_text.text(f"📊 네이버 데이터 분석 중 ({idx+1}/15): {clean_kw}")
        
        try:
            resp = requests.get(BASE_URL + uri, params={'hintKeywords': clean_kw, 'showDetail': '1'}, headers=get_header('GET', uri), timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    p = lambda v: v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    
                    is_child = any(cw in clean_kw for cw in child_words)
                    bonus = 1.8 if is_child else 1.0
                    index = round((vol / (blog if blog > 0 else 1) * 100) * bonus, 2)
                    
                    results.append({
                        '키워드': clean_kw, '총검색량': vol, '블로그수': blog, 
                        '블루오션지수': index, '추천': '👶' if is_child else ''
                    })
            else:
                st.warning(f"⚠️ '{clean_kw}' 네이버 응답 실패 ({resp.status_code})")
            time.sleep(0.4)
        except: continue
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면 구성] ---
st.title("🤖 제미나이 x 네이버 키워드 비기")

if 'trends' not in st.session_state: st.session_state['trends'] = []

c1, c2 = st.columns([1, 2])
with c1:
    cat = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "초등학생", "맛집", "스포츠"])
    if st.button("✨ 트렌드 확인"):
        with st.spinner("제미나이가 키워드 뽑는 중..."):
            res = ask_gemini(f"육아 블로거를 위한 {cat} 카테고리 핫키워드 5개")
            if res:
                st.session_state['trends'] = res
                st.rerun()
    
    if st.session_state['trends']:
        st.divider()
        for t in st.session_state['trends']:
            st.markdown(f'<span class="keyword-badge"># {t}</span>', unsafe_allow_html=True)

with c2:
    target = st.text_input("메인 키워드 입력", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 블루오션 분석 시작"):
        if target:
            with st.spinner("데이터 분석 중... 잠시만 기다려주세요!"):
                kws = ask_gemini(f"'{target}' 관련 네이버 블로그용 세부 키워드 15개")
                if kws:
                    df = analyze_keywords(kws)
                    if not df.empty:
                        st.success("분석 완료!")
                        st.dataframe(df.sort_values('블루오션지수', ascending=False).reset_index(drop=True), use_container_width=True)
                        st.balloons()
                    else:
                        st.error("분석 결과가 없습니다. 네이버 API 설정을 확인해주세요.")
