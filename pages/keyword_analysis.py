import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd

# --- [1. Secrets에서 API 키 불러오기] ---
try:
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
except KeyError:
    st.error("Streamlit Secrets에 API 키가 설정되지 않았습니다. 설정을 확인해주세요.")
    st.stop()

# --- [2. 네이버 검색광고 API 인증 헤더 생성 함수] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    message = "{}.{}.{}".format(timestamp, method, uri)
    hash = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(hash.digest()).decode('utf-8')
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': AD_API_KEY,
        'X-Customer': AD_CUSTOMER_ID,
        'X-Signature': signature
    }

# --- [3. 네이버 검색 API로 블로그 발행수 조회] ---
def get_blog_count(keyword):
    url = f"https://openapi.naver.com/v1/search/blog.json?query={keyword}&display=1"
    headers = {
        "X-Naver-Client-Id": SEARCH_CLIENT_ID,
        "X-Naver-Client-Secret": SEARCH_CLIENT_SECRET
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get('total', 0)
    except:
        return 0
    return 0

# --- [4. 키워드 데이터 수집 및 분석 함수] ---
def analyze_keywords(hint_keyword):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    method = 'GET'
    params = {'hintKeywords': hint_keyword, 'showDetail': '1'}
    
    response = requests.get(BASE_URL + uri, params=params, headers=get_header(method, uri))
    
    if response.status_code != 200:
        st.error(f"API 호출 실패 (코드: {response.status_code})")
        return None

    data = response.json().get('keywordList', [])
    top_keywords = data[:10] # 상위 10개 키워드 분석
    
    results = []
    progress_bar = st.progress(0)
    
    for i, item in enumerate(top_keywords):
        kw = item['relKeyword']
        # 수치 변환 (< 10 등으로 오는 데이터 처리)
        def parse_val(val):
            if isinstance(val, int): return val
            if isinstance(val, str) and '<' in val: return 5
            return 0

        pc_vol = parse_val(item['monthlyPcQcCnt'])
        mo_vol = parse_val(item['monthlyMobileQcCnt'])
        total_vol = pc_vol + mo_vol
        blog_count = get_blog_count(kw)
        
        # 블루오션 지수 (높을수록 좋음)
        index = round(total_vol / blog_count * 100, 2) if blog_count > 0 else total_vol
        
        results.append({
            '키워드': kw,
            '총검색량': total_vol,
            '블로그수': blog_count,
            '블루오션지수': index,
            '경쟁정도': item['compIdx']
        })
        progress_bar.progress((i + 1) / len(top_keywords))
        time.sleep(0.1)
        
    return pd.DataFrame(results)

# --- [5. 스트림릿 화면 구성] ---
st.title("🔍 네이버 블로그 키워드 분석기")
st.info("카테고리를 고르고 키워드를 입력하면 검색량 대비 발행량이 적은 키워드를 찾아드립니다.")

category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "육아", "초등학생", "스포츠(야구)", "도서", "영화"])
hint_kw = st.text_input("분석할 대표 키워드를 입력하세요", value=category)

if st.button("데이터 분석 시작"):
    with st.spinner(f"'{hint_kw}' 관련 데이터를 분석 중입니다..."):
        df = analyze_keywords(hint_kw)
        
        if df is not None and not df.empty:
            st.success("데이터 분석 완료!")
            # 지수 높은 순으로 정렬해서 보여주기
            df = df.sort_values(by='블루오션지수', ascending=False)
            st.dataframe(df, use_container_width=True)
            
            st.balloons() # 축하 풍선!
        else:
            st.warning("결과가 없습니다. 키워드를 바꿔보세요.")
