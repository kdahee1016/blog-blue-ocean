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

# 2. API 설정
st.info("💡 실행 후 웹 화면의 입력창에 ID와 Secret을 직접 붙여넣어 주세요.")
col1, col2 = st.columns(2)
with col1:
    c_id = st.text_input("Client ID", value="", placeholder="네이버 ID 입력")
with col2:
    c_secret = st.text_input("Client Secret", value="", type="password", placeholder="네이버 Secret 입력")

st.markdown("---")

# 3. 카테고리 설정
category_map = {
    "패션의류": {"여성의류": "50000000", "여성언더웨어/잠옷": "50000167", "남성의류": "50000001", "아동의류": "50000002"},
    "패션잡화": {"신발": "50000003", "가방": "50000004", "지갑": "50000005", "벨트": "50000006", "선글라스/안경테": "50000007", "헤어액세서리": "50000008"},
    "화장품/미용": {"스킨케어": "50000009", "메이크업": "50000010", "헤어케어": "50000011", "바디케어": "50000012", "향수": "50000013", "네일케어": "50000014"},
    "디지털/가전": {"주방가전": "50000015", "생활가전": "50000016", "계절가전": "50000017", "PC/노트북": "50000020"},
    "가구/인테리어": {"침실가구": "50000021", "거실가구": "50000022", "주방가구": "50000023", "인테리어소품": "50000026"},
    "출산/육아": {"분유/기저귀/물티슈": "50000027", "유아동의류": "50000028", "장난감/완구": "50000030", "유아외출용품": "50000032"},
    "식품": {"농산물": "50000033", "축산물": "50000034", "가공식품": "50000036", "건강식품": "50000037", "음료": "50000038"},
    "스포츠/레저": {"등산": "50000039", "캠핑": "50000040", "낚시": "50000041", "골프": "50000042", "자전거": "50000043"},
    "생활/건강": {"주방용품": "50000045", "생활용품": "50000046", "욕실용품": "50000047", "반려동물": "50000049", "공구": "50000050"},
    "여가/생활편의": {"국내여행/티켓": "50000051", "해외여행/티켓": "50000052", "문화/예매권": "50000053"}
}

mode = st.radio("분석 방식 선택", ["직접 입력", "실시간 핫 키워드"])

if mode == "실시간 핫 키워드":
    main_cat = st.selectbox("📂 대분류 선택", list(category_map.keys()))
    sub_cat = st.selectbox("🔍 하위 카테고리 선택", list(category_map[main_cat].keys()))
    selected_category_id = category_map[main_cat][sub_cat]
else:
    user_input = st.text_area("분석할 키워드를 쉼표(,)로 구분해서 적어주세요.", "건대 베이커리 카페, 서울 아이랑 맛집")

def generate_ai_titles(keyword):
    if any(x in keyword for x in ["여행", "가볼만한곳", "코스", "티켓"]):
        return [
            f"{keyword} 아이랑 200% 즐기는 팁! (체력 아끼는 동선)",
            f"{keyword} 근처 가볼만한 곳까지 싹 정리 (주말 나들이)",
            f"주말에 다녀온 {keyword} 솔직 후기, '이것'만은 꼭 챙기세요"
        ]
    else:
        return [
            f"내돈내산 {keyword} 솔직 사용기! 장단점 완벽 비교",
            f"요즘 핫한 {keyword} 실패 없이 고르는 법 (성분/가성비 분석)",
            f"{keyword} 고민 중이라면 필독! 직접 써보고 느낀 점 정리"
        ]

# 4. 분석 실행
if st.button("🚀 심층 분석 시작"):
    clean_id = c_id.strip()
    clean_secret = c_secret.strip()

    headers = {
        "X-Naver-Client-Id": clean_id,
        "X-Naver-Client-Secret": clean_secret,
        "Content-Type": "application/json"
    }

    final_keywords = []

    with st.spinner('실시간 블로그 발행량을 정밀 조사 중입니다...'):
        if mode == "실시간 핫 키워드":
            search_name = sub_cat if sub_cat else "인기상품"
            url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/top100"
            target_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            payload = {"startDate": target_date, "endDate": target_date, "timeUnit": "date", "category": str(selected_category_id)}
            
            try:
                res = requests.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    raw_data = res.json().get('results', [{}])[0].get('data', [])
                    final_keywords = [item.get('group') for item in raw_data[:15] if item.get('group')]
            except:
                pass

            if not final_keywords:
                st.info(f"💡 {search_name} 순위 집계 중... 맞춤형 연관 분석으로 전환합니다.")
                if "여행" in search_name or "티켓" in search_name:
                    suffixes = ["가볼만한곳", "숙소 추천", "패키지", "가격", "예약", "명소", "당일치기", "1박2일", "코스", "꿀팁"]
                elif "의류" in search_name or "패션" in search_name:
                    suffixes = ["코디", "사이즈", "추천", "브랜드", "신상", "데일리룩", "후기", "하객룩", "가성비", "쇼핑몰"]
                elif "식품" in search_name or "음식" in search_name:
                    suffixes = ["밀키트", "대용량", "레시피", "칼로리", "맛있게 먹는 법", "추천", "후기", "유통기한", "보관법", "가성비"]
                elif "육아" in search_name or "아동" in search_name:
                    suffixes = ["추천", "사이즈", "선물", "인기순위", "체험단", "내돈내산", "공구", "할인", "사용법", "신학기"]
                else:
                    suffixes = ["추천", "후기", "가성비", "순위", "비교", "장단점", "할인", "방법", "꿀팁", "사이트"]
                final_keywords = [f"{search_name} {s}" for s in suffixes]
        else:
            final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

        if final_keywords:
            results_list = []
            p_bar = st.progress(0)
            
            for idx, kw in enumerate(final_keywords):
                r_blog = requests.get(
                    f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(kw)}&display=1", 
                    headers=headers
                )
                # 데이터가 없으면 0이 아니라 최소 1로 잡아 로그 에러 방지
                b_cnt = r_blog.json().get('total', 1) if r_blog.status_code == 200 else 1
                
                # [수정] 디테일한 블루오션 지수 계산식 (오늘 오전 논의 반영)
                # 발행량이 많을수록 감점 폭을 키우고(1.1 -> 1.3), 기본 점수를 조정했습니다.
                if b_cnt > 1:
                    score = round(max(0.1, 10.0 - (math.log10(b_cnt) * 1.35)), 2)
                else:
                    score = 9.99 # 발행량이 아예 없으면 최상위 점수
                
                results_list.append({
                    "키워드": kw, 
                    "블로그 발행량": f"{b_cnt:,}건",
                    "블루오션지수": score, 
                    "AI 제목 추천": " | ".join(generate_ai_titles(kw))
                })
                p_bar.progress((idx + 1) / len(final_keywords))

            df = pd.DataFrame(results_list).sort_values(by="블루오션지수", ascending=False)
            
            # [색상 수정] 레드(0점) -> 옐로우(5점) -> 블루(10점)
            fig = px.bar(
                df, x='키워드', y='블루오션지수',
                color='블루오션지수',
                # 컬러 스케일을 더 직관적인 3단계로 구성
                color_continuous_scale=['#FF0000', '#FFFF00', '#0000FF'], 
                range_y=[0, 10],
                title=f"🌊 {search_name} 정밀 분석 (파란색일수록 발행량이 적은 블루오션!)"
            )
            # 수치가 잘 보이게 텍스트 추가
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig)
            
            st.subheader("📑 실시간 블루오션 전략 리포트")
            st.dataframe(df, use_container_width=True)
            st.balloons()

if final_keywords:
            results_list = []
            p_bar = st.progress(0)
            
            for idx, kw in enumerate(final_keywords):
                r_blog = requests.get(
                    f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(kw)}&display=1", 
                    headers=headers
                )
                b_cnt = r_blog.json().get('total', 1) if r_blog.status_code == 200 else 1
                
                # 1. 정밀 지수 계산 (발행량 감점 강화)
                if b_cnt > 1:
                    score = round(max(0.1, 10.0 - (math.log10(b_cnt) * 1.35)), 2)
                else:
                    score = 9.99
                
                # 2. [추가] 다이아몬드~브론즈 등급 판정 로직
                if score >= 8.5:
                    grade = "💎 다이아몬드 (무조건 써야 함)"
                elif score >= 7.0:
                    grade = "🥇 골드 (상위노출 확률 높음)"
                elif score >= 4.0:
                    grade = "🥈 실버 (경쟁이 좀 있음)"
                else:
                    grade = "🥉 브론즈 (레드오션 주의)"

                results_list.append({
                    "등급": grade,
                    "키워드": kw, 
                    "블로그 발행량": f"{b_cnt:,}건",
                    "블루오션지수": score, 
                    "AI 제목 추천": " | ".join(generate_ai_titles(kw))
                })
                p_bar.progress((idx + 1) / len(final_keywords))

            # 3. 데이터프레임 생성 및 정렬
            df = pd.DataFrame(results_list).sort_values(by="블루오션지수", ascending=False)
            
            # 그래프 출력
            fig = px.bar(
                df, x='키워드', y='블루오션지수',
                color='블루오션지수',
                color_continuous_scale=['#FF0000', '#FFFF00', '#0000FF'], 
                range_y=[0, 10],
                title=f"🌊 {search_name} 블루오션 등급 분석"
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig)
            
            # 4. 등급별 요약 표 출력 (이종호님이 찾으시던 그 표!)
            st.subheader("📑 실시간 블루오션 전략 리포트")
            
            # 표 디자인 개선: 등급 컬럼을 맨 앞으로
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.balloons()

# 5. 본문 프롬프트 생성기
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
 - 본문 작성 시 블로그에 맞는 톤앤매너를 지켜주고
 - 말투는 30대 여자가 작성하는 ~했음, ~했다, 혼잣말 느낌 등의 편안한 일기형 말투를 섞어서 작성
 - 긴 문장이라도 한 줄에 공백포함 최대 60~70byte로 자연스럽게 끊어서 작성해줘.
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


