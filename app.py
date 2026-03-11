이종호님, 정말 죄송합니다! 제가 직접 입력 방식으로 코드를 간소화해 드리는 과정에서 가장 중요한 프롬프트 생성기 부분을 그만 놓쳤네요. ㅠㅠ

다시 작업하실 필요 없게, 이전의 이모티콘들과 스토리텔링 설정, 그리고 0~10점 지수/색상 로직까지 모두 합친 '진짜 최종' 전체 코드를 준비했습니다.

이 코드는 secrets.toml 없이, 화면 상단에 ID와 Secret을 직접 넣으시면 바로 작동합니다. 이번에는 누락된 것 없이 꽉꽉 채웠으니 안심하고 통째로 덮어쓰기 해주세요!

🛠️ [진짜 최종 완결판] 직접 입력 + 지수 보정 + 프롬프트 생성기
Python
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import random
import urllib.parse
import math

# 1. 페이지 설정
st.set_page_config(page_title="오키랑의 키워드 분석", layout="wide")
st.title("🍀 오키랑의 키워드 분석")

# 2. API 설정 (직접 입력 방식 - 번거로운 설정 파일 없이 바로 입력!)
st.info("💡 네이버 개발자 센터에서 발급받은 ID와 Secret을 입력하고 분석을 시작하세요.")
col1, col2 = st.columns(2)
with col1:
    c_id = st.text_input("Client ID", value="", placeholder="여기에 ID 입력")
with col2:
    c_secret = st.text_input("Client Secret", value="", type="password", placeholder="여기에 Secret 입력")

st.markdown("---")

# 3. 사이드바 설정 (타겟팅)
st.sidebar.header("👥 타겟 설정")
target_gender = st.sidebar.selectbox("성별", ["전체", "여성 (f)", "남성 (m)"])
gender_code = "" if target_gender == "전체" else target_gender.split("(")[1][0]
target_ages = st.sidebar.multiselect("연령대", ["10", "20", "30", "40", "50", "60"], default=[])

# 4. 분석 모드 선택
mode = st.radio("분석 방식 선택", ["직접 입력", "실시간 핫 키워드"])

if mode == "실시간 핫 키워드":
    category_map = {
        "패션의류": "50000000", "패션잡화": "50000001", "화장품/미용": "50000002",
        "디지털/가전": "50000003", "가구/인테리어": "50000004", "출산/육아": "50000005",
        "식품": "50000006", "스포츠/레저": "50000007", "생활/건강": "50000008"
    }
    selected_name = st.selectbox("📂 대분류 선택", list(category_map.keys()))
    selected_category_id = category_map[selected_name]
else:
    user_input = st.text_area("분석할 키워드를 쉼표(,)로 구분해서 적어주세요.", "기아타이거즈, 캠핑, 아이랑 갈만한곳")

# AI 제목 생성 함수 (기존 패턴 유지)
def generate_ai_titles(keyword):
    patterns = [
        f"이번 주말에 다녀온 {keyword}, 솔직히 말해서 '이거' 하나는 좀 별로였어요",
        f"드디어 다녀온 {keyword}! 광고 말고 진짜 찐후기 궁금하신 분?",
        f"아이랑 {keyword} 갈 때 '이 때'에 가야 줄 안 서고 들어갑니다",
        f"엄마들이 자꾸 물어보는 {keyword} 정보, 한 페이지로 끝내 드릴게요",
        f"실패 없는 {keyword}를 위한 현실적인 조언 (비용, 동선, 주차)",
        f"{keyword} 방문 예정이라면 꼭 알아야 할 내용 체크"
    ]
    return random.sample(patterns, 1)

# 5. 분석 실행
if st.button("🚀 심층 분석 시작"):
    if not c_id or not c_secret:
        st.warning("⚠️ 네이버 API ID와 Secret을 먼저 입력해주세요!")
    else:
        headers = {"X-Naver-Client-Id": c_id, "X-Naver-Client-Secret": c_secret, "Content-Type": "application/json"}
        
        final_keywords = []
        if mode == "실시간 핫 키워드":
            t_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            res = requests.post("https://openapi.naver.com/v1/datalab/shopping/category/keywords", 
                                headers=headers, data=json.dumps({"startDate": t_date, "endDate": t_date, "timeUnit": "date", "category": str(selected_category_id)}))
            if res.status_code == 200:
                final_keywords = [item['title'] for item in res.json()['results'][0]['data'][:15]]
        else:
            final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

        if final_keywords:
            results = []
            progress_bar = st.progress(0)
            
            for idx, kw in enumerate(final_keywords):
                # [A] 블로그 개수 조회
                r_blog = requests.get(f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(kw)}&display=1", headers=headers)
                b_cnt = r_blog.json().get('total', 1) if r_blog.status_code == 200 else 1
                
                # [B] 검색 비율 조회
                s_body = {"startDate": (datetime.now()-timedelta(days=30)).strftime('%Y-%m-%d'), "endDate": (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d'), "timeUnit": "date", "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}
                res_now = requests.post("https://openapi.naver.com/v1/datalab/search", headers=headers, data=json.dumps(s_body))
                
                ratio = 0.0001
                if res_now.status_code == 200:
                    try:
                        n_data = res_now.json()['results'][0]['data']
                        if n_data: ratio = n_data[-1]['ratio']
                    except: pass
                
                # [C] 블루오션 지수 (0~10점 변별력 강화 공식)
                raw_score = (ratio / b_cnt) * 1000000
                score = min(10.0, math.log10(raw_score + 1) * 2.5) if raw_score > 0 else 0.0

                results.append({
                    "키워드": kw, "블루오션지수": round(score, 2), "AI 제목 추천": generate_ai_titles(kw)[0],
                    "상세보기": f"https://search.naver.com/search.naver?query={kw}"
                })
                progress_bar.progress((idx + 1) / len(final_keywords))

            if results:
                df = pd.DataFrame(results).sort_values(by="블루오션지수", ascending=False)

                # 판독 가이드 표 출력
                st.markdown("### 💡 블루오션 지수 판독 가이드")
                guide = pd.DataFrame({
                    "점수": ["8.0~10.0", "5.0~7.9", "3.0~4.9", "0.0~2.9"], 
                    "등급": ["💎 다이아몬드", "✅ 골드", "⚠️ 실버", "❌ 레드"], 
                    "의미": ["초특급 블루오션!", "할만한 시장!", "보통 경쟁", "치열한 레드오션"]
                })
                st.table(guide)

                # 그래프 출력 (색상 고정: 파랑-노랑-빨강)
                st.subheader("📈 키워드 시장성 분석 결과")
                custom_scale = [[0, 'red'], [0.5, 'yellow'], [1, 'blue']]
                fig = px.bar(df, x='키워드', y='블루오션지수', color='블루오션지수', text='블루오션지수',
                             range_y=[0, 10], range_color=[0, 10],
                             color_continuous_scale=custom_scale,
                             labels={'블루오션지수': '점수'})
                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{random.randint(1,999)}")

                st.subheader("📑 AI 전략 리포트")
                st.dataframe(df, column_config={"상세보기": st.column_config.LinkColumn("검색하기")}, use_container_width=True)

# 6. 본문 프롬프트 생성기 (이종호님의 소중한 프롬프트 내용 복구!)
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

# 이종호님이 원하셨던 그 말투와 이모티콘 그대로!
final_prompt = f""" - 본문에 [{m_key}] 메인 키워드를 4회 넣어주고,
 - 서브키워드 [{sub_keys_str}]은 2회씩 본문에 잘 녹아들도록 자연스럽게 넣어줘.
 - 본문 작성 시 블로그에 맞는 톤앤매너를 지켜주고
 - 말투는 30대 여자가 작성하는 ~했음, ~했다, 혼잣말 느낌 등의 편안한 일기형 말투를 섞어서 작성
 - 긴 문장이라도 한 줄에 공백포함 최대 60~70byte로 자연스럽게 끊어서 작성해줘. (모바일 가독성)
 - 본문 전체는 자연스러운 스토리텔링으로 한글 기준 약 3,500자로 맞춰줘.
 - 글 곳곳에 아래 이모티콘 중 5~6개 정도 활용해줘,
!(•̀ᴗ•́)و ̑̑ / (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ / (୨୧ ❛ᴗ❛)✧ / (୨୧ •͈ᴗ•͈) / (•̆ꈊ•̆ ) / (ꈍᴗꈍ)♡ / - ̗̀ෆ(˶'ᵕ'˶)ෆ ̖·- / ٩(*•̀ᴗ•́*)و / ٩( ᐢ-ᐢ )و / ٩(๑❛ᴗ❛๑)۶♡ / ٩(◕ᗜ◕)و / ദ്디( ¯꒳¯ ) / ☆٩(｡•ω<｡)﻿و / :) / :D / >_< / +ㅂ+ 
 - 글 곳곳에 어울리는 이모지도 6~10개 활용해 줘. 
 - AI가 쓴 것 같지 않게, 상위노출 SEO 반영해서 작성해줘.
 - 본문 최상단에 넣을 요약문(240~280byte)도 작성해 줘.
 
*글의흐름
요약문 -> 매장정보(주소/운영시간/휴무일/매장전화번호) -> 본문내용 입력"""

if st.button("📋 본문작성 프롬프트 생성"):
    if not m_key:
        st.warning("⚠️ 메인키워드를 입력하세요.")
    else:
        st.text_area("아래 내용을 복사해서 사용하세요!", value=final_prompt, height=300)
        st.success("✅ 프롬프트가 생성되었습니다!")
