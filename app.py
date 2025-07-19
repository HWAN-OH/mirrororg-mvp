# app.py
# 역할: 전체 워크플로우를 관리하고, 사용자 인터페이스를 렌더링합니다.
# 최종 버전: 각 분석을 개별적으로 실행하여 안정성과 사용자 경험을 개선합니다.

import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import google.generativeai as genai

import parsers
import analyzer

# --- TEXTS 딕셔너리는 이전과 동일 (생략) ---
TEXTS = {
    "page_title": {"ko": "MirrorOrg MVP", "en": "MirrorOrg MVP"},
    "main_title": {"ko": "🪞 MirrorOrg MVP: 종합 팀 분석", "en": "🪞 MirrorOrg MVP: Comprehensive Team Analysis"},
    "main_description": {
        "ko": "'미러오알지 팀 분석 사례'에 기반한 다차원 협업 진단 도구입니다.\n**팀 채팅 기록(카카오톡, 슬랙 등)**을 업로드하여 팀 프로필, 피로도 변화, 관계 네트워크를 종합적으로 진단합니다.",
        "en": "A multi-dimensional collaboration diagnostic tool based on the 'MirrorOrg Team Analysis Case Study'.\nUpload your **team chat history (e.g., KakaoTalk, Slack)** to diagnose Team Profile, Fatigue Trajectory, and Relationship Network."
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
        "ko": "팀 채팅 기록을 텍스트(.txt) 파일로 업로드하세요. 현재 **카카오톡 대화 형식**에 최적화되어 있습니다.",
        "en": "Upload your team chat history as a text (.txt) file. Currently optimized for the **KakaoTalk chat format**."
    },
    "file_uploader_label": {"ko": "분석할 .txt 파일을 선택하세요.", "en": "Choose a .txt file to analyze."},
    "parsing_success": {"ko": "파일 파싱 성공! {count}개의 메시지를 발견했습니다. ({format} 형식)", "en": "File parsed successfully! Found {count} messages. (Format: {format})"},
    "parsing_error": {"ko": "지원하지 않는 파일 형식이거나 파일이 손상되었을 수 있습니다.", "en": "The file format is not supported or the file may be corrupted."},
    "analysis_button": {"ko": "{analysis_type} 분석하기", "en": "Analyze {analysis_type}"},
    "spinner_analysis": {"ko": "{analysis_type} 분석 중...", "en": "Analyzing {analysis_type}..."},
    "analysis_complete": {"ko": "✅ 분석이 완료되었습니다!", "en": "✅ Analysis complete!"},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "2. 진단 결과", "en": "2. Diagnostic Results"},
    "tab_profile": {"ko": "**팀 프로필 (진단)**", "en": "**Team Profile (Diagnosis)**"},
    "tab_fatigue": {"ko": "**피로도 변화 (예측)**", "en": "**Fatigue Trajectory (Prediction)**"},
    "tab_network": {"ko": "**관계 네트워크 (예측)**", "en": "**Relationship Network (Prediction)**"},
    "profile_subheader": {"ko": "정체성 계수 맵", "en": "Identity Coefficient Map"},
    "profile_info": {"ko": "팀원들의 성향과 역할을 파악하여 팀의 전체적인 구성을 진단합니다.", "en": "Diagnoses the overall team composition by identifying member traits and roles."},
    "profile_error": {"ko": "프로필 데이터를 표시하는 중 오류가 발생했습니다", "en": "An error occurred while displaying profile data"},
    "profile_warning": {"ko": "팀 프로필 데이터가 없습니다. 분석 버튼을 눌러주세요.", "en": "No team profile data. Please press the analyze button."},
    "fatigue_subheader": {"ko": "피로도 시계열 그래프", "en": "Fatigue Timeline Graph"},
    "fatigue_info": {"ko": "시간에 따른 팀원들의 감정적, 업무적 소진 상태의 변화를 예측합니다.", "en": "Predicts the changes in team members' emotional and professional burnout over time."},
    "fatigue_error": {"ko": "타임라인 데이터를 표시하는 중 오류가 발생했습니다", "en": "An error occurred while displaying timeline data"},
    "fatigue_warning": {"ko": "피로도 타임라인 데이터가 없습니다. 분석 버튼을 눌러주세요.", "en": "No fatigue timeline data. Please press the analyze button."},
    "network_subheader": {"ko": "갈등 네트워크 맵", "en": "Conflict Network Map"},
    "network_info": {"ko": "팀원 간 상호작용의 질을 분석하여 잠재적 갈등 및 협력 관계를 예측합니다. (그래프는 마우스로 조작 가능합니다)", "en": "Predicts potential conflicts and collaborations by analyzing the quality of interactions. (The graph is interactive)."},
    "network_error": {"ko": "네트워크 그래프를 렌더링하는 중 오류가 발생했습니다", "en": "Error rendering network graph"},
    "network_warning": {"ko": "네트워크 데이터를 생성할 수 없습니다. 분석 버튼을 눌러주세요.", "en": "Could not generate network data. Please press the analyze button."},
    "col_name": {"ko": "이름", "en": "Name"},
    "col_emotion": {"ko": "감정 계수", "en": "Emotion Score"},
    "col_cognition": {"ko": "사고 계수", "en": "Cognition Score"},
    "col_expression": {"ko": "표현 계수", "en": "Expression Score"},
    "col_value": {"ko": "가치 계수", "en": "Value Score"},
    "col_bias": {"ko": "편향 계수", "en": "Bias Score"},
    "col_role": {"ko": "핵심 역할", "en": "Core Role"},
    "raw_response_error": {"ko": "LLM이 유효한 JSON을 반환하지 않았습니다. 아래는 LLM의 원본 응답입니다.", "en": "The LLM did not return valid JSON. Below is the raw response from the LLM."}
}

# --- Page Config & Initialization ---
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'
# Initialize session state for each analysis type
if 'profile_result' not in st.session_state:
    st.session_state.profile_result = None
if 'timeline_result' not in st.session_state:
    st.session_state.timeline_result = None
if 'network_result' not in st.session_state:
    st.session_state.network_result = None
if 'chat_df' not in st.session_state:
    st.session_state.chat_df = None

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
def draw_network_graph(network_data, lang):
    if not network_data or 'nodes' not in network_data or 'edges' not in network_data:
        st.warning(TEXTS["network_warning"][lang])
        return
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", notebook=True, directed=False)
    color_map = {"high_risk": "#FF4136", "medium_risk": "#FF851B", "potential_risk": "#FFDC00", "stable": "#DDDDDD"}
    for node in network_data.get('nodes', []): net.add_node(node.get('id'), label=node.get('label'), size=25)
    for edge in network_data.get('edges', []):
        edge_type = edge.get('type', 'stable')
        net.add_edge(edge.get('from'), edge.get('to'), color=color_map.get(edge_type, "#DDDDDD"), width=4 if edge_type == 'high_risk' else 2)
    try:
        net.save_graph("network_graph.html")
        with open("network_graph.html", 'r', encoding='utf-8') as f: html_content = f.read()
        components.html(html_content, height=620)
    except Exception as e: st.error(f"{TEXTS['network_error'][lang]}: {e}")

# --- Main App UI ---
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

if api_configured:
    st.header(TEXTS["upload_header"][lang])
    st.info(TEXTS["upload_info"][lang])
    uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt")

    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.chat_df = parsers.parse(file_content)

            if isinstance(st.session_state.chat_df, pd.DataFrame):
                detected_format = parsers.detect_format(file_content)
                st.success(TEXTS["parsing_success"][lang].format(count=len(st.session_state.chat_df), format=detected_format))
            else:
                st.error(TEXTS["parsing_error"][lang])
                st.session_state.chat_df = None # Clear df on parsing error
        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")
            st.session_state.chat_df = None

    # --- Display Results in Tabs ---
    if st.session_state.chat_df is not None:
        st.header(TEXTS["results_header"][lang])
        tab_titles = [TEXTS["tab_profile"][lang], TEXTS["tab_fatigue"][lang], TEXTS["tab_network"][lang]]
        tab1, tab2, tab3 = st.tabs(tab_titles)

        with tab1:
            st.subheader(TEXTS["profile_subheader"][lang])
            st.info(TEXTS["profile_info"][lang])
            
            if st.button(TEXTS["analysis_button"][lang].format(analysis_type="팀 프로필")):
                with st.spinner(TEXTS["spinner_analysis"][lang].format(analysis_type="팀 프로필")):
                    st.session_state.profile_result = analyzer.analyze_profile(st.session_state.chat_df)
            
            profile_data = st.session_state.profile_result
            if isinstance(profile_data, list):
                try:
                    profile_df = pd.DataFrame(profile_data)
                    st.dataframe(profile_df, use_container_width=True)
                except Exception as e:
                    st.error(f"{TEXTS['profile_error'][lang]}: {e}")
            elif isinstance(profile_data, str):
                st.error(TEXTS["raw_response_error"][lang])
                st.code(profile_data, language=None)
            else:
                st.warning(TEXTS["profile_warning"][lang])

        with tab2:
            st.subheader(TEXTS["fatigue_subheader"][lang])
            st.info(TEXTS["fatigue_info"][lang])

            if st.button(TEXTS["analysis_button"][lang].format(analysis_type="피로도 변화")):
                with st.spinner(TEXTS["spinner_analysis"][lang].format(analysis_type="피로도 변화")):
                    st.session_state.timeline_result = analyzer.analyze_timeline(st.session_state.chat_df)

            timeline_data = st.session_state.timeline_result
            if isinstance(timeline_data, dict) and 'error' not in timeline_data:
                try:
                    timeline_df = pd.DataFrame.from_dict(timeline_data, orient='index')
                    timeline_df.index = pd.to_datetime(timeline_df.index).strftime('%Y-%m-%d')
                    st.line_chart(timeline_df.sort_index())
                except Exception as e:
                    st.error(f"{TEXTS['fatigue_error'][lang]}: {e}")
            elif isinstance(timeline_data, str):
                st.error(TEXTS["raw_response_error"][lang])
                st.code(timeline_data, language=None)
            else:
                st.warning(TEXTS["fatigue_warning"][lang])

        with tab3:
            st.subheader(TEXTS["network_subheader"][lang])
            st.info(TEXTS["network_info"][lang])

            if st.button(TEXTS["analysis_button"][lang].format(analysis_type="관계 네트워크")):
                with st.spinner(TEXTS["spinner_analysis"][lang].format(analysis_type="관계 네트워크")):
                    st.session_state.network_result = analyzer.analyze_network(st.session_state.chat_df)

            network_data = st.session_state.network_result
            if isinstance(network_data, dict) and 'nodes' in network_data:
                draw_network_graph(network_data, lang)
            elif isinstance(network_data, str):
                st.error(TEXTS["raw_response_error"][lang])
                st.code(network_data, language=None)
            else:
                st.warning(TEXTS["network_warning"][lang])
