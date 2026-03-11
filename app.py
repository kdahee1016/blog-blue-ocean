import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import random
import urllib.parse
import math # 지수 계산을 위한 수학 함수 추가

# 1. 페이지 설정
st.set_page_config(page_title="오키랑의 키워드 분석", layout="wide")
st.title("🍀 오키랑의 키워드 분석")

# 2. API 설정 (secrets.toml 연동)
default_id = st.secrets.get("naver_client_id", "")
default_secret = st.secrets.get("naver_client_secret", "")

with st.expander("🔐 네이버 API 키 설정", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        c_id = st.text_input("Client ID", value=default_id, type="password")
    with col2:
        c_secret = st.text_input("Client Secret", value=default_secret, type="password")

st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("👥 타겟 설정")
target_gender = st.sidebar.selectbox("성별", ["전체", "여성 (f)", "남성 (m)"])
gender_code = "" if target_gender == "전체" else target_gender.split("(")[1][0]
target_ages = st.sidebar.multiselect("연령대", ["10", "20", "30", "40", "50", "60"], default=[])

# 4. 분석 모드 (카테고리 맵)
category_map = {
    "패션의류": {
        "여성의류": "50000000",
        "여성언더웨어/잠옷": "50000167",
        "남성의류": "50000001",
        "남성언더웨어/잠옷": "50000168",
        "아동의류": "50000002"
    },
    "패션잡화": {
        "신발": "50000003",
        "가방": "50000004",
        "지갑": "50000005",
        "벨트": "50000006",
        "선글라스/안경테": "50000007",
        "헤어액세서리": "50000008"
    },
    "화장품/미용": {
        "스킨케어": "50000009",
        "메이크업": "50000010",
        "헤어케어": "50000011",
        "바디케어": "50000012",
        "향수": "50000013",
        "네일케어": "50000014"
    },
    "디지털/가전": {
        "주방가전": "50000015",
        "생활가전": "50000016",
        "계절가전": "50000017",
        "영상가전": "50000018",
        "음향가전": "50000019",
        "PC/노트북": "50000020"
    },
    "가구/인테리어": {
        "침실가구": "50000021",
        "거실가구": "50000022",
        "주방가구": "50000023",
        "침구단품": "50000024",
        "커튼/블라인드": "50000025",
        "인테리어소품": "50000026"
    },
    "출산/육아": {
        "분유/기저귀/물티슈": "50000027",
        "유아동의류": "50000028",
        "유아동잡화": "50000029",
        "장난감/완구": "50000030",
        "임산부용품": "50000031",
        "유아외출용품": "50000032"
    },
    "식품": {
        "농산물": "50000033",
        "축산물": "50000034",
        "수산물": "50000035",
        "가공식품": "50000036",
        "건강식품": "50000037",
        "음료": "50000038"
    },
    "스포츠/레저": {
        "등산": "50000039",
        "캠핑": "50000040",
        "낚시": "50000041",
        "골프": "50000042",
        "자전거": "50000043",
        "헬스": "50000044"
    },
    "생활/건강": {
        "주방용품": "50000045",
        "생활용품": "50000046",
        "욕실용품": "50000047",
        "문구/사무용품": "50000048",
        "반려동물": "50000049",
        "공구": "50000050"
    },
    "여가/생활편의": {
        "국내여행/티켓": "50000051",
        "해외여행/티켓": "50000052",
        "문화/예매권": "50000053",
        "렌탈서비스": "50000054",
        "생활편의": "50000055"
    }
}

mode = st.radio("모드 선택", ["직접 입력", "실시간 핫 키워드"])

if mode == "실시간 핫 키워드":
    main_category = st.selectbox("📂 대분류를 선택하세요", list(category_map.keys()))
    sub_category_list = list(category_map[main_category].keys())
    sub_category = st.selectbox("🔍 하위 카테고리를 선택하세요", sub_category_list)
    selected_category_id = category_map[main_category][sub_category]
    st.info(f"✅ 현재 선택: {main_category} > {sub_category} (코드: {selected_category_id})")
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
            target_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
            body = {
                "startDate": target_date,
                "endDate": target_date,
                "timeUnit": "date",
                "category": str(selected_category_id)
            }
            if gender_code: body["gender"] = gender_code
            if target_ages: body["ages"] = target_ages
            
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                data = res.json()
                if "results" in data and data['results']:
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
                    
                    # --- 0~10점 지수 보정 로직 적용 ---
                    raw_score = (now_ratio / blog_count) * 100000
                    if raw_score > 0:
                        final_score = min(10.0, math.log10(raw_score + 1) * 3)
                    else:
                        final_score = 0.0

                    results.append({
                        "키워드": kw,
                        "블루오션지수": round(final_score, 2),
                        "AI 제목 추천": generate_ai_titles(kw)[0], 
                        "상세보기": f"https://search.naver.com/search.naver?query={kw}"
                    })

            if results:
                df = pd.DataFrame(results).sort_values(by="블루오션지수", ascending=False)
                
                # --- 가이드 표 추가 ---
                st.markdown("### 💡 블루오션 지수 판독 가이드 (0~10 기준)")
                guide_data = {
                    "점수": ["8.0 ~ 10.0", "5.0 ~ 7.9", "3.0 ~ 4.9", "0.0 ~ 2.9"],
                    "등급": ["💎 다이아몬드", "✅ 골드", "⚠️ 실버", "❌ 레드"],
                    "의미": ["초특급 블루오션! 무조건 쓰세요.", "할만한 시장. 유입 보장!", "평범한 경쟁. 서브 키워드 필수.", "전쟁터. 상위 노출이 어렵습니다."]
                }
                st.table(pd.DataFrame(guide_data))
                
                st.markdown("---")
                
                # --- 색상 변경 그래프 적용 ---
                st.subheader("📈 키워드별 시장성 분석")
                fig = px.bar(
                    df, 
                    x='키워드', 
                    y='블루오션지수', 
                    color='블루오션지수', 
                    text='블루오션지수', 
                    range_y=[0, 10], 
                    color_continuous_scale='RdYlBu_r', # 파랑(고) -> 초록 -> 노랑 -> 빨강(저)
                    labels={'블루오션지수': '블루오션 점수'}
                )
                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig.update_coloraxes(showscale=True)
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📑 AI 전략 리포트")
                st.dataframe(df, column_config={"상세보기": st.column_config.LinkColumn("네이버 검색")}, use_container_width=True)

# 6. 본문 프롬프트 생성기 (기존 이모티콘 및 내용 보존)
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
 - 긴 문장이라도 한 줄에 공백포함 최대 60~70byte로 자연스럽게 끊어서 작성해줘. (블로그 모바일 화면으로 편하게 읽힐 수 있도록)
 - 본문 전체는 자연스러운 스토리텔링으로 한글 기준 약 3,500자로 맞춰줘.
 - 글 곳곳에 아래 이모티콘 중 5~6개 정도 활용해줘,
!(•̀ᴗ•́)و ̑̑ / (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ / (୨୧ ❛ᴗ❛)✧ / (୨୧ •͈ᴗ•͈) / (•̆ꈊ•̆ ) / (ꈍᴗꈍ)♡ / - ̗̀ෆ(˶'ᵕ'˶)ෆ ̖·- / ٩(*•̀ᴗ•́*)و / ٩( ᐢ-ᐢ )و / ٩(๑❛ᴗ❛๑)۶♡ / ٩(◕ᗜ◕)و / ദ്디( ¯꒳¯ ) / ☆٩(｡•ω<｡)﻿و / :) / :D / >_< / +ㅂ+ 
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
본문내용 입력"""

if st.button("📋 본문작성 프롬프트 생성"):
    if not m_key:
        st.warning("⚠️ 메인키워드를 입력하세요.")
    else:
        st.text_area("아래 내용을 복사해서 사용하세요!", value=final_prompt, height=300)
        st.success("✅ 프롬프트가 생성되었습니다!")
