import streamlit as st
import google.generativeai as genai
import analyzer
import pandas as pd

TEXTS = {
    "page_title": {"ko": "MirrorOrg MVP", "en": "MirrorOrg MVP"},
    "main_title": {"ko": "🪞 MirrorOrg MVP: 종합 팀 분석", "en": "🪞 MirrorOrg MVP: Comprehensive Team Analysis"},
    "main_description": {
        "ko": "'미러오알지 팀 분석 사례'에 기반한 다차원 협업 진단 도구입니다.\n**팀 채팅 기록(카카오톡, 슬랙 등)**을 업로드하여 챕터별 분석을 실행할 수 있습니다.",
        "en": "A multi-dimensional collaboration diagnostic tool based on the 'MirrorOrg Team Analysis Case Study'.\nUpload your **team chat history (e.g., KakaoTalk, Slack)** and run each analysis chapter independently."
    },
    "sidebar_header": {"ko": "설정", "en": "Settings"},
    "language_selector": {"ko": "언어", "en": "Language"},
    "api_key_error_title": {"ko": "API 키 설정 오류", "en": "API Key Configuration Error"},
    "api_key_error_body": {
        "ko": "앱 관리자가 설정한 API 키에 문제가 있습니다. Streamlit Cloud의 'Secrets' 설정을 확인해주세요.",
        "en": "There is an issue with the API key configured by the app administrator. Please check the 'Secrets' settings on Streamlit Cloud."
    },
    "upload_header": {"ko": "1. 채팅 기록 업로드", "en": "1. Upload Chat History"},
    "upload_info": {
        "ko": "팀 채팅 기록을 텍스트(.txt) 파일로 업로드하세요. 다양한 형식을 지원합니다.",
        "en": "Upload your team chat history as a text (.txt) file. Various formats are supported."
    },
    "file_uploader_label": {"ko": "분석할 .txt 파일을 선택하세요.", "en": "Choose a .txt file to analyze."},
    "chapter_header": {
        "ko": "2. 챕터별 분석 실행", "en": "2. Run Each Analysis Chapter"
    },
    "chapter1_btn": {"ko": "챕터 1: 종합 분석 보고서 생성", "en": "Chapter 1: Generate Comprehensive Report"},
    "chapter2_btn": {"ko": "챕터 2: 피로도 곡선 분석", "en": "Chapter 2: Analyze Fatigue Trajectory"},
    "chapter3_btn": {"ko": "챕터 3: 관계 네트워크 분석", "en": "Chapter 3: Analyze Relationship Network"},
    "spinner_report": {"ko": "보고서를 생성 중입니다...", "en": "Generating report..."},
    "spinner_fatigue": {"ko": "피로도 곡선 분석 중...", "en": "Analyzing fatigue trajectory..."},
    "spinner_network": {"ko": "관계 네트워크 분석 중...", "en": "Analyzing relationship network..."},
    "analysis_complete": {"ko": "✅ 분석이 완료되었습니다!", "en": "✅ Analysis complete!"},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "3. 분석 결과", "en": "3. Results"},
    "fatigue_title": {"ko": "3.1 피로도 변화 (Fatigue Trajectory)", "en": "3.1 Fatigue Trajectory"},
    "network_title": {"ko": "3.2 관계 네트워크 (Relationship Network)", "en": "3.2 Relationship Network"},
    "no_fatigue_data": {"ko": "피로도 곡선 데이터를 생성할 수 없습니다.", "en": "Fatigue trajectory data could not be generated."},
    "no_network_data": {"ko": "관계 네트워크 데이터를 생성할 수 없습니다.", "en": "Network data could not be generated."}
}

# 1. Page config
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

# 2. Sidebar (Language Switch)
with st.sidebar:
    st.header(TEXTS["sidebar_header"][st.session_state.lang])
    lang_choice = st.selectbox(
        label=f'{TEXTS["language_selector"]["en"]} / {TEXTS["language_selector"]["ko"]}',
        options=['한국어', 'English'],
        index=0 if st.session_state.lang == 'ko' else 1
    )
    st.session_state.lang = 'ko' if lang_choice == '한국어' else 'en'
lang = st.session_state.lang

# 3. API Key Config
api_configured = False
try:
    genai.configure(api_key=st.secrets["GOOGLE_AI_API_KEY"])
    api_configured = True
except (KeyError, AttributeError):
    st.error(TEXTS["api_key_error_title"][lang])
    st.warning(TEXTS["api_key_error_body"][lang])

# 4. Main UI
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

if api_configured:
    st.header(TEXTS["upload_header"][lang])
    st.info(TEXTS["upload_info"][lang])
    uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt")

    if uploaded_file:
        try:
            if 'uploaded_file_id' not in st.session_state or uploaded_file.file_id != st.session_state.uploaded_file_id:
                # 새 파일이면 모든 분석 결과 초기화
                st.session_state.report = None
                st.session_state.fatigue_data = None
                st.session_state.network_data = None
                st.session_state.uploaded_file_id = uploaded_file.file_id

            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")

            st.header(TEXTS["chapter_header"][lang])
            c1, c2, c3 = st.columns(3)

            # 챕터 1: 종합 분석 보고서
            with c1:
                if st.button(TEXTS["chapter1_btn"][lang], use_container_width=True):
                    with st.spinner(TEXTS["spinner_report"][lang]):
                        st.session_state.report = analyzer.generate_report(file_content, lang=lang)
                    st.toast(TEXTS["analysis_complete"][lang], icon="✅")

            # 챕터 2: 피로도 곡선
            with c2:
                if st.button(TEXTS["chapter2_btn"][lang], use_container_width=True):
                    with st.spinner(TEXTS["spinner_fatigue"][lang]):
                        st.session_state.fatigue_data = analyzer.analyze_fatigue_json(file_content, lang=lang)
                    st.toast(TEXTS["analysis_complete"][lang], icon="✅")

            # 챕터 3: 관계 네트워크
            with c3:
                if st.button(TEXTS["chapter3_btn"][lang], use_container_width=True):
                    with st.spinner(TEXTS["spinner_network"][lang]):
                        st.session_state.network_data = analyzer.analyze_network_json(file_content, lang=lang)
                    st.toast(TEXTS["analysis_complete"][lang], icon="✅")

            # 결과 출력 구간
            st.header(TEXTS["results_header"][lang])

            # --- 종합 보고서 ---
            if st.session_state.get('report'):
                st.markdown(st.session_state.report, unsafe_allow_html=True)
                st.divider()

            # --- 피로도 곡선 ---
            st.subheader(TEXTS["fatigue_title"][lang])
            fatigue_data = st.session_state.get('fatigue_data')
            if fatigue_data and isinstance(fatigue_data, list):
                try:
                    lines = []
                    for item in fatigue_data:
                        for d in item["fatigue_timeline"]:
                            lines.append({"name": item["name"], "date": d["date"], "score": d["score"]})
                    df = pd.DataFrame(lines)
                    chart_data = df.pivot(index="date", columns="name", values="score")
                    st.line_chart(chart_data)
                except Exception as e:
                    st.error(f"{TEXTS['no_fatigue_data'][lang]}: {e}")
            elif fatigue_data and "raw_response" in fatigue_data:
                st.warning("LLM 원본 응답(raw):")
                st.code(fatigue_data["raw_response"])
                st.info(TEXTS["no_fatigue_data"][lang])
            else:
                st.info(TEXTS["no_fatigue_data"][lang])

            # --- 네트워크 ---
            st.subheader(TEXTS["network_title"][lang])
            network_data = st.session_state.get('network_data')
            if network_data and isinstance(network_data, list):
                try:
                    import networkx as nx
                    import matplotlib.pyplot as plt
                    G = nx.Graph()
                    for link in network_data:
                        G.add_edge(link["source"], link["target"], weight=link["strength"])
                    fig, ax = plt.subplots()
                    pos = nx.spring_layout(G)
                    nx.draw(G, pos, with_labels=True, ax=ax, node_color='lightblue', edge_color='gray')
                    st.pyplot(fig)
                except Exception as e:
                    st.error(f"{TEXTS['no_network_data'][lang]}: {e}")
            elif network_data and "raw_response" in network_data:
                st.warning("LLM 원본 응답(raw):")
                st.code(network_data["raw_response"])
                st.info(TEXTS["no_network_data"][lang])
            else:
                st.info(TEXTS["no_network_data"][lang])

        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")
else:
    st.warning("API 미설정: 관리자에게 문의하세요.")
