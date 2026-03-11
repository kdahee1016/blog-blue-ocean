import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import urllib.parse
import math
import random

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
    # 1. 여행/티켓/장소 관련 키워드용 (맛집, 코스 위주)
    if any(x in keyword for x in ["여행", "가볼만한곳", "코스", "티켓", "관광", "명소"]):
        travel_templates = [
            f"{keyword} 현지인 추천 맛집 리스트 공유",
            f"{keyword} 아이랑 가기 좋은 실내 코스 정리",
            f"{keyword} 주차장 정보 및 입장료 총정리",
            f"{keyword} 직접 다녀온 당일치기 여행 코스",
            f"{keyword} 숨겨진 명소와 포토존 위치 정보",
            f"{keyword} 근처 식당 솔직한 방문 후기",
            f"{keyword} 주말 나들이 가기 전 꼭 알아야 할 점",
            f"{keyword} 대기 시간 줄이는 예약 꿀팁 공유",
            f"{keyword} 연령대별 선호하는 관광 포인트 분석",
            f"{keyword} 숙소 선정 시 주의사항 및 가격 비교",
            f"{keyword} 야경 예쁜 곳과 산책로 동선 추천",
            f"{keyword} 부모님 모시고 가기 좋은 식당 정보",
            f"{keyword} 시즌별 운영 시간 및 휴무일 안내",
            f"{keyword} 뚜벅이 여행자를 위한 대중교통 이용법",
            f"{keyword} 비 오는 날 갈만한 실내 장소 추천",
            f"{keyword} 실패 없는 1박 2일 여행 일정표",
            f"{keyword} 사진 잘 나오는 시간대와 촬영 포인트",
            f"{keyword} 입장권 할인 받는 방법과 구매처 정보",
            f"{keyword} 주변 카페 투어 및 디저트 맛집 분석",
            f"{keyword} 여행 가방 준비물 리스트 체크사항"
        ]
        return random.sample(travel_templates, 3)

    # 2. 스킨케어/육아/식품/의류 등 일반 상품용 (정보성/리뷰 위주)
    else:
        product_templates = [
            f"{keyword} 내돈내산 한 달 사용 후기 정리",
            f"{keyword} 성분 분석 및 피부 타입별 주의사항",
            f"{keyword} 사이즈 선택 가이드 및 실착용 데이터",
            f"{keyword} 가성비 좋은 브랜드 제품별 특징 비교",
            f"{keyword} 장단점 확실하게 정리한 구매 가이드",
            f"{keyword} 유통기한 확인법 및 올바른 보관 방법",
            f"{keyword} 실제 사용자들의 평점 및 만족도 분석",
            f"{keyword} 최저가 구매처 및 할인 프로모션 정보",
            f"{keyword} 부작용 유무와 안전성 테스트 결과 공유",
            f"{keyword} 초보자를 위한 단계별 사용법 안내",
            f"{keyword} 비슷한 가격대 타사 제품과 정밀 비교",
            f"{keyword} 재구매 의사 결정에 도움 되는 정보",
            f"{keyword} 선물용으로 적합한 패키지 구성 확인",
            f"{keyword} 실물 색상과 가장 유사한 촬영 사진",
            f"{keyword} 세탁 및 관리 시 주의해야 할 포인트",
            f"{keyword} 맛과 식감 위주의 솔직한 시식 기록",
            f"{keyword} 아이에게 안전한 소재인지 확인한 결과",
            f"{keyword} 계절별 활용도 및 코디 연출 방법",
            f"{keyword} 단독 사용 시와 병행 사용 시 차이점",
            f"{keyword} 공식 홈페이지와 오픈마켓 가격 차이 분석"
        ]
        return random.sample(product_templates, 3)

# 4. 분석 실행
if st.button("🚀 심층 분석 시작"):
    clean_id = c_id.strip()
    clean_secret = c_secret.strip()
    headers = {
        "X-Naver-Client-Id": clean_id, 
        "X-Naver-Client-Secret": clean_secret, 
        "Content-Type": "application/json"
    }
    
    final_keywords = [] # 변수 초기화

    with st.spinner('선택하신 카테고리에 딱 맞는 키워드를 분석 중입니다...'):
        # 1. 키워드 추출 로직
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
                st.info(f"💡 {search_name} 연관 분석으로 전환합니다.")
                
                # 1. 여행 관련 (가장 먼저 체크)
                if any(x in search_name for x in ["여행", "티켓", "가볼만한곳"]):
                    suffixes = [
                        "아이랑 가볼만한곳", "주차 정보", "입장료 할인", 
                        "근처 맛집 베스트", "포토존 위치", "방문 전 주의사항", 
                        "현지인 추천 코스", "무료 입장 꿀팁", "주말 웨이팅 후기", 
                        "숙소 근처 식당", "내돈내산 솔직후기", "실내 데이트 코스"
                    ]
                
                # 2. 패션 관련
                elif any(x in search_name for x in ["의류", "패션", "잡화"]):
                    suffixes = ["코디", "사이즈", "추천", "브랜드", "신상", "데일리룩", "후기", "하객룩", "가성비", "쇼핑몰"]
                
                # 3. 식품 관련
                elif any(x in search_name for x in ["식품", "음식", "맛집"]):
                    suffixes = ["밀키트", "대용량", "레시피", "칼로리", "맛있게 먹는 법", "추천", "후기", "유통기한", "보관법", "가성비"]
                
                # 4. 육아 관련
                elif any(x in search_name for x in ["육아", "아동", "유아"]):
                    suffixes = ["추천", "사이즈", "선물", "인기순위", "체험단", "내돈내산", "공구", "할인", "사용법", "신학기"]
                
                # 5. 그 외 기타 카테고리
                else:
                    suffixes = ["추천", "후기", "가성비", "순위", "비교", "장단점", "할인", "방법", "꿀팁", "사이트"]
                
                # [중요] 여기서 딱 한 번만 키워드 조합을 생성합니다.
                final_keywords = [f"{search_name} {s}" for s in suffixes]
        
        else: # 직접 입력 모드 (여기가 에러 났던 부분입니다!)
            search_name = "직접 입력"
            final_keywords = [k.strip() for k in user_input.split(",") if k.strip()]

        # 2. 결과 분석 및 출력
        if final_keywords:
            results_list = []
            p_bar = st.progress(0)
            
            for idx, kw in enumerate(final_keywords):
                # 1. 블로그 발행량 조회 (공급량)
                r_blog = requests.get(
                    f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(kw)}&display=1", 
                    headers=headers
                )
                b_cnt = r_blog.json().get('total', 0) if r_blog.status_code == 200 else 0
                
                # 2. 검색 트렌드 조회 (상대적 수요)
                url_trend = "https://openapi.naver.com/v1/datalab/search"
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                payload_trend = {
                    "startDate": last_month, "endDate": yesterday, "timeUnit": "month",
                    "keywordGroups": [{"groupName": kw, "keywords": [kw]}]
                }
                res_trend = requests.post(url_trend, headers=headers, json=payload_trend)
                s_ratio = 0
                if res_trend.status_code == 200:
                    res_data = res_trend.json().get('results', [{}])[0].get('data', [])
                    if res_data: s_ratio = res_data[0].get('ratio', 0)

                # 3. 전략적 등급 산출 (발행량 기반 판정)
                # 수만 건 이상의 발행량은 검색량이 많아도 현실적으로 상위 노출이 어렵다는 점을 반영
                if b_cnt > 100000: # 10만 건 이상
                    status = "🔴 레드오션"
                    score = 1.5
                elif b_cnt > 30000: # 3만 건 ~ 10만 건
                    status = "🟠 중간"
                    score = 4.5
                elif b_cnt > 5000: # 5천 건 ~ 3만 건
                    status = "🟢 양호"
                    score = 7.5
                else: # 5천 건 미만 (진짜 틈새)
                    if s_ratio > 0:
                        status = "🔵 블루오션"
                        score = 9.5
                    else:
                        status = "🟢 양호" # 검색은 적지만 써볼만한 곳
                        score = 6.5

                results_list.append({
                    "시장성": status,
                    "키워드": kw, 
                    "발행량": f"{b_cnt:,}건", 
                    "검색강도(상대)": f"{s_ratio:.1f}%",
                    "지수": score,
                    "AI 제목": " | ".join(generate_ai_titles(kw))
                })
                p_bar.progress((idx + 1) / len(final_keywords))

            # 4. 결과 출력 및 시각화
            df = pd.DataFrame(results_list).sort_values(by="지수", ascending=False)
            
            # 그래프: 등급별 컬러 매핑
            fig = px.bar(
                df, x='키워드', y='지수', color='시장성',
                color_discrete_map={
                    "🔵 블루오션": "#0000FF", "🟢 양호": "#00FF00",
                    "🟠 중간": "#FFA500", "🔴 레드오션": "#FF0000"
                },
                title="🔍 키워드별 시장성 분석 리포트"
            )
            st.plotly_chart(fig)
            
            st.subheader("📑 실시간 블루오션 전략 리포트")
            # 표에서도 동그라미가 보이게 출력
            st.dataframe(df.drop(columns=['지수']), use_container_width=True, hide_index=True)
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





