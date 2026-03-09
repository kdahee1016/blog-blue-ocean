import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import random
import urllib.parse

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
        f"{keyword} 방문 예정이라면 꼭 알아야 할 내용 체크"
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
            url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
            body = {"startDate": str_date, "endDate": str_date, "timeUnit": "date", "category": selected_category_id}
            if gender_code: body["gender"] = gender_code
            if target_ages: body["ages"] = target_ages
            
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                data = res.json()
                if "results" in data:
                    final_keywords = [item['title'] for item in data['results'][0]['data'][:20]]
            else:
                st.warning("⚠️ 실시간 수집 일시 오류. 직접 입력을 이용해주세요.")
        else:
            final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

        if final_keywords:
            results = []
            with st.spinner("📊 시즌성 비교 및 데이터 분석 중..."):
                for kw in final_keywords:
                    def get_blog_total(t_kw):
                        encoded = urllib.parse.quote(t_kw)
                        b_url = f"https://openapi.naver.com/v1/search/blog?query={encoded}&display=1"
                        r = requests.get(b_url, headers=headers)
                        return r.json().get('total', 0) if r.status_code == 200 else 0

                    cnt1 = get_blog_total(kw)
                    cnt2 = get_blog_total(kw.replace(" ", ""))
                    blog_count = max(cnt1, cnt2, 1)

                    s_body = {"startDate": (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'), "endDate": datetime.now().strftime('%Y-%m-%d'), "timeUnit": "month", "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}
                    res_now = requests.post("https://openapi.naver.com/v1/datalab/search", headers=headers, data=json.dumps(s_body))
                    
                    now_ratio = 0.01
                    if res_now.status_code == 200:
                        try:
                            n_data = res_now.json()['results'][0]['data']
                            now_ratio = n_data[0]['ratio'] if n_data else 0.01
                        except: pass
                    
                    score = (now_ratio / blog_count) * 10000
                    results.append({
                        "키워드": kw,
                        "블루오션지수": round(score, 4),
                        "AI 제목 추천": generate_ai_titles(kw)[0], 
                        "상세보기": f"https://search.naver.com/search.naver?query={kw}"
                    })

            if results:
                df = pd.DataFrame(results).sort_values(by="블루오션지수", ascending=False)
                
                st.markdown("### 💡 블루오션 지수 판독 가이드")
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1: st.success("**💎 10 이상: 블루오션**\n\n무조건 쓰세요! 노출 확률 최상")
                with col_g2: st.info("**✅ 5 ~ 10: 할만한 시장**\n\n제목만 잘 지어도 유입 쏠쏠함")
                with col_g3: st.warning("**⚠️ 3 미만: 레드오션**\n\n경쟁 치열. 구체적 키워드 필요")
                
                st.markdown("---")
                
                st.subheader("📈 키워드별 시장성 분석")
                fig = px.bar(df, x='키워드', y='블루오션지수', color='블루오션지수', text='블루오션지수', color_continuous_scale='Portland')
                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📑 AI 전략 리포트")
                st.dataframe(df, column_config={"상세보기": st.column_config.LinkColumn("네이버 검색")}, use_container_width=True)

# 6. 본문 프롬프트 생성기
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

final_prompt = f""" - 본문에 [{m_key}] 메인 키워드를 4회 넣어주고,
 - 서브키워드 [{sub_keys_str}]은 2회씩 본문에 잘 녹아들도록 자연스럽게 넣어줘.
 - 30대 여자가 작성하는 ~했음, ~했다, 일기형 말투 활용.
 - 한글 기준 약 3,500자로 작성하고 이모티콘 적극 활용.
 - 상위노출 SEO 반영해서 작성해줘."""

if st.button("📋 본문작성 프롬프트 생성"):
    if not m_key:
        st.warning("⚠️ 메인키워드를 입력하세요.")
    else:
        st.text_area("아래 내용을 복사해서 사용하세요!", value=final_prompt, height=300)
        st.success("✅ 프롬프트가 생성되었습니다!")
