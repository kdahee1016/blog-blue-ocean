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

# --- [2. 공식 API를 활용한 트렌드 추출 (자동완성 대체)] ---
def get_official_trends(category_name):
    # 검색광고 API를 사용하여 해당 카테고리의 연관 키워드 상위 7개를 가져옵니다.
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    # 카테고리 이름에서 특수문자 제거 (예: 스포츠(야구) -> 스포츠)
    clean_cat = category_name.split('(')[0]
    params = {'hintKeywords': clean_cat, 'showDetail': '1', 'biztpId': '15'}
    
    try:
        response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
        if response.status_code == 200:
            data = response.json().get('keywordList', [])
            # 검색량 순으로 정렬되어 오므로 상위 키워드만 추출
            return [item['relKeyword'] for item in data[:7]]
    except:
        pass
    return [f"{clean_cat} 추천", f"{clean_cat} 가볼만한곳", f"아이랑 {clean_cat}"]

# --- [3. 메인 분석 함수] ---
def analyze_keywords(hint_keyword, category_name):
    clean_keyword = hint_keyword.replace(" ", "").split(',')[0]
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    params = {'hintKeywords': clean_keyword, 'showDetail': '1', 'biztpId': '15'}
    response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
    
    if response.status_code != 200: return None

    data = response.json().get('keywordList', [])
    results = []
    # 🚫 전 카테고리 공통 제외 단어
    exclude_words = ['아기띠', '아띠', '힙시트', '카시트', '유모차', '기저귀', '분유', '스쿠버', '어에']
    
    # ❌ 해외여행일 때만 추가로 제외할 단어 (국내 전용 숙박 시설)
    if category_name == "해외여행":
        exclude_words += ['펜션', '모텔', '민박', '글램핑', '캠핑장', '풀빌라']

    # 👶 아이랑 관련 장소 (카테고리별 맞춤형)
    if category_name == "해외여행":
        # 해외여행은 '박물관', '미술관', '디즈니', '투어' 등이 더 중요함
        child_place_words = ['아이', '가족', '어린이', '초등학생', '키즈', '체험', '박물관', '미술관', '동물원', '수족관', '테마파크', '투어', '현지투어', '갈만한', '볼만한']
    else:
        child_place_words = ['아이', '어린이', '초등학생', '아들', '자녀', '가족', '키즈', '체험', '박물관', '공원', '랜드', '목장', '카페', '펜션', '숙소', '갈만한', '볼만한']


    for i, item in enumerate(data[:150]):
        kw = item['relKeyword']
        
        # 1. 제외 단어 필터링 (이제 펜션, 모텔이 해외여행에서 걸러집니다)
        if any(word in kw for word in exclude_words):
            continue
        
        def parse_val(val):
            if isinstance(val, int): return val
            if isinstance(val, str) and '<' in val: return 5
            return 0
            
        total_vol = parse_val(item['monthlyPcQcCnt']) + parse_val(item['monthlyMobileQcCnt'])
        
        # 500 ~ 3,000 황금 구간 필터
        if not (500 <= total_vol <= 3000): continue
        
        blog_count = get_blog_count(kw)
        if blog_count == 0: continue
        
        # 아이랑 관련 가중치 1.8배
        bonus = 1.8 if any(word in kw for word in child_place_words) else 1.0
        index = round((total_vol / blog_count * 100) * bonus, 2)
        
        results.append({'키워드': kw, '총검색량': total_vol, '블로그수': blog_count, '블루오션지수': index})
        if len(results) >= 15: break
        time.sleep(0.05)
    
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
            df = analyze_keywords(hint_kw)
            if df is not None and not df.empty:
                st.success(f"'{hint_kw}' 분석 완료!")
                st.dataframe(df, use_container_width=True)
                st.balloons()
            else:
                st.warning("500~3,000 구간의 키워드가 없네요. 다른 키워드를 눌러보세요!")
