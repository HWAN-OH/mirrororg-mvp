# app.py
# 역할: 전체 워크플로우를 관리하고, 텍스트와 데이터를 결합하여 최종 보고서를 렌더링합니다.
# 최종 버전: AI가 생성한 텍스트와 앱이 생성한 그래프를 결합하여 하나의 완성된 보고서를 출력합니다.

import streamlit as st
import pandas as pd
import google.generativeai as genai
from pyvis.network import Network
import streamlit.components.v1 as components

# We no longer need a separate parser file.
import analyzer

# --- TEXTS 딕셔너리는 이전과 동일 (생략) ---
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
    "spinner_data": {"ko": "1/2: 시각화를 위한 데이터 추출 중...", "en": "1/2: Extracting data for visualizations..."},
    "spinner_report": {"ko": "2/2: 보고서 텍스트 작성 중...", "en": "2/2: Writing report narrative..."},
    "analysis_complete": {"ko": "✅ 보고서 생성이 완료되었습니다!", "en": "✅ Report generation complete!"},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "2. 종합 분석 보고서", "en": "2. Comprehensive Analysis Report"},
    "raw_response_error": {"ko": "LLM이 유효한 데이터를 반환하지 않았습니다. 아래는 LLM의 원본 응답입니다.", "en": "The LLM did not return valid data. Below is the raw response from the LLM."}
}

# --- Page Config & Initialization ---
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state: st.session_state.lang = 'ko'
if 'report_text' not in st.session_state: st.session_state.report_text = None
if 'graph_data' not in st.session_state: st.session_state.graph_data = None

# --- Sidebar ---
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

# --- UI Rendering Functions ---
def draw_network_graph(network_data):
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", notebook=True, directed=False)
    color_map = {"high_risk": "#FF4136", "medium_risk": "#FF851B", "potential_risk": "#FFDC00", "stable": "#DDDDDD"}
    for node in network_data.get('nodes', []): net.add_node(node.get('id'), label=node.get('label'), size=25)
    for edge in network_data.get('edges', []):
        edge_type = edge.get('type', 'stable')
        net.add_edge(edge.get('from'), edge.get('to'), color=color_map.get(edge_type, "#DDDDDD"), width=4 if edge_type == 'high_risk' else 2)
    try:
        net.save_graph("network_graph.html")
        with open("network_graph.html", 'r', encoding='utf-8') as f: html_content = f.read()
        components.html(html_content, height=620, scrolling=True)
    except Exception as e: st.error(f"Error rendering network graph: {e}")

# --- Main App UI ---
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

if api_configured:
    st.header(TEXTS["upload_header"][lang])
    st.info(TEXTS["upload_info"][lang])
    uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt")

    if uploaded_file:
        try:
            if 'uploaded_file_id' not in st.session_state or uploaded_file.file_id != st.session_state.uploaded_file_id:
                st.session_state.report_text = None
                st.session_state.graph_data = None
                st.session_state.uploaded_file_id = uploaded_file.file_id

            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다. 이제 분석 버튼을 눌러주세요.")
            
            if st.button(TEXTS["analysis_button"][lang]):
                with st.spinner(TEXTS["spinner_data"][lang]):
                    st.session_state.graph_data = analyzer.generate_graph_data(file_content)
                with st.spinner(TEXTS["spinner_report"][lang]):
                    st.session_state.report_text = analyzer.generate_report_text(file_content, lang=lang)
                st.success(TEXTS["analysis_complete"][lang])

        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")
    else:
        st.session_state.report_text = None
        st.session_state.graph_data = None
        st.session_state.uploaded_file_id = None

    # --- Display Report ---
    if st.session_state.report_text and st.session_state.graph_data:
        st.header(TEXTS["results_header"][lang])
        st.markdown("---")

        # Split the report text to inject visualizations
        report_parts = st.session_state.report_text.split("---")
        graph_data = st.session_state.graph_data

        # Check if graph_data is valid
        if isinstance(graph_data, dict):
            # Render part 1: Overview
            st.markdown(report_parts[0], unsafe_allow_html=True)

            # Render part 2: Diagnosis with Profile Table
            if len(report_parts) > 1:
                st.markdown(report_parts[1], unsafe_allow_html=True)
                profile_data = graph_data.get('profile_data')
                if isinstance(profile_data, list):
                    st.dataframe(pd.DataFrame(profile_data), use_container_width=True)
                else:
                    st.error(TEXTS["raw_response_error"][lang])
                    st.code(profile_data, language=None)

            # Render part 3: Prediction with Timeline and Network
            if len(report_parts) > 2:
                st.markdown(report_parts[2], unsafe_allow_html=True)
                
                # Fatigue Timeline
                timeline_data = graph_data.get('timeline_data')
                if isinstance(timeline_data, dict):
                    try:
                        df = pd.DataFrame.from_dict(timeline_data, orient='index')
                        df.index = pd.to_datetime(df.index).strftime('%Y-%m-%d')
                        st.line_chart(df.sort_index())
                    except Exception:
                        st.error(TEXTS["raw_response_error"][lang])
                        st.json(timeline_data)
                
                # Relationship Network
                network_data = graph_data.get('network_data')
                if isinstance(network_data, dict):
                    draw_network_graph(network_data)
                else:
                    st.error(TEXTS["raw_response_error"][lang])
                    st.code(network_data, language=None)

            # Render part 4: Conclusion
            if len(report_parts) > 3:
                st.markdown("---")
                st.markdown(report_parts[3], unsafe_allow_html=True)
        
        else: # If graph_data itself is not a dict (i.e., an error string)
            st.error(TEXTS["raw_response_error"][lang])
            st.code(graph_data, language=None)
            st.markdown("---")
            st.markdown("### 보고서 텍스트 (참고)")
            st.markdown(st.session_state.report_text)
