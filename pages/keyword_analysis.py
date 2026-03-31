import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai
import re

# --- [1. 설정 및 스타일] ---
st.set_page_config(page_title="제미나이 키워드 비기", layout="wide")
st.markdown("""
<style>
    .keyword-badge { display: inline-block; background-color: #f0f7ff; color: #007bff; padding: 4px 12px; border-radius: 12px; font-size: 14px !important; margin: 4px; border: 1px solid #cce5ff; }
</style>
""", unsafe_allow_html=True)

# --- [2. API 설정] ---
try:
    cust_id = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    ad_key = str(st.secrets["AD_API_KEY"]).strip()
    ad_secret = str(st.secrets["AD_SECRET_KEY"]).strip()
    s_id = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    s_secret = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0]
    model = genai.GenerativeModel(target_model)
except Exception as e:
    st.error(f"❌ 설정 로드 실패: {e}")
    st.stop()

# --- [3. 핵심 함수] ---
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
        full_prompt = f"{prompt}. 반드시 다른 설명이나 영어 없이 '키워드1, 키워드2, 키워드3' 형식으로 단어만 출력해."
        response = model.generate_content(full_prompt)
        if response and response.text:
            raw_text = response.text.strip()
            kws = [k.strip() for k in raw_text.split(',') if k.strip()]
            return [k for k in kws if re.search('[가-힣]', k)][:15]
        return []
    except: return []

def analyze_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    status_text = st.empty()
    
    child_words = ['아이', '가족', '초등학생', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']
    
    for idx, kw in enumerate(keyword_list):
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        if not clean_kw: continue
        
        status_text.text(f"📊 분석 중 ({idx+1}/{len(keyword_list)}): {clean_kw}")
        hint_param = clean_kw.replace(" ", ",")
        
        try:
            resp = requests.get(BASE_URL + uri, params={'hintKeywords': hint_param, 'showDetail': '1'}, headers=get_header('GET', uri), timeout=10)
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    def p(v): return v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    
                    is_child = any(cw in clean_kw for cw in child_words)
                    raw_index = (vol / (blog if blog > 0 else 1) * 100) * (1.3 if is_child else 1.0)
                    index = round(raw_index, 2)
                    
                    results.append({
                        '키워드': clean_kw, '총검색량': vol, '블로그수': blog, 
                        '블루오션지수': index, '상태': '👍 블루' if index >= 1.0 else '👎 레드', '추천': '👶' if is_child else ''
                    })
            time.sleep(0.4)
        except: continue
    status_text.empty()
    return pd.DataFrame(results)

# --- [4. 메인 화면] ---
st.title("🤖 제미나이 x 네이버 키워드 비기")

if 'trends' not in st.session_state: st.session_state['trends'] = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("💡 주제별 트렌드 추천")
    # 🔥 [수정] Selectbox 대신 Text Input으로 변경
    custom_cat = st.text_input("추천받고 싶은 주제를 입력하세요", placeholder="예: 아이랑 갈만한 식당, 캠핑, 광주 맛집 등")
    
    if st.button("✨ 추천 키워드 추출"):
        if custom_cat:
            with st.spinner("제미나이가 고민 중..."):
                # 야구/영화 관련 단어가 포함되면 일반용, 아니면 육아용으로 프롬프트 자동 조절
                if any(x in custom_cat for x in ["야구", "기아", "타이거즈", "영화", "KBO"]):
                    prompt = f"네이버 검색량이 많은 핫한 {custom_cat} 관련 인기 키워드 5개"
                else:
                    prompt = f"육아 블로거가 포스팅하기 좋은 {custom_cat} 관련 인기 키워드 5개"
                    
                res = ask_gemini(prompt)
                if res:
                    st.session_state['trends'] = res
                    st.rerun()
        else:
            st.warning("주제를 입력해 주세요!")
            
    for t in st.session_state['trends']:
        if len(t) < 20: 
            st.markdown(f'<span class="keyword-badge"># {t}</span>', unsafe_allow_html=True)

with col2:
    st.subheader("🚀 블루오션 지수 분석")
    target = st.text_input("정밀 분석할 메인 키워드 입력", placeholder="위의 추천 키워드 중 하나를 복사해서 넣어보세요!")
    if st.button("분석 시작"):
        if target:
            with st.spinner("네이버 데이터 분석 중..."):
                if any(x in target for x in ["야구", "기아", "타이거즈", "영화"]):
                    prompt = f"'{target}' 관련 네이버 검색량이 많은 세부 키워드 15개"
                else:
                    prompt = f"'{target}' 관련 육아 블로거용 세부 키워드 15개"
                    
                kws = ask_gemini(prompt)
                df = analyze_keywords(kws)
                if not df.empty:
                    st.success("분석 완료!")
                    df = df.sort_values('블루오션지수', ascending=False).reset_index(drop=True)
                    df.index = df.index + 1
                    
                    def style_status(val):
                        color = '#1f77b4' if '👍' in val else '#d62728'
                        return f'color: {color}; font-weight: bold;'

                    st.dataframe(df.style.applymap(style_status, subset=['상태']), use_container_width=True)
                    st.balloons()
