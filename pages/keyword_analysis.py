import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai

# --- [1. API 설정 및 기본 함수] ---
# 에러를 구체적으로 보기 위해 try-except 범위를 좁혔습니다.


# `st.info` 스타일을 타겟팅합니다.
font_css = """
<style>
/* `st.info` 스타일 타겟팅 */
div[data-testid="stInfo"] {
    padding: 0.5rem 1rem; /* 안쪽 여백 줄이기 */
    border-radius: 0.5rem; /* 모서리 둥글게 */
    font-size: 1rem !important; /* ⭐ 글씨 크기를 1rem(블로그 본문 크기)으로 줄이기 */
    font-weight: normal !important; /* ⭐ 글씨 두께를 보통으로 */
    margin-bottom: 0.5rem; /* 아래쪽 여백 */
}

/* st.info 내부 폰트 스타일 타겟팅 */
div[data-testid="stInfo"] .stMarkdown {
    font-size: 1rem !important;
}
</style>
"""


if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ secrets.toml 파일에 'GEMINI_API_KEY'가 없습니다! 확인해 주세요.")
    st.stop()

try:
    AD_CUSTOMER_ID = st.secrets["AD_CUSTOMER_ID"]
    AD_API_KEY = st.secrets["AD_API_KEY"]
    AD_SECRET_KEY = st.secrets["AD_SECRET_KEY"]
    SEARCH_CLIENT_ID = st.secrets["SEARCH_CLIENT_ID"]
    SEARCH_CLIENT_SECRET = st.secrets["SEARCH_CLIENT_SECRET"]
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 1. 현재 사용 가능한 모델 목록을 직접 불러옵니다.
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 2. 가장 성능 좋은 모델 순서대로 자동 선택 (우선순위 부여)
    target_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
    selected_model_name = None
    
    for target in target_models:
        if target in available_models:
            selected_model_name = target
            break
            
    # 3. 만약 위 모델들이 없으면 목록 중 첫 번째 모델이라도 강제로 잡습니다.
    if not selected_model_name and available_models:
        selected_model_name = available_models[0]
        
    if selected_model_name:
        model = genai.GenerativeModel(selected_model_name)
        # st.success(f"✅ 모델 연결 성공: {selected_model_name}") # 연결 확인용 (테스트 후 주석 처리)
    else:
        st.error("❌ 사용 가능한 제미나이 모델을 찾을 수 없습니다. API 키 권한을 확인해 주세요.")
        st.stop()

except Exception as e:
    st.error(f"❌ 제미나이 초기 설정 오류: {e}")
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


# --- [2. 제미나이 키워드 생성 함수 - 에러 출력 강화] ---
def ask_gemini_keywords(prompt):
    try:
        response = model.generate_content(prompt + " 답변은 다른 설명 없이 키워드만 콤마(,)로 구분해서 나열해줘.")
        if response and response.text:
            return [k.strip() for k in response.text.split(',')]
        else:
            st.warning("⚠️ 제미나이가 빈 답변을 보냈습니다.")
            return []
    except Exception as e:
        st.error(f"❌ 제미나이 호출 중 오류 발생: {e}")
        return []

# --- [3. 메인 분석 함수] ---
def analyze_gemini_keywords(keyword_list, category_name):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    child_words = ['아이', '가족', '초등학생', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']

    progress_bar = st.progress(0) # 진행도 표시용
    
    for idx, kw in enumerate(keyword_list):
        # 진행률 업데이트
        progress_bar.progress((idx + 1) / len(keyword_list))
        
        params = {'hintKeywords': kw, 'showDetail': '1', 'biztpId': '15'}
        try:
            response = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
            if response.status_code == 200:
                data = response.json().get('keywordList', [])
                if not data: continue
                
                item = data[0]
                def parse_val(val):
                    if isinstance(val, int): return val
                    if isinstance(val, str) and '<' in val: return 5
                    return 0
                    
                total_vol = parse_val(item['monthlyPcQcCnt']) + parse_val(item['monthlyMobileQcCnt'])
                blog_count = get_blog_count(kw)
                
                if blog_count > 0:
                    is_child = any(cw in kw for cw in child_words)
                    bonus = 1.8 if is_child else 1.0
                    index = round((total_vol / blog_count * 100) * bonus, 2)
                    
                    results.append({
                        '키워드': kw, 
                        '총검색량': total_vol, 
                        '블로그수': blog_count, 
                        '블루오션지수': index
                    })
            time.sleep(0.1) # API 부하 방지용 미세 지연
        except: continue
    
    progress_bar.empty() # 진행바 제거
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by='블루오션지수', ascending=False).reset_index(drop=True)
        df.index = df.index + 1
    return df

# --- [4. 화면 구성] ---
st.set_page_config(page_title="꿀키워드 뽑아내기", layout="wide")

# CSS 주입!
st.markdown(font_css, unsafe_allow_allow=True)

st.title("🤖 제미나이 x 네이버 키워드 탐색기")

# 세션 상태 초기화
if 'trend_list' not in st.session_state: st.session_state['trend_list'] = []

col1, col2 = st.columns([1, 2])

with col1:
    category = st.selectbox("카테고리 선택", ["국내여행", "해외여행", "스포츠", "야구", "도서", "영화", "초등학생"])
    
    if st.button(f"✨ {category} 핫키워드 추출"):
        with st.spinner("제미나이에게 물어보는 중..."):
            prompt = f"육아 블로거 입장에서 '{category}' 카테고리와 연계하여 포스팅하기 좋은 요즘 핫한 키워드 5개 추천해줘."
            result = ask_gemini_keywords(prompt)
            if result:
                st.session_state['trend_list'] = result
                st.rerun() # 화면 갱신

    if st.session_state['trend_list']:
        st.divider()
        st.subheader("💡 제미나이 추천")
        # CSS가 적용된 `st.info`를 사용하여 깔끔하게 표시
        for tk in st.session_state['trend_list']:
            st.info(f"# {tk}") # st.info를 그대로 사용해도 CSS가 자동으로 적용됩니다.

with col2:
    search_input = st.text_input("분석할 메인 키워드 입력 (예: 아이랑 중국여행)")
    
    if st.button("🚀 꿀키워드 50개 발굴 및 데이터 분석"):
        if not search_input:
            st.warning("키워드를 입력해 주세요!")
        else:
            with st.spinner("제미나이가 50개를 뽑고 네이버 데이터를 가져오는 중... (약 20~30초 소요)"):
                prompt = f"'{search_input}'과 관련하여 네이버 블로그에 포스팅했을 때 조회수가 잘 나올만한 세부 꿀키워드 50개를 콤마로 구분해서 알려줘. 광고성이나 쇼핑몰 이름은 제외하고 실제 정보 검색 위주로."
                gemini_suggestions = ask_gemini_keywords(prompt)
                
                if gemini_suggestions:
                    df = analyze_gemini_keywords(gemini_suggestions, category)
                    
                    if df is not None and not df.empty:
                        st.success(f"'{search_input}' 분석 완료!")
                        st.dataframe(df.head(30), use_container_width=True)
                        st.balloons()
                    else:
                        st.error("분석 결과 데이터가 없습니다. 다시 시도해 보세요.")
                else:
                    st.error("제미나이로부터 키워드를 추천받지 못했습니다.")
