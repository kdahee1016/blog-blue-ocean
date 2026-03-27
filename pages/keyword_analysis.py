import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd

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

# --- [2. 트렌드 추출 (왼쪽 버튼)] ---
def analyze_keywords(hint_keyword, category_name):
    clean_keyword = hint_keyword.replace(" ", "").split(',')[0]
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    params = {'hintKeywords': clean_keyword, 'showDetail': '1', 'biztpId': '15'}
    response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
    
    if response.status_code != 200: return None

    data = response.json().get('keywordList', [])
    results = []
    
    # 🚫 공통 제외 단어
    base_exclude = [
        '아기띠', '힙시트', '카시트', '유모차', '기저귀', '분유', '어에',
        '14k', '18k', '24k', '순금', '금시세', '금값', '커플링',
        '쇼핑몰', '드레스룸', '캐리어', '중고', '장터', '판매', '구매', '매입', '렌탈', '최저가', '할인쿠폰',
        '20대', '30대', '40대', '여성', '남성'
    ]
    
    if category_name == "해외여행":
        # '풀빌라' 허용을 위해 제외 목록에서 제외
        exclude_words = base_exclude + ['펜션', '모텔', '민박', '글램핑', '캠핑장', '스테이', '파티룸', '국내', '제주도', '강원도']
        min_vol, max_vol = 500, 10000
        child_words = ['아이', '가족', '어린이', '초등학생', '키즈', '체험', '박물관', '미술관', '동물원', '수족관', '테마파크', '투어', '현지투어', '갈만한', '볼만한', '디즈니', '유니버설']
    
    elif category_name == "초등학생":
        # 초등학생은 금 관련 시세만 막고 단어 자체는 허용(선물용)
        exclude_words = base_exclude + ['금시세', '금값', '14k', '18k', '24k']
        min_vol, max_vol = 500, 3000
        child_words = ['아이', '체험', '교육', '학습', '박물관', '도서', '전시', '과학', '미술', '갈만한', '볼만한', '놀이터']
    
    else:
        exclude_words = base_exclude
        min_vol, max_vol = 500, 3000
        child_words = ['아이', '초등학생', '아들', '자녀', '가족', '키즈', '체험', '박물관', '공원', '랜드', '목장', '카페', '펜션', '숙소', '갈만한', '볼만한']

    for item in data:
        kw = item['relKeyword']
        
        # 1. 제외 단어 필터 (기존 로직)
        if any(word in kw for word in exclude_words):
            continue
            
        # 2. ⭐ [추가] 여행 키워드 필수 포함 로직 (여행 카테고리일 때만 작동)
        # 이 단어들이 하나도 안 들어있으면 '여행'과 무관한 쇼핑몰로 간주하고 버립니다.
        if category_name in ["해외여행", "국내여행"]:
            must_include = ['여행', '투어', '숙소', '호텔', '리조트', '갈만한', '볼만한', '아이랑', '비행기', '항공', '입국', '명소']
            if not any(word in kw for word in must_include):
                continue

        def parse_val(val):
            if isinstance(val, int): return val
            if isinstance(val, str) and '<' in val: return 5
            return 0
            
        total_vol = parse_val(item['monthlyPcQcCnt']) + parse_val(item['monthlyMobileQcCnt'])
        if not (min_vol <= total_vol <= max_vol):
            continue
        
        blog_count = get_blog_count(kw)
        if blog_count == 0: continue
        
        is_child_related = any(word in kw for word in child_words)
        bonus = 1.8 if is_child_related else 1.0
        index = round((total_vol / blog_count * 100) * bonus, 2)
        
        results.append({
            '키워드': kw, 
            '총검색량': total_vol, 
            '블로그수': blog_count, 
            '블루오션지수': index
        })
        
        if len(results) >= 15:
            break
            
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by='블루오션지수', ascending=False).reset_index(drop=True)
        df.index = df.index + 1
    return df
    
# --- [4. 화면 구성] ---
st.set_page_config(page_title="육아 블로거 키워드 비기", layout="wide")
st.title("🔍 네이버 블로그 키워드 분석기")

if 'current_kw' not in st.session_state: st.session_state['current_kw'] = ""
if 'trend_list' not in st.session_state: st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 3])

with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "스포츠", "야구", "도서", "영화", "초등학생"])
    
    if st.button(f"🔄 {category} 트렌드 확인"):
        with st.spinner("공식 API 데이터 수집 중..."):
            st.session_state['trend_list'] = get_official_trends(category)
            st.rerun()

    st.divider()
    if st.session_state['trend_list']:
        st.subheader("✨ 연관 추천 키워드")
        for idx, tk in enumerate(st.session_state['trend_list']):
            if st.button(f"# {tk}", key=f"trend_{idx}"):
                st.session_state['current_kw'] = tk
                st.session_state['do_analyze'] = True
                st.rerun()

with col2:
    hint_kw = st.text_input("분석 키워드 입력", value=st.session_state['current_kw'])
    
    if st.button("🚀 데이터 분석 시작") or st.session_state.get('do_analyze', False):
        if 'do_analyze' in st.session_state: del st.session_state['do_analyze']
        
        with st.spinner(f"'{hint_kw}' 꿀 키워드 발굴 중..."):
            df = analyze_keywords(hint_kw, category) 
            if df is not None and not df.empty:
                st.success(f"'{hint_kw}' 분석 완료!")
                st.dataframe(df, use_container_width=True)
                st.balloons()
            else:
                st.warning("조건에 맞는 키워드가 없네요. 다른 키워드를 눌러보세요!")
