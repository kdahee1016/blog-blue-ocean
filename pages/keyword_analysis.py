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

# --- [2. API 설정] ---
try:
    # secrets에서 값 가져오기 (공백 제거)
    cust_id = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    ad_key = str(st.secrets["AD_API_KEY"]).strip()
    ad_secret = str(st.secrets["AD_SECRET_KEY"]).strip()
    s_id = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    s_secret = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()
    g_key = st.secrets["GEMINI_API_KEY"]

    genai.configure(api_key=g_key)
    # 모델명을 명확하게 지정
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ 설정 로드 실패 (secrets.toml 확인): {e}")
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
        response = model.generate_content(prompt + " 답변은 콤마(,)로만 구분해서 키워드만 줘.")
        return [k.strip() for k in response.text.split(',') if k.strip()]
    except Exception as e:
        st.error(f"🤖 제미나이 응답 오류: {e}")
        return []

def analyze_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    status_text = st.empty()
    
    for kw in keyword_list[:10]: # 속도를 위해 10개만 테스트
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        if not clean_kw: continue
        status_text.text(f"📊 분석 중: {clean_kw}")
        
        try:
            resp = requests.get(BASE_URL + uri, params={'hintKeywords': clean_kw, 'showDetail': '1'}, headers=get_header('GET', uri), timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    p = lambda v: v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    bonus = 1.8 if any(w in clean_kw for w in ['아이', '가족', '체험', '역사', '초등']) else 1.0
                    index = round((vol / (blog if blog > 0 else 1) * 100) * bonus, 2)
                    results.append({'키워드': clean_kw, '총검색량': vol, '블로그수': blog, '블루오션지수': index, '추천': '👶' if bonus > 1.0 else ''})
            else:
                st.error(f"❌ 네이버 응답 에러 ({clean_kw}): {resp.status_code}")
                st.write(resp.text) # 에러 원문 출력
            time.sleep(0.5)
        except Exception as e:
            st.error(f"⚠️ 연결 오류: {e}")
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면] ---
st.title("🤖 제미나이 키워드 분석기")

if 'trends' not in st.session_state: st.session_state['trends'] = []

c1, c2 = st.columns([1, 2])
with c1:
    cat = st.selectbox("카테고리", ["국내여행", "해외여행", "초등학생"])
    if st.button("✨ 트렌드 확인"):
        res = ask_gemini(f"육아 블로거용 {cat} 인기 키워드 5개")
        if res:
            st.session_state['trends'] = res
            st.rerun()
    for t in st.session_state['trends']:
        st.markdown(f'<span class="keyword-badge"># {t}</span>', unsafe_allow_html=True)

with c2:
    target = st.text_input("메인 키워드", placeholder="예: 아이랑 중국여행")
    if st.button("🚀 블루오션 분석 시작"):
        if target:
            kws = ask_gemini(f"'{target}' 관련 네이버 세부 키워드 10개")
            if kws:
                df = analyze_keywords(kws)
                if not df.empty:
                    st.success("분석 완료!")
                    st.dataframe(df.sort_values('블루오션지수', ascending=False))
                else:
                    st.error("분석 결과가 없습니다. 에러 메시지를 확인하세요.")
