import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
from datetime import datetime

# --- [1. API 설정 및 기본 함수] ---
try:
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
except:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

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

# --- [2. 실시간 자동완성 및 분석 로직] ---
def get_naver_autocomplete(keyword):
    url = f"https://ac.search.naver.com/nx/ac?q={keyword}&con=0&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_k_ticket=0&p_type=mm&ac_q_f_e=1"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return [item[0] for item in res.json()['items'][0][:7]]
    except: return []
    return []

def analyze_keywords(hint_keyword):
    clean_keyword = hint_keyword.replace(" ", "").split(',')[0]
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    params = {'hintKeywords': clean_keyword, 'showDetail': '1', 'biztpId': '15'}
    response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
    
    if response.status_code != 200: return None

    data = response.json().get('keywordList', [])
    results = []
    exclude_words = ['아기띠', '아띠', '힙시트', '카시트', '유모차', '기저귀', '분유', '스쿠버', '어에']
    child_place_words = ['아이', '초등학생', '아들', '자녀', '가족', '키즈', '체험', '박물관', '공원', '랜드', '목장', '카페', '펜션', '숙소', '갈만한', '볼만한']

    for i, item in enumerate(data[:150]):
        kw = item['relKeyword']
        if any(word in kw for word in exclude_words): continue
        def parse_val(val):
            if isinstance(val, int): return val
            if isinstance(val, str) and '<' in val: return 5
            return 0
        total_vol = parse_val(item['monthlyPcQcCnt']) + parse_val(item['monthlyMobileQcCnt'])
        if not (500 <= total_vol <= 3000): continue # 500~3,000 황금구간
        blog_count = get_blog_count(kw)
        if blog_count == 0: continue
        bonus = 1.8 if any(word in kw for word in child_place_words) else 1.0
        index = round((total_vol / blog_count * 100) * bonus, 2)
        results.append({'키워드': kw, '총검색량': total_vol, '블로그수': blog_count, '블루오션지수': index, '경쟁정도': item['compIdx']})
        if len(results) >= 15: break
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by='블루오션지수', ascending=False).reset_index(drop=True)
        df.index = df.index + 1
    return df

# --- [3. 화면 레이아웃] ---
st.set_page_config(page_title="육아 블로거 키워드 비기", layout="wide")
st.title("🔍 네이버 블로그 키워드 분석기")

# 세션 상태 초기화 (처음 한 번만 실행)
if 'auto_list' not in st.session_state:
    st.session_state['auto_list'] = []
if 'current_kw' not in st.session_state:
    st.session_state['current_kw'] = "제주도 아이랑"

col1, col2 = st.columns([1, 3])

with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "육아", "스포츠", "도서"])
    
    # 🔄 버튼 클릭 시 바로 리스트를 업데이트하고 화면을 강제로 다시 그립니다.
    if st.button(f"🔄 {category} 트렌드 확인"):
        with st.spinner("데이터 수집 중..."):
            new_list = get_naver_autocomplete(category)
            if new_list:
                st.session_state['auto_list'] = new_list
                st.rerun() # ⭐ 핵심: 화면을 즉시 새로고침해서 리스트를 보여줌
            else:
                st.warning("트렌드 데이터를 가져오지 못했습니다.")

    st.divider()
    
    # 리스트가 있을 때만 서브헤더와 버튼 표시
    if st.session_state['auto_list']:
        st.subheader(f"✨ {category} 인기어")
        for idx, ak in enumerate(st.session_state['auto_list']):
            # 각 버튼에 고유한 키(key)를 부여하여 충돌 방지
            if st.button(f"# {ak}", key=f"auto_btn_{idx}_{ak}"):
                st.session_state['current_kw'] = ak
                # 분석을 시작하도록 트리거 설정 후 새로고침
                st.session_state['trigger_analysis'] = True
                st.rerun()

with col2:
    # 세션 상태에 저장된 키워드를 입력창에 표시
    hint_kw = st.text_input("분석할 키워드", value=st.session_state['current_kw'])
    
    # 분석 실행 조건: 버튼 클릭 OR 자동완성 키워드 클릭
    run_analysis = st.button("🚀 데이터 분석 시작")
    
    if run_analysis or st.session_state.get('trigger_analysis', False):
        # 트리거 초기화
        if 'trigger_analysis' in st.session_state:
            del st.session_state['trigger_analysis']
            
        with st.spinner(f"'{hint_kw}' 꿀 키워드 발굴 중..."):
            df = analyze_keywords(hint_kw)
            if df is not None and not df.empty:
                st.success(f"'{hint_kw}' 분석 완료!")
                st.dataframe(df, use_container_width=True)
                st.balloons()
            else:
                st.warning("500~3,000 구간의 키워드가 없네요. 범위를 넓혀보세요!")
