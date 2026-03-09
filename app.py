import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import io
import plotly.express as px  # 그래프를 위해 추가

# 페이지 설정
st.set_page_config(page_title="오키랑의 블루오션 키워드 분석기", layout="wide")
st.title("🌊 오키랑의 블루오션 키워드 분석기")

# 2. API 설정창을 메인 화면 최상단에 배치 (접었다 폈다 할 수 있게!)
with st.expander("🔐 네이버 API 키 입력 (먼저 입력해주세요)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        c_id = st.text_input("Client ID", type="password")
    with col2:
        c_secret = st.text_input("Client Secret", type="password")

st.markdown("---")

# 3. 그 아래에 키워드 입력창 배치
st.subheader("🔍 분석할 키워드 입력")
user_input = st.text_area(
    "키워드를 쉼표(,)로 구분해서 입력하세요", 
    value="원하는, 키워드를, 입력하세요"
)

# 블루오션 지수에 따른 색상 적용 함수
def highlight_score(val):
    if val <= 3:
        return 'color: red; font-weight: bold'
    elif 3 < val <= 5:
        return 'color: red'
    elif 5 < val <= 8:
        return 'color: blue'
    elif 8 < val <= 10:
        return 'color: blue; font-weight: bold'
    else:
        return 'color: green; font-weight: bold' # 10 초과는 초록 볼드!

if start_btn:
    if not c_id or not c_secret:
        st.error("API 키를 입력해주세요!")
    else:
        # 빈칸 제거 로직 적용
        keywords = [k.strip() for k in user_input.split(",") if k.strip()]
        results_list = []
        
        headers = {"X-Naver-Client-Id": c_id, "X-Naver-Client-Secret": c_secret, "Content-Type": "application/json"}
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        with st.spinner('데이터 분석 중...'):
            for kw in keywords:
                # 데이터랩 요청
                res_t = requests.post("https://openapi.naver.com/v1/datalab/search", 
                                    headers=headers, 
                                    data=json.dumps({"startDate": start_date, "endDate": end_date, "timeUnit": "month",
                                                     "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}))
                # 블로그수 요청
                res_b = requests.get(f"https://openapi.naver.com/v1/search/blog?query={kw}&display=1", headers=headers)
                
                if res_t.status_code == 200 and res_b.status_code == 200:
                    try:
                        ratio = res_t.json()['results'][0]['data'][0]['ratio']
                    except: ratio = 0
                    blog_count = res_b.json().get('total', 0)
                    
                    # 지수 계산 (조정된 공식)
                    score = (ratio / (blog_count + 1)) * 10000
                    
                    results_list.append({
                        "키워드": kw,
                        "검색 트렌드(점수)": round(ratio, 2),
                        "블로그 발행량": blog_count,
                        "블루오션 지수": round(score, 2)
                    })

        if results_list:
            df = pd.DataFrame(results_list)

            # 1. 그래프 그리기
            st.subheader("📈 키워드별 블루오션 지수 비교")
            fig = px.bar(df, x='키워드', y='블루오션 지수', 
                         color='블루오션 지수', 
                         color_continuous_scale='RdBu_r', # 빨강-파랑 반전 스케일
                         text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

            # 2. 색상 적용된 표 보여주기
            st.subheader("📑 상세 데이터")
            styled_df = df.style.applymap(highlight_score, subset=['블루오션 지수'])
            st.dataframe(styled_df, use_container_width=True)

            # 3. 엑셀 다운로드
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)

            st.download_button("📥 결과 엑셀 다운로드", output.getvalue(), "blue_ocean_report.xlsx")
