import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import random

# 1. 페이지 설정
st.set_page_config(page_title="오키랑의 키워드 분석", layout="wide")
st.title("🍀 오키랑의 키워드 분석")

# 2. API 설정
with st.expander("🔐 네이버 API 키 입력", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        c_id = st.text_input("Client ID", type="password")
    with col2:
        c_secret = st.text_input("Client Secret", type="password")

st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("👥 타겟 설정")
target_gender = st.sidebar.selectbox("성별", ["전체", "여성 (f)", "남성 (m)"])
gender_code = "" if target_gender == "전체" else target_gender.split("(")[1][0]
target_ages = st.sidebar.multiselect("연령대", ["10", "20", "30", "40", "50", "60"], default=[])

# 4. 분석 모드
category_map = {
    "여행/문화": "50000009", "출산/육아": "50000005", "식품": "50000006",
    "스포츠/레저": "50000007", "가구/인테리어": "50000004", "생활/건강": "50000008"
}
mode = st.radio("모드 선택", ["직접 입력", "실시간 핫 키워드"])

if mode == "실시간 핫 키워드":
    selected_name = st.selectbox("카테고리 선택", list(category_map.keys()))
    selected_category_id = category_map[selected_name]
else:
    user_input = st.text_area("키워드 입력 (쉼표 구분)", "아이랑 갈만한, 주말 나들이")

# --- AI 제목 생성 함수 ---
def generate_ai_titles(keyword):
    patterns = [
        f"이번 주말에 다녀온 {keyword}, 솔직히 말해서 '이거' 하나는 좀 별로였어요",
        f"드디어 다녀온 {keyword}! 광고 말고 진짜 찐후기 궁금하신 분?",
        f"제가 직접 겪어보고 정리한 {keyword} 방문 전 필수 체크리스트 3가지",
        f"혹시 아직도 {keyword} 갈 때 준비물 없이 가시나요? (꿀팁 포함)",
        f"요즘 SNS에 난리 난 {keyword}, 직접 가보니 이유를 알겠네",
        f"주말 {keyword} 나들이, 나만 알고싶은 비밀장소였는데 공개합니다",
        f"아이랑 {keyword} 갈 때 '이 때'에 가야 줄 안 서고 들어갑니다",
        f"엄마들이 자꾸 물어보는 {keyword} 정보, 한 페이지로 끝내 드릴게요",
        f"실패 없는 {keyword}를 위한 현실적인 조언 (비용, 동선, 주차)",
        f"{keyword} 방문 예정이라면 꼭 알아야 할 내용 체크",
        f"기대 이상이었던 {keyword}, 놓치면 아쉬울 뻔한 포인트",
        f"솔직히 {keyword} 가기 전에 이 글은 꼭 보길 추천"
    ]
    return random.sample(patterns, 5)

# 5. 분석 시작
if st.button("🚀 심층 분석 및 AI 제목 생성"):
    if not c_id or not c_secret:
        st.error("API 키를 입력하세요!")
    else:
        headers = {
            "X-Naver-Client-Id": c_id, 
            "X-Naver-Client-Secret": c_secret, 
            "Content-Type": "application/json"
        }
        
        final_keywords = []
        
        if mode == "실시간 핫 키워드":
            target_date = datetime.now() - timedelta(days=3)
            str_date = target_date.strftime('%Y-%m-%d')
            
            # 주소 끝이 'keywords'인 것을 확인하세요! (s가 붙어야 랭킹을 가져옵니다)
            url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
            
            # 네이버 쇼핑인사이트 키워드 랭킹 API의 필수 규격입니다.
            body = {
                "startDate": str_date,
                "endDate": str_date,
                "timeUnit": "date",
                "category": selected_category_id,
                "device": "",
                "gender": gender_code,
                "ages": target_ages if target_ages else []
            }
            
            # [중요] 주소가 혹시라도 오타가 날 수 있으니 다시 한 번 변수에 담습니다.
            res = requests.post(url, headers=headers, data=json.dumps(body))
            
            if res.status_code == 200:
                data = res.json()
                # 쇼핑인사이트 랭킹 데이터는 ['results'][0]['data'] 구조입니다.
                if "results" in data and len(data['results']) > 0:
                    final_keywords = [item['title'] for item in data['results'][0]['data'][:20]]
                    st.success(f"✅ {str_date} 기준 실시간 키워드 20개 수집 완료!")
                else:
                    st.warning(f"⚠️ {str_date} 데이터가 아직 없습니다. 타겟을 넓혀보세요.")
            else:
                st.error(f"❌ 데이터 수집 실패 (에러: {res.status_code})")
                st.write("네이버 응답 메시지:", res.json())
        
        else:
            final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

        # 수집된 키워드로 상세 분석 진행
        if final_keywords:
            results = []
            with st.spinner("📊 시즌성 비교 및 데이터 분석 중..."):
                for kw in final_keywords:
                    # 현재 트렌드
                    s_body = {"startDate": (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'), "endDate": datetime.now().strftime('%Y-%m-%d'), "timeUnit": "month", "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}
                    res_now = requests.post("https://openapi.naver.com/v1/datalab/search", headers=headers, data=json.dumps(s_body))
                    
                    # 작년 트렌드 (시즌성)
                    last_year_start = (datetime.now() - timedelta(days=365+30)).strftime('%Y-%m-%d')
                    last_year_end = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                    s_body_last = {"startDate": last_year_start, "endDate": last_year_end, "timeUnit": "month", "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}
                    res_last = requests.post("https://openapi.naver.com/v1/datalab/search", headers=headers, data=json.dumps(s_body_last))
                    
                    # 블로그수 검색
                    res_b = requests.get(f"https://openapi.naver.com/v1/search/blog?query={kw}&display=1", headers=headers)
                    
                    if res_now.status_code == 200:
                        try: now_ratio = res_now.json()['results'][0]['data'][0]['ratio']
                        except: now_ratio = 0
                        try: last_ratio = res_last.json()['results'][0]['data'][0]['ratio']
                        except: last_ratio = 0
                        
                        growth = now_ratio - last_ratio
                        blog_count = res_b.json().get('total', 0)
                        score = (now_ratio / (blog_count + 1)) * 10000
                        
                        results.append({
                            "키워드": kw,
                            "블루오션지수": round(score, 2),
                            "전년비 성장": f"{'+' if growth > 0 else ''}{round(growth, 2)}",
                            "AI 제목 추천": generate_ai_titles(kw)[0], 
                            "상세보기": f"https://search.naver.com/search.naver?query={kw}"
                        })

            if results:
                df = pd.DataFrame(results).sort_values(by="블루오션지수", ascending=False)
                
                st.subheader("📈 키워드별 시장성 분석")
                fig = px.bar(df, x='키워드', y='블루오션지수', color='블루오션지수', color_continuous_scale='Portland', text='전년비 성장')
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📑 AI 전략 리포트")
                st.dataframe(
                    df,
                    column_config={"상세보기": st.column_config.LinkColumn("네이버 검색")},
                    use_container_width=True
                )

                st.markdown("---")
                st.subheader("✍️ 선택 키워드 AI 제목 무한 생성")
                target_kw = st.selectbox("제목을 뽑고 싶은 키워드를 선택하세요", df['키워드'].tolist())
                if st.button("🪄 새로운 제목 생성"):
                    new_titles = generate_ai_titles(target_kw)
                    for t in new_titles:
                        st.success(t)

# 6. 블로그 본문 프롬프트 생성기 (항상 표시)
st.markdown("---")
st.subheader("📝 블로그 본문 작성 프롬프트 생성기")

m_key = st.text_input("📍 메인 키워드", placeholder="메인 키워드를 입력하세요.")

col_s1, col_s2 = st.columns(2)
with col_s1:
    s_key1 = st.text_input("🔹 서브1")
    s_key2 = st.text_input("🔹 서브2")
    s_key3 = st.text_input("🔹 서브3")
with col_s2:
    s_key4 = st.text_input("🔹 서브4")
    s_key5 = st.text_input("🔹 서브5")

sub_keys = [k for k in [s_key1, s_key2, s_key3, s_key4, s_key5] if k.strip()]
sub_keys_str = ", ".join(sub_keys) if sub_keys else "(없음)"

# 프롬프트 템플릿
final_prompt = f""" - 본문에 [{m_key}] 메인 키워드를 4회 넣어주고,
 - 서브키워드 [{sub_keys_str}]은 2회씩 본문에 잘 녹아들도록 자연스럽게 넣어줘.

 - 본문 작성 시 블로그에 맞는 톤앤매너를 지켜주고
 - 말투는 30대 여자가 작성하는 ~했음, ~했다, 혼잣말 느낌 등의 편안한 일기형 말투를 섞어서 작성
 - 긴 문장이라도 한 줄에 공백포함 최대 60~70byte로 자연스럽게 끊어서 작성해줘. (블로그 모바일 화면으로 편하게 읽힐 수 있도록)
 - 본문 전체는 자연스러운 스토리텔링으로 한글 기준 약 3,500자로 맞춰줘.
 - 글 곳곳에 아래 이모티콘 중 5~6개 정도 활용해줘,
!(•̀ᴗ•́)و ̑̑ / (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ / (୨୧ ❛ᴗ❛)✧ / (୨୧ •͈ᴗ•͈) / (•̆ꈊ•̆ ) / (ꈍᴗꈍ)♡ / - ̗̀ෆ(˶'ᵕ'˶)ෆ ̖·- / ٩(*•̀ᴗ•́*)و / ٩( ᐢ-ᐢ )و / ٩(๑❛ᴗ❛๑)۶♡ / ٩(◕ᗜ◕)و / ദ്ദി( ¯꒳¯ ) / ☆٩(｡•ω<｡)و / :) / :D / >_< / +ㅂ+ 
 - 글 곳곳에 어울리는 이모지도 6~10개 활용해 줘. 
 - AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토해주고,
 - 상위노출SEO 반영해서 내용 작성해줘.
 - 본문 최상단에 넣을 요약문도 작성해 줘. (공백포함 약 240~280byte)
 (예시) 서울,인천 쪽은 이미 ㅇㅇㅇ가 유명한 지역인데
대구에 ㅇㅇㅇ 맛집이 있다는 이야기를 듣고
드디어 다녀오게 됨 :D
     
특히 아이랑 같이 먹기 좋은 메뉴라 더 관심이 갔던 곳이다.
     
​고퀄리티의 ㅇㅇㅇㅇ를 배터지게 먹고 온      
방문후기 고고쓰 (ღ•͈ᴗ•͈ღ)


*글의흐름
요약문 -> 매장정보(주소/운영시간/휴무일/매장전화번호) -> 
이후 본문은 내가 입력"""

if st.button("📋 본문작성 프롬프트 복사"):
    if not m_key:
        st.warning("⚠️ 메인키워드를 입력하세요.")
    else:
        st.text_area("아래 내용을 복사해서 사용하세요!", value=final_prompt, height=450)
        st.success("✅ 프롬프트가 생성되었습니다!")



