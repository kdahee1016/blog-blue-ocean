import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="오키랑의 블로그 초안 메이커", layout="centered")

st.title("📝 오키랑의 블로그 초안 생성기")
st.caption("직접 겪은 에피소드를 적어주시면 자연스러운 감성으로 맛있게 버무려 드려요! ✨")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.info("API 키가 작동하지 않으면 새로 발급받아 1분 뒤 시도하세요.")

# 메인 화면: 입력 폼
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        main_k = st.text_input("📍 메인 키워드 (4회 반복)", placeholder="예: OO맛집")
    with col2:
        sub_k1 = st.text_input("🔍 서브 키워드 1", placeholder="예: 아이랑 가기 좋은")
        
    col3, col4 = st.columns(2)
    with col3:
        sub_k2 = st.text_input("🔍 서브 키워드 2", placeholder="예: 무한리필")
    with col4:
        sub_k3 = st.text_input("🔍 서브 키워드 3", placeholder="예: 내돈내산")

    st.subheader("📸 나의 실제 경험 (흐름 적기)")
    user_experience = st.text_area(
        "블로그에 꼭 넣고 싶은 내용이나 흐름을 자유롭게 적어주세요.",
        placeholder="예: 우리 아들이 OO를 평소 안 먹는데 여기서 2인분 먹음 / 주차장이 넓어서 편했음 등",
        height=200
    )

# 실행 버튼
if st.button("✨ 내 경험 반영해서 원고 만들기"):
    if not api_key:
        st.error("API 키를 입력해주세요!")
    elif not main_k:
        st.warning("메인 키워드는 필수입니다.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # --- [개선] 사용 가능한 모델 리스트 확보 ---
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # 429 에러(할당량 0)를 피하기 위해 1.5-flash를 1순위로 시도
            priority_list = [
                "models/gemini-1.5-flash", 
                "models/gemini-flash-latest", 
                "models/gemini-2.0-flash"
            ]
            
            target_model_name = None
            for m_name in priority_list:
                if m_name in available_models:
                    target_model_name = m_name
                    break
            
            if not target_model_name and available_models:
                target_model_name = available_models[0]
            
            if not target_model_name:
                st.error("사용 가능한 모델을 찾을 수 없습니다.")
                st.stop()
            
            # 여기서 model 변수를 확실하게 정의합니다!
            model = genai.GenerativeModel(target_model_name)
            # ------------------------------------------

            with st.spinner(f"[{target_model_name}] 모델로 글을 짓는 중입니다..."):
                prompt = f"""
                주제: {main_k} (서브: {sub_k1}, {sub_k2}, {sub_k3})
                
                [블로거의 실제 경험 내용]
                {user_experience}

                네이버 블로그 원고를 작성해줘. 아래 조건을 엄격히 지켜줘:

                1. 키워드: '{main_k}' 4회, '{sub_k1}', '{sub_k2}', '{sub_k3}' 각 1회 자연스럽게 포함.
                2. 제목: 클릭율 높이는 제목 3개 추천.
                3. 말투: 30대 여성의 일기체 (~했음, ~했다, 혼잣말). 친근하고 편안하게.
                4. 가독성: 한 줄에 공백포함 최대 60-70byte 내외로 끊어서 작성(모바일 최적화).
                5. 이모티콘: 리스트 중 5~6개 필수 사용 !(•̀ᴗ•́)و ̑̑ , (*ᴗ͈ˬᴗ͈)ꕤ*.ﾟ , (୨୧ ❛ᴗ❛)✧ , (୨୧ •͈ᴗ•͈) , (•̆ꈊ•̆ ) , (ꈍᴗꈍ)♡ ,  ̗̀ෆ(˶'ᵕ'˶)ෆ ̖́- , ٩(*•̀ᴗ•́*)و /,٩( ᐢ-ᐢ ), / ٩(๑❛ᴗ❛๑)۶♡ , ٩(◕ᗜ◕)و , ദ്ദി( ¯꒳¯ ) , ☆٩(｡•ω<｡)﻿و , :) , :D , >_< , +ㅂ+ 등).
                6. 이모지: 문맥에 맞는 그림 이모지 8개 내외 활용.
                7. AI가 쓴 것 같지 않도록 작성하되 중복문서 걸리지 않게 이중검토
                8. 분량: 한글 기준 약 3,500자 내외로 아주 상세하게.
                9. 상위노출SEO 반영해서 내용 작성
                10. 요약문: 최상단에 240~280byte 요약문 포함.
                """
                
                response = model.generate_content(prompt)
                full_text = response.text
                
                st.success("🎉 나만의 원고 작성이 완료되었습니다!")
                st.divider()
                
                st.subheader("📋 생성된 블로그 원고")
                st.text_area("결과물", value=full_text, height=600)
                
                st.download_button(
                    label="💾 텍스트 파일로 다운로드",
                    data=full_text,
                    file_name=f"{main_k}_경험담원고.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            # 에러 발생 시 상세 내용을 찍어줍니다.
            st.error(f"오류가 발생했습니다: {str(e)}")
            if "quota" in str(e).lower():
                st.warning("⚠️ 할당량 부족 에러입니다. 1분 뒤 다시 시도하거나, 1.5-flash 모델이 활성화될 때까지 기다려주세요.")
