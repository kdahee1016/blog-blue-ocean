import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import urllib.parse
import math
import random
from bs4 import BeautifulSoup

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

def get_naver_related_keywords(keyword):
    """
    네이버 검색 결과 페이지에서 연관검색어를 추출합니다.
    """
    url = f"https://search.naver.com/search.naver?query={urllib.parse.quote(keyword)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        related_tags = soup.select(".lst_related_srch .tit")
        return [tag.get_text().strip() for tag in related_tags]
    except:
        return []

mode = st.radio("분석 방식 선택", ["직접 입력", "실시간 핫 키워드"])

# 초기 변수 설정
search_name = ""
selected_category_id = ""

if mode == "실시간 핫 키워드":
    main_cat = st.selectbox("📂 대분류 선택", list(category_map.keys()))
    sub_cat = st.selectbox("🔍 하위 카테고리 선택", list(category_map[main_cat].keys()))
    selected_category_id = category_map[main_cat][sub_cat]
    search_name = sub_cat
else:
    user_input = st.text_area("분석할 키워드를 쉼표(,)로 구분해서 적어주세요.", "건대 베이커리 카페, 서울 아이랑 맛집")
    search_name = "직접 입력"

# 4. 분석 실행
if st.button("🚀 심층 분석 시작"):
    headers = {"X-Naver-Client-Id": c_id.strip(), "X-Naver-Client-Secret": c_secret.strip(), "Content-Type": "application/json"}
    final_keywords = [] 

    with st.spinner('분석 중...'):
        if mode == "실시간 핫 키워드":
            url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/top100"
            target_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            payload = {"startDate": target_date, "endDate": target_date, "timeUnit": "date", "category": str(selected_category_id)}
            res = requests.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                raw_data = res.json().get('results', [{}])[0].get('data', [])
                final_keywords = [item.get('group') for item in raw_data[:15]]
        else: 
            final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

        if final_keywords:
            results_list = []
            related_data = {}
            p_bar = st.progress(0)
            
            for idx, kw in enumerate(final_keywords):
                r_blog = requests.get(f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(kw)}&display=1", headers=headers)
                b_cnt = r_blog.json().get('total', 0) if r_blog.status_code == 200 else 0
                
                url_trend = "https://openapi.naver.com/v1/datalab/search"
                payload_trend = {"startDate": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'), "endDate": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), "timeUnit": "month", "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}
                res_trend = requests.post(url_trend, headers=headers, json=payload_trend)
                s_ratio = 0
                if res_trend.status_code == 200:
                    res_data = res_trend.json().get('results', [{}])[0].get('data', [])
                    if res_data: s_ratio = res_data[0].get('ratio', 0)

                if b_cnt > 100000: status = "🔴 레드오션"; score = 1.5
                elif b_cnt > 30000: status = "🟠 중간"; score = 4.5
                elif b_cnt > 5000: status = "🟢 양호"; score = 7.5
                else: status = "🔵 블루오션" if s_ratio > 0 else "🟢 양호"; score = 9.5 if s_ratio > 0 else 6.5

                results_list.append({"시장성": status, "키워드": kw, "발행량": f"{b_cnt:,}건", "검색강도(상대)": f"{s_ratio:.1f}%", "지수": score})
                related_data[kw] = get_naver_related_keywords(kw)
                p_bar.progress((idx + 1) / len(final_keywords))

            df = pd.DataFrame(results_list).sort_values(by="지수", ascending=False)
            
            # --- 그래프 y축 범위 고정 (0~10) ---
            fig = px.bar(
                df, x='키워드', y='지수', color='시장성',
                color_discrete_map={"🔵 블루오션": "#0000FF", "🟢 양호": "#00FF00", "🟠 중간": "#FFA500", "🔴 레드오션": "#FF0000"},
                title="🔍 키워드별 시장성 분석 리포트",
                range_y=[0, 10]
            )
            st.plotly_chart(fig)
            st.dataframe(df.drop(columns=['지수']), use_container_width=True, hide_index=True)
            
            # --- 연관검색어 리스트 (st.code 활용으로 자동 복사 구현) ---
            st.markdown("---")
            st.subheader("🔗 네이버 연관검색어 (단어를 클릭하면 개별 복사됩니다)")
            
            for kw in final_keywords:
                rel_list = related_data.get(kw, [])
                st.write(f"📌 **{kw}**")
                
                if rel_list:
                    # 단어들을 가로로 나열하기 위해 컬럼 사용 (최대 5개씩 끊어서 표시)
                    # 혹은 간단하게 개별 버튼을 생성
                    cols = st.columns(5) # 한 줄에 5개씩 버튼 배치
                    for i, rel_kw in enumerate(rel_list):
                        with cols[i % 5]:
                            # 단어별로 클릭 시 복사 기능 제공
                            st.copy_to_clipboard(rel_kw, before_text=f"{rel_kw}", after_text="✅")
                    st.write("") # 간격 조절
                else:
                    st.caption("관련된 연관검색어가 없습니다.")
            
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



