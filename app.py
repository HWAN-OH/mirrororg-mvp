# app.py
import streamlit as st
import google.generativeai as genai
import analyzer
import pandas as pd

TEXTS = {
    "page_title": {"ko": "MirrorOrg MVP", "en": "MirrorOrg MVP"},
    "main_title": {"ko": "🪞 MirrorOrg MVP: 종합 팀 분석", "en": "🪞 MirrorOrg MVP: Comprehensive Team Analysis"},
    "main_description": {
        "ko": "'미러오알지 팀 분석 사례'에 기반한 다차원 협업 진단 도구입니다.\n**팀 채팅 기록(카카오톡, 슬랙 등)**을 업로드하여 종합 분석 보고서를 생성합니다.",
        "en": "A multi-dimensional collaboration diagnostic tool based on the 'MirrorOrg Team Analysis Case Study'.\nUpload your **team chat history (e.g., KakaoTalk, Slack)** to generate a comprehensive analysis report."
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
    "analysis_button": {"ko": "종합 분석 보고서 생성하기", "en": "Generate Comprehensive Report"},
    "spinner_analysis": {"ko": "보고서를 생성 중입니다... (1~2분 소요될 수 있습니다)", "en": "Generating report... (This may take 1-2 minutes)"},
    "analysis_complete": {"ko": "✅ 보고서 생성이 완료되었습니다!", "en": "✅ Report generation complete!"},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "2. 종합 분석 보고서", "en": "2. Comprehensive Analysis Report"},
    "fatigue_title": {"ko": "3.1 피로도 변화 (Fatigue Trajectory)", "en": "3.1 Fatigue Trajectory"},
    "network_title": {"ko": "3.2 관계 네트워크 (Relationship Network)", "en": "3.2 Relationship Network"},
    "no_fatigue_data": {"ko": "피로도 곡선 데이터를 생성할 수 없습니다.", "en": "Fatigue trajectory data could not be generated."},
    "no_network_data": {"ko": "관계 네트워크 데이터를 생성할 수 없습니다.", "en": "Network data could not be generated."}
}

st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state: st.session_state.lang = 'ko'
if 'report' not in st.session_state: st.session_state.report = None

# --- Sidebar (Language Switch) ---
with st.sidebar:
    st.header(TEXTS["sidebar_header"][st.session_state.lang])
    lang_choice = st.selectbox(
        label=f'{TEXTS["language_selector"]["en"]} / {TEXTS["language_selector"]["ko"]}',
        options=['한국어', 'English'],
        index=0 if st.session_state.lang == 'ko' else 1
    )
    st.session_state.lang = 'ko' if lang_choice == '한국어' else 'en'
lang = st.session_state.lang

# --- API Key Configuration ---
api_configured = False
try:
    genai.configure(api_key=st.secrets["GOOGLE_AI_API_KEY"])
    api_configured = True
except (KeyError, AttributeError):
    st.error(TEXTS["api_key_error_title"][lang])
    st.warning(TEXTS["api_key_error_body"][lang])

# --- Main App UI ---
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

if api_configured:
    st.header(TEXTS["upload_header"][lang])
    st.info(TEXTS["upload_info"][lang])
    uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt")

    if uploaded_file:
        try:
            # Clear previous report when a new file is uploaded
            if 'uploaded_file_id' not in st.session_state or uploaded_file.file_id != st.session_state.uploaded_file_id:
                st.session_state.report = None
                st.session_state.uploaded_file_id = uploaded_file.file_id

            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")
            
            if st.button(TEXTS["analysis_button"][lang]):
                with st.spinner(TEXTS["spinner_analysis"][lang]):
                    st.session_state.report = analyzer.generate_report(file_content, lang=lang)
                st.success(TEXTS["analysis_complete"][lang])
        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")
    else:
        st.session_state.report = None
        st.session_state.uploaded_file_id = None

    # --- Display Report ---
    if st.session_state.report:
        st.header(TEXTS["results_header"][lang])
        st.markdown("---")
        st.markdown(st.session_state.report, unsafe_allow_html=True)

        # --- Fatigue Trajectory Chart ---
        st.subheader(TEXTS["fatigue_title"][lang])
        fatigue_data = analyzer.analyze_fatigue_json(file_content, lang=lang)
        if fatigue_data and isinstance(fatigue_data, list):
            lines = []
            for item in fatigue_data:
                for d in item["fatigue_timeline"]:
                    lines.append({"name": item["name"], "date": d["date"], "score": d["score"]})
            df = pd.DataFrame(lines)
            chart_data = df.pivot(index="date", columns="name", values="score")
            st.line_chart(chart_data)
        else:
            st.info(TEXTS["no_fatigue_data"][lang])

        # --- Relationship Network ---
        st.subheader(TEXTS["network_title"][lang])
        network_data = analyzer.analyze_network_json(file_content, lang=lang)
        if network_data and isinstance(network_data, list):
            import networkx as nx
            import matplotlib.pyplot as plt
            G = nx.Graph()
            for link in network_data:
                G.add_edge(link["source"], link["target"], weight=link["strength"])
            fig, ax = plt.subplots()
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, ax=ax, node_color='lightblue', edge_color='gray')
            st.pyplot(fig)
        else:
            st.info(TEXTS["no_network_data"][lang])
