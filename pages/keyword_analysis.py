import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd

# --- [1. Secrets 설정 확인] ---
try:
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
except:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

# --- [2. API 관련 함수들] ---
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

def analyze_keywords(hint_keyword):
    # '제주도 아이랑' 입력 시 -> '제주도 아이랑 가볼만한곳', '제주도 키즈펜션' 등으로 자동 확장
    expanded_keywords = [
        f"{hint_keyword} 가볼만한곳",
        f"{hint_keyword} 체험",
        f"{hint_keyword} 숙소",
        f"제주도 키즈카페" # 예시
    ]
    clean_keyword = ",".join(expanded_keywords)
    
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    
    # ⭐ biztpId="15"는 '여행/숙박' 업종 코드입니다. 
    # 이걸 넣어야 '아기띠' 대신 '여행지'가 나옵니다!
    params = {
        'hintKeywords': clean_keyword, 
        'showDetail': '1',
        'biztpId': '15' 
    }
    
    response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
    
    if response.status_code != 200:
        st.error(f"API 호출 실패 (코드: {response.status_code}) - 키워드를 확인해주세요.")
        return None

    data = response.json().get('keywordList', [])
    # 본인 키워드 포함 상위 15개 분석
    results = []
    progress_bar = st.progress(0)

    # 👶 "아이랑" 관련 필수 포함 단어 리스트
    include_words = ['아이', '아기', '초등학생', '아들', '딸', '가족', '키즈', '체험', '박물관', '공원', '동물원', '자녀']
    
    # 제외하고 싶은 단어 리스트 (여기에 추가하면 절대 안 뜹니다)
    exclude_words = ['아띠', '아기띠', '힙시트', '카시트', '유모차', '기저귀', '분유', '스쿠버', '어에']
    
    for i, item in enumerate(data[:100]): # 필터링을 위해 데이터를 좀 더 넉넉히 100개 가져옵니다.
        kw = item['relKeyword']
        
        # 🚫 필터링 로직: 제외 단어가 포함되어 있으면 이번 루프는 그냥 건너뜁니다.
        if any(word in kw for word in exclude_words):
            continue

        # 2. ⭐ 유연한 필터링: 
        # 검색어(제주도 아이랑)에 들어간 핵심 단어('제주')가 있거나, 아이 관련 단어가 있으면 통과!
        target_city = hint_keyword.split()[0] if " " in hint_keyword else hint_keyword[:2]
        
        is_child_related = any(word in kw for word in include_words)
        is_location_related = target_city in kw
        
        if not (is_child_related or is_location_related):
            continue
            
        # 수치 변환 로직
        def parse_val(val):
            if isinstance(val, int): return val
            if isinstance(val, str) and '<' in val: return 5
            return 0

        total_vol = parse_val(item['monthlyPcQcCnt']) + parse_val(item['monthlyMobileQcCnt'])
        blog_count = get_blog_count(kw)
        
        # 블루오션 지수 계산
        index = round(total_vol / blog_count * 100, 2) if blog_count > 0 else total_vol
        
        results.append({
            '키워드': kw, 
            '총검색량': total_vol, 
            '블로그수': blog_count, 
            '블루오션지수': index, 
            '경쟁정도': item['compIdx']
        })
        
        # 진행 바 (최대 15개까지만 보여줄 것이므로 적절히 조절)
        if len(results) >= 15:
            break
            
        progress_bar.progress(min((i + 1) / 40, 1.0))
        time.sleep(0.05)
        
    return pd.DataFrame(results)

# --- [3. 화면 구성] ---
st.set_page_config(page_title="블루오션 키워드 분석", layout="wide")
st.title("🔍 네이버 블로그 키워드 분석기")

# 카테고리별 추천 키워드 매핑
recommend_map = {
    "국내여행": ["제주도 아이랑", "강원도 아이랑", "주말 가볼만한곳"],
    "육아": ["유아식 식단", "아기랑 실내놀이터", "초등학생 준비물"],
    "스포츠(야구)": ["기아타이거즈 일정", "잠실야구장 명당", "야구 응원가"],
    "도서": ["초등 역사책 추천", "베스트셀러 순위", "육아 서적"],
}

col1, col2 = st.columns([1, 2])

with col1:
    category = st.selectbox("카테고리 선택", list(recommend_map.keys()) + ["기타"])
    
    # 카테고리에 맞는 추천 키워드 버튼 생성
    st.write("💡 추천 키워드")
    recommends = recommend_map.get(category, ["직접 입력"])
    selected_recom = ""
    for r in recommends:
        if st.button(r):
            selected_recom = r

with col2:
    # 버튼 클릭 시 해당 키워드가 입력창에 들어가도록 설정
    hint_kw = st.text_input("분석할 대표 키워드를 입력하세요", value=selected_recom if selected_recom else category)
    
    if st.button("🚀 데이터 분석 시작"):
        with st.spinner(f"'{hint_kw}' 기반 블루오션 키워드 찾는 중..."):
            df = analyze_keywords(hint_kw)
            if df is not None and not df.empty:
                st.success("분석 완료!")
                df = df.sort_values(by='블루오션지수', ascending=False).reset_index(drop=True)
                df.index = df.index + 1
                st.dataframe(df, use_container_width=True)
                st.balloons()
