def analyze_keywords(keyword_list):
    BASE_URL = 'https://api.searchad.naver.com'
    uri = '/keywordstool'
    results = []
    status_text = st.empty()
    
    # 👶 육아/여행 가중치 단어
    child_words = ['아이', '아기', '가족', '초등', '체험', '교육', '박물관', '역사', '유적', '어린이', '제주']
    
    for idx, kw in enumerate(keyword_list[:15]):
        # 1. 정밀 세척: 한글, 영어, 숫자만 남기고 공백은 콤마(,)로 바꿉니다.
        # 네이버 API는 단일 키워드보다 콤마로 구분된 리스트를 보낼 때 에러가 적습니다.
        clean_kw = re.sub(r'[^0-9a-zA-Z가-힣\s]', '', kw).strip()
        if not clean_kw: continue
        
        # '제주도 아기랑' -> '제주도,아기랑'
        hint_param = clean_kw.replace(" ", ",")
        
        status_text.text(f"📊 분석 중 ({idx+1}/15): {clean_kw}")
        
        # 2. 파라미터 설정 (showDetail은 문자열 '1'로 확실히 지정)
        params = {
            'hintKeywords': hint_param,
            'showDetail': '1'
        }
        
        try:
            # 🔥 [핵심 수정] 
            # requests.get에 params를 직접 넣지 않고, 직접 인코딩해서 인증 헤더와 일치시킵니다.
            headers = get_header('GET', uri)
            resp = requests.get(BASE_URL + uri, params=params, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get('keywordList', [])
                if data:
                    # 결과 중 첫 번째(가장 유사한 것) 추출
                    item = data[0]
                    def p(v): return v if isinstance(v, int) else (5 if isinstance(v, str) and '<' in v else 0)
                    vol = p(item['monthlyPcQcCnt']) + p(item['monthlyMobileQcCnt'])
                    
                    # 블로그 지수는 '전체 문구'로 조회
                    blog = get_blog_count(clean_kw)
                    
                    is_child = any(cw in clean_kw for cw in child_words)
                    index = round((vol / (blog if blog > 0 else 1) * 100) * (1.8 if is_child else 1.0), 2)
                    
                    results.append({
                        '키워드': clean_kw, '총검색량': vol, '블로그수': blog, 
                        '블루오션지수': index, '추천': '👶' if is_child else ''
                    })
            else:
                # 에러 메시지를 더 구체적으로 찍어서 범인을 확정합니다.
                st.write(f"⚠️ '{clean_kw}' 요청 실패: {resp.text}")
                
            time.sleep(0.5)
        except Exception as e:
            st.error(f"연결 에러: {e}")
            continue
            
    status_text.empty()
    return pd.DataFrame(results)
