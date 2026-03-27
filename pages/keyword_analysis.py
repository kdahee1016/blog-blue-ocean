import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd
import google.generativeai as genai

# --- [1. API 설정 및 보안 값 로드] ---
try:
    # 모든 설정값을 문자열(str)로 강제 변환하여 공백을 제거합니다.
    AD_CUSTOMER_ID = str(st.secrets["AD_CUSTOMER_ID"]).strip()
    AD_API_KEY = str(st.secrets["AD_API_KEY"]).strip()
    AD_SECRET_KEY = str(st.secrets["AD_SECRET_KEY"]).strip()
    SEARCH_CLIENT_ID = str(st.secrets["SEARCH_CLIENT_ID"]).strip()
    SEARCH_CLIENT_SECRET = str(st.secrets["SEARCH_CLIENT_SECRET"]).strip()

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ 설정 로드 오류: {e}")
    st.stop()

# --- [2. 네이버 광고 API 전용 헤더 생성 함수] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    # 네이버 공식 가이드: {timestamp}.{method}.{uri}
    message = timestamp + "." + method + "." + uri
    
    hash = hmac.new(AD_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(hash.digest()).decode('utf-8')
    
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': AD_API_KEY,
        'X-Customer': AD_CUSTOMER_ID,
        'X-Signature': signature
    }

# --- [3. 블로그 수 조회 함수 (네이버 검색 API)] ---
def get_blog_count(keyword):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": SEARCH_CLIENT_ID,
        "X-Naver-Client-Secret": SEARCH_CLIENT_SECRET
    }
    params = {"query": keyword, "display": 1}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        return res.json().get('total', 0) if res.status_code == 200 else 0
    except: return 0

# --- [4. 데이터 분석 함수: 400 에러 방지용] ---
def analyze_gemini_keywords(keyword_list):
    # 중요: URI는 반드시 /로 시작해야 하며 파라미터가 포함되지 않아야 합니다.
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool' 
    results = []
    
    status_text = st.empty()
    target_list = keyword_list[:15] # 테스트를 위해 15개로 제한
    
    for idx, kw in enumerate(target_list):
        clean_kw = kw.strip().replace("#", "")
        status_text.text(f"📊 분석 중 ({idx+1}/{len(target_list)}): {clean_kw}")
        
        # 네이버 광고 API 파라미터 설정
        params = {
            'hintKeywords': clean_kw,
            'showDetail': '1'
        }
        
        try:
            # 헤더 생성 시 uri(/keywordstool)를 정확히 전달해야 합니다.
            headers = get_header('GET', uri)
            resp = requests.get(BASE_URL + uri, params=params, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    item = data[0]
                    # '연관 키워드'가 아닌 '정확히 내가 입력한 키워드'를 찾기 위해 필터링하거나 첫 번째 값 사용
                    p = lambda v: v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    blog = get_blog_count(clean_kw)
                    
                    if blog > 0:
                        # 👶 육아 가중치 (아이, 가족, 체험, 역사 단어 포함 시 1.8배)
                        bonus = 1.8 if any(w in clean_kw for w in ['아이', '가족', '초등학생', '체험', '교육', '박물관', '미술', '과학', '갈만한', '볼만한']) else 1.0
                        index = round((vol / blog * 100) * bonus, 2)
                        results.append({
                            '키워드': clean_kw, '총검색량': vol, '블로그수': blog, 
                            '블루오션지수': index, '추천': '👶' if bonus > 1.0 else ''
                        })
            else:
                # ⚠️ 400 에러 발생 시 원인 파악을 위해 상세 메시지 출력
                st.warning(f"⚠️ '{clean_kw}' 요청 실패 (코드: {resp.status_code})")
                st.write(f"상세 메시지: {resp.text}") # 네이버가 왜 거절했는지 이유가 나옵니다.
                
            time.sleep(0.3)
        except Exception as e:
            st.error(f"알 수 없는 에러: {e}")
            continue
            
    status_text.empty()
    return pd.DataFrame(results)

# --- [이후 메인 화면 로직은 이전과 동일] ---
# ... (생략) ...
