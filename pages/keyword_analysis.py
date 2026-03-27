import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd

# --- [비밀 키 불러오기] ---
AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
AD_API_KEY = st.secrets["AD_API_KEY"]
AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]

# 1. 검색광고 API 인증 시그니처 생성 함수
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

# 2. 네이버 검색 API를 이용한 블로그 발행수 조회 함수
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

# 3. 메인 분석 함수
def analyze_keywords(hint_keyword):
    uri = '/keywordstool'
    method = 'GET'
    # 연관검색어 최대 5개 추출 설정 (showDetail=1로 상세 수치 포함)
    params = {'hintKeywords': hint_keyword, 'showDetail': '1'}
    
    response = requests.get(BASE_URL + uri, params=params, headers=get_header(method, uri))
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    data = response.json()['keywordList']
    
    # 상위 5개(검색어 본인 포함 6개)만 슬라이싱
    top_keywords = data[:6]
    
    results = []
    for item in top_keywords:
        kw = item['relKeyword']
        
        # 검색량 수치 처리 (10 미만은 < 10으로 오기 때문에 숫자로 변환)
        pc_vol = item['monthlyPcQcCnt']
        mo_vol = item['monthlyMobileQcCnt']
        pc_vol = int(pc_vol) if isinstance(pc_vol, int) else 5
        mo_vol = int(mo_vol) if isinstance(mo_vol, int) else 5
        
        total_vol = pc_vol + mo_vol
        blog_count = get_blog_count(kw)
        
        # 블루오션 지수 (발행량 대비 검색량) - 숫자가 높을수록 좋음
        index = round(total_vol / blog_count, 4) if blog_count > 0 else total_vol
        
        results.append({
            '키워드': kw,
            'PC검색량': pc_vol,
            '모바일검색량': mo_vol,
            '총검색량': total_vol,
            '블로그발행수': blog_count,
            '경쟁지수(index)': index,
            '경쟁정도': item['compIdx'] # PC 기준 경쟁정도
        })
        # API 과부하 방지를 위한 미세한 지연
        time.sleep(0.1)
        
    return pd.DataFrame(results)

st.title("🔍 네이버 블로그 키워드 분석기")

category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "육아", "초등학생", "스포츠(야구)", "도서", "영화"])
hint_kw = st.text_input("분석할 키워드를 입력하세요", value=category)

if st.button("데이터 분석 시작"):
    with st.spinner('네이버 데이터를 수집 중입니다...'):
        # 여기에 분석 함수 호출 로직 추가
        # df = analyze_keywords(hint_kw)
        # st.dataframe(df)
        st.success("분석 완료!")
