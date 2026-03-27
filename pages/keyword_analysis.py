import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
from datetime import datetime

# --- [1. API 설정] ---
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

def get_naver_autocomplete(keyword):
    # 네이버 자동완성 API (비공식적이지만 인증 없이 사용 가능)
    url = f"https://ac.search.naver.com/nx/ac?q={keyword}&con=0&frm=nv&ans=2&r_format=json&r_enc=UTF-8&r_unicode=0&t_k_ticket=0&p_type=mm&ac_q_f_e=1"
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            # 자동완성 결과에서 키워드만 쏙 뽑아오기
            items = data['items'][0]
            # 상위 5~7개만 리스트로 반환
            return [item[0] for item in items[:7]]
    except:
        pass
    return []

# --- [2. 핵심 분석 로직] ---
def analyze_keywords(hint_keyword):
    # 400 에러 방지: 쉼표 기준으로 딱 1개만 확실하게 보냅니다.
    clean_keyword = hint_keyword.replace(" ", "").split(',')[0]
    
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    # biztpId='15' (여행/숙박) 고정
    params = {'hintKeywords': clean_keyword, 'showDetail': '1', 'biztpId': '15'}
    
    response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
    
    if response.status_code != 200:
        st.error(f"API 호출 실패 (코드: {response.status_code}) - '{clean_keyword}' 키워드 형식을 확인해주세요.")
        return None

    data = response.json().get('keywordList', [])
    results = []
    
    exclude_words = ['아기띠', '아띠', '힙시트', '카시트', '유모차', '기저귀', '분유', '스쿠버', '어에']
    child_place_words = ['아이', '아기', '애랑', '자녀', '가족', '키즈', '체험', '박물관', '공원', '랜드', '목장', '카페', '펜션', '숙소', '정원', '숲길']

    progress_bar = st.progress(0)
    found_count = 0

    for i, item in enumerate(data[:150]): # 더 많이 훑습니다.
        kw = item['relKeyword']
        if any(word in kw for word in exclude_words): continue
            
        def parse_val(val):
            if isinstance(val, int): return val
            if isinstance(val, str) and '<' in val: return 5
            return 0

        total_vol = parse_val(item['monthlyPcQcCnt']) + parse_val(item['monthlyMobileQcCnt'])
        
        # ⭐ 요청하신 검색량 필터 (500~3,000 구간)
        if not (500 <= total_vol <= 3000): continue

        blog_count = get_blog_count(kw)
        if blog_count == 0: continue
        
        # 지수 계산 및 아이 관련 가점
        bonus = 1.8 if any(word in kw for word in child_place_words) else 1.0
        index = round((total_vol / blog_count * 100) * bonus, 2)
        
        results.append({'키워드': kw, '총검색량': total_vol, '블로그수': blog_count, '블루오션지수': index, '경쟁정도': item['compIdx']})
        found_count += 1
        
        progress_bar.progress(min(found_count / 15, 1.0))
        if found_count >= 15: break
        time.sleep(0.05)
        
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by='블루오션지수', ascending=False).reset_index(drop=True)
        df.index = df.index + 1
    return df

# --- [3. 화면 레이아웃] ---
st.set_page_config(page_title="육아 블로거 키워드 비기", layout="wide")
st.title("🔍 네이버 블로그 키워드 분석기")

# 핫 키워드 데이터 (3월 말 기준 수동 업데이트 - 추후 자동화 가능)
hot_keywords = ["제주도 유채꽃", "딸기체험 농장", "서울근교 피크닉", "아이랑 벚꽃", "키즈펜션 추천"]

col1, col2 = st.columns([1, 3])

with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "육아", "스포츠", "도서"])
    
    # ⭐ 클릭하면 해당 카테고리로 실시간 자동완성어를 긁어옵니다
    if st.button(f"🔄 {category} 실시간 트렌드 확인"):
        with st.spinner("네이버 실시간 데이터 수집 중..."):
            # 카테고리명을 키워드로 해서 자동완성어를 가져옴
            # 예: '국내여행' -> '국내여행지 베스트 10', '국내여행 추천' 등
            realtime_kws = get_naver_autocomplete(category)
            st.session_state['auto_kws'] = realtime_kws

    st.divider()
    
    # 긁어온 키워드를 버튼으로 뿌려주기
    if 'auto_kws' in st.session_state and st.session_state['auto_kws']:
        st.subheader(f"✨ 지금 뜨는 {category}")
        for ak in st.session_state['auto_kws']:
            if st.button(f"# {ak}"):
                st.session_state['selected_kw'] = ak

with col2:
    hint_kw = st.text_input("분석할 키워드를 입력하세요 (예: 제주도 아이랑)", value=selected_hot if selected_hot else "제주도 아이랑")
    
    if st.button("🚀 데이터 분석 시작"):
        with st.spinner("알짜 키워드를 발굴 중입니다..."):
            df = analyze_keywords(hint_kw)
            if df is not None and not df.empty:
                st.success(f"'{hint_kw}' 관련 500~3,000 검색량 구간 블루오션 결과입니다!")
                st.dataframe(df, use_container_width=True)
                st.balloons()
            else:
                st.warning("조건에 맞는 블루오션 키워드를 찾지 못했습니다. 키워드를 조금 더 넓게 입력해보세요!")
