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
st.info("💡 에러 방지를 위해 연령/성별 필드를 제거하고 '전체 데이터'를 수집하도록 최적화했습니다.")
col1, col2 = st.columns(2)
with col1:
    c_id = st.text_input("Client ID", value="", placeholder="ID 입력")
with col2:
    c_secret = st.text_input("Client Secret", value="", type="password", placeholder="Secret 입력")

st.markdown("---")

# 3. 카테고리 설정 (전체 리스트 유지)
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
    patterns = [
        f"이번 주말에 다녀온 {keyword}, 솔직히 말해서 '이거' 하나는 좀 별로였어요",
        f"드디어 다녀온 {keyword}! 광고 말고 진짜 찐후기 궁금하신 분들을 위해 준비함",
        f"아이랑 {keyword} 갈 때 '이 시간'에 가야 줄 안 서고 바로 들어갑니다 (꿀팁)",
        f"엄마들이 자꾸 물어보는 {keyword} 정보, 이 포스팅 하나로 정리 끝낼게요",
        f"실패 없는 {keyword} 방문을 위한 현실적인 조언 (주차, 동선, 명당자리)",
        f"{keyword} 방문 예정이라면 꼭 알아야 할 '의외의' 준비물 3가지",
        f"요즘 핫한 {keyword}, 소문만큼 정말 좋을까? 내돈내산 가감 없는 후기",
        f"아이와 함께 {keyword} 200% 즐기는 법! (부모님 체력 아끼는 코스 추천)",
        f"{keyword} 가기 전 필독! 모르면 손해보는 할인 정보와 입장 팁",
        f"직접 가보고 느낀 {keyword} 명당 자리! 명당 잡으려면 몇 시까지 가야 할까?",
        f"{keyword} 근처 맛집까지 싹 정리! 아이랑 가기 좋은 완벽한 하루 코스"
    ]
    return random.sample(patterns, 3)

# 5. 분석 실행
if st.button("🚀 심층 분석 시작"):
    if not c_id or not c_secret:
        st.warning("⚠️ API 키를 입력해주세요!")
    else:
        headers = {
            "X-Naver-Client-Id": c_id.strip(),
            "X-Naver-Client-Secret": c_secret.strip(),
            "Content-Type": "application/json"
        }
        final_keywords = []

        with st.spinner('데이터를 수집 중입니다...'):
            if mode == "실시간 핫 키워드":
                success = False
                for i in range(3, 11):
                    target_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    
                    # [최종 해결책] keyword 필드 추가 및 category 문자열 유지
                    s_body = {
                        "startDate": target_date,
                        "endDate": target_date,
                        "timeUnit": "date",
                        "category": str(selected_category_id), 
                        "keyword": "",  # [필수] 이 필드가 없어서 에러가 났던 겁니다!
                        "device": "", 
                        "gender": "", 
                        "ages": []
                    }
                    
                    res = requests.post(
                        "https://openapi.naver.com/v1/datalab/shopping/category/keywords", 
                        headers=headers, 
                        data=json.dumps(s_body)
                    )
                    
                    if res.status_code == 200:
                        data = res.json()
                        if 'results' in data and data['results'][0]['data']:
                            final_keywords = [item['title'] for item in data['results'][0]['data'][:15]]
                            success = True
                            st.write(f"✅ {target_date} 데이터 수집 성공!")
                            break
                    else:
                        st.write(f"🔍 {target_date} 시도 결과: {res.status_code} ({res.text})")
                
                if not success:
                    st.error("⚠️ 데이터 수집 실패. API 권한 설정 또는 필수 필드를 다시 확인해주세요.")
            else:
                final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

            # 결과 리스트와 리포트 출력
            if final_keywords:
                results = []
                p_bar = st.progress(0)
                for idx, kw in enumerate(final_keywords):
                    # 블로그 조회
                    r_blog = requests.get(f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(kw)}&display=1", headers=headers)
                    b_cnt = r_blog.json().get('total', 1) if r_blog.status_code == 200 else 1
                    
                    # 트렌드 조회
                    t_body = {"startDate": (datetime.now()-timedelta(days=31)).strftime('%Y-%m-%d'), "endDate": (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d'), "timeUnit": "date", "keywordGroups": [{"groupName": kw, "keywords": [kw]}]}
                    r_trend = requests.post("https://openapi.naver.com/v1/datalab/search", headers=headers, data=json.dumps(t_body))
                    
                    ratio = 0.0001
                    if r_trend.status_code == 200:
                        try: ratio = r_trend.json()['results'][0]['data'][-1]['ratio']
                        except: pass
                    
                    penalty = math.log10(b_cnt) * 0.6 if b_cnt > 0 else 0
                    score = max(0.0, min(10.0, (math.log10((ratio/b_cnt)*1000000 + 1) * 2.2) - penalty))
                    results.append({"키워드": kw, "블루오션지수": round(score, 2), "AI 제목 추천": " | ".join(generate_ai_titles(kw))})
                    p_bar.progress((idx + 1) / len(final_keywords))

                df = pd.DataFrame(results).sort_values(by="블루오션지수", ascending=False)
                st.plotly_chart(px.bar(df, x='키워드', y='블루오션지수', color='블루오션지수', range_y=[0, 10]))
                
                st.subheader("📑 AI 전략 리포트")
                st.dataframe(df, use_container_width=True)

# 6. 본문 프롬프트 생성기 (이종호님의 이모티콘 프롬프트)
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



















