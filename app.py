# app.py
# 역할: 전체 워크플로우를 관리하고, 사용자 인터페이스를 렌더링합니다.

import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import google.generativeai as genai

# Import new custom modules
import parsers
import analyzer

# --- [Delta] Centralized Text Management for Multilingual Support ---
# This dictionary holds all UI text for easy translation and management.
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
    "analysis_button": {"ko": "종합 분석 시작하기 🚀", "en": "Start Comprehensive Analysis 🚀"},
    "spinner_analysis": {"ko": "종합 분석을 진행 중입니다...", "en": "Running comprehensive analysis..."},
    "analysis_complete": {"ko": "✅ 모든 분석이 완료되었습니다! 아래 탭에서 결과를 확인하세요.", "en": "✅ Analysis complete! Check the results in the tabs below."},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "2. 진단 결과", "en": "2. Diagnostic Results"},
    "tab_profile": {"ko": "**팀 프로필 (진단)**", "en": "**Team Profile (Diagnosis)**"},
    "tab_fatigue": {"ko": "**피로도 변화 (예측)**", "en": "**Fatigue Trajectory (Prediction)**"},
    "tab_network": {"ko": "**관계 네트워크 (예측)**", "en": "**Relationship Network (Prediction)**"},
    "profile_subheader": {"ko": "정체성 계수 맵", "en": "Identity Coefficient Map"},
    "profile_info": {"ko": "팀원들의 성향과 역할을 파악하여 팀의 전체적인 구성을 진단합니다.", "en": "Diagnoses the overall team composition by identifying member traits and roles."},
    "profile_error": {"ko": "프로필 데이터를 표시하는 중 오류가 발생했습니다", "en": "An error occurred while displaying profile data"},
    "profile_warning": {"ko": "팀 프로필 데이터가 없습니다.", "en": "No team profile data available."},
    "fatigue_subheader": {"ko": "피로도 시계열 그래프", "en": "Fatigue Timeline Graph"},
    "fatigue_info": {"ko": "시간에 따른 팀원들의 감정적, 업무적 소진 상태의 변화를 예측합니다.", "en": "Predicts the changes in team members' emotional and professional burnout over time."},
    "fatigue_error": {"ko": "타임라인 데이터를 표시하는 중 오류가 발생했습니다", "en": "An error occurred while displaying timeline data"},
    "fatigue_warning": {"ko": "피로도 타임라인 데이터가 없습니다.", "en": "No fatigue timeline data available."},
    "network_subheader": {"ko": "갈등 네트워크 맵", "en": "Conflict Network Map"},
    "network_info": {"ko": "팀원 간 상호작용의 질을 분석하여 잠재적 갈등 및 협력 관계를 예측합니다. (그래프는 마우스로 조작 가능합니다)", "en": "Predicts potential conflicts and collaborations by analyzing the quality of interactions. (The graph is interactive)."},
    "network_error": {"ko": "네트워크 그래프를 렌더링하는 중 오류가 발생했습니다", "en": "Error rendering network graph"},
    "network_warning": {"ko": "네트워크 데이터를 생성할 수 없습니다.", "en": "Could not generate network data."},
    "col_name": {"ko": "이름", "en": "Name"},
    "col_emotion": {"ko": "감정 계수", "en": "Emotion Score"},
    "col_cognition": {"ko": "사고 계수", "en": "Cognition Score"},
    "col_expression": {"ko": "표현 계수", "en": "Expression Score"},
    "col_value": {"ko": "가치 계수", "en": "Value Score"},
    "col_bias": {"ko": "편향 계수", "en": "Bias Score"},
    "col_role": {"ko": "핵심 역할", "en": "Core Role"},
}

# --- Page Config & Initialization ---
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = {}
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

# --- Sidebar ---
with st.sidebar:
    st.header(TEXTS["sidebar_header"][st.session_state.lang])
    lang_choice = st.selectbox(
        label=f'{TEXTS["language_selector"]["en"]} / {TEXTS["language_selector"]["ko"]}',
        options=['한국어', 'English'],
        index=0 if st.session_state.lang == 'ko' else 1, key='lang_selector'
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

def display_results(lang):
    st.header(TEXTS["results_header"][lang])
    tab_titles = [TEXTS["tab_profile"][lang], TEXTS["tab_fatigue"][lang], TEXTS["tab_network"][lang]]
    tab1, tab2, tab3 = st.tabs(tab_titles)

    with tab1:
        st.subheader(TEXTS["profile_subheader"][lang])
        st.info(TEXTS["profile_info"][lang])
        profile_data = st.session_state.analysis_result.get('profile')
        if profile_data:
            try:
                profile_df = pd.DataFrame(profile_data)
                if not profile_df.empty:
                    # More robust renaming
                    rename_map = {
                        profile_df.columns[0]: TEXTS['col_name'][lang],
                        "emotion_score": TEXTS['col_emotion'][lang], "cognition_score": TEXTS['col_cognition'][lang],
                        "expression_score": TEXTS['col_expression'][lang], "value_score": TEXTS['col_value'][lang],
                        "bias_score": TEXTS['col_bias'][lang], "core_role": TEXTS['col_role'][lang],
                    }
                    # Only rename columns that actually exist in the DataFrame
                    actual_rename_map = {k: v for k, v in rename_map.items() if k in profile_df.columns}
                    profile_df.rename(columns=actual_rename_map, inplace=True)
                st.dataframe(profile_df, use_container_width=True)
            except Exception as e:
                st.error(f"{TEXTS['profile_error'][lang]}: {e}")
                st.json(profile_data)
        else:
            st.warning(TEXTS["profile_warning"][lang])

    with tab2:
        st.subheader(TEXTS["fatigue_subheader"][lang])
        st.info(TEXTS["fatigue_info"][lang])
        timeline_data = st.session_state.analysis_result.get('timeline')
        if timeline_data:
            try:
                timeline_df = pd.DataFrame.from_dict(timeline_data, orient='index')
                timeline_df.index = pd.to_datetime(timeline_df.index).strftime('%Y-%m-%d')
                timeline_df = timeline_df.sort_index()
                st.line_chart(timeline_df)
            except Exception as e:
                st.error(f"{TEXTS['fatigue_error'][lang]}: {e}")
                st.json(timeline_data)
        else:
            st.warning(TEXTS["fatigue_warning"][lang])
    
    with tab3:
        st.subheader(TEXTS["network_subheader"][lang])
        st.info(TEXTS["network_info"][lang])
        network_data = st.session_state.analysis_result.get('network')
        if network_data:
            draw_network_graph(network_data, lang)
        else:
            st.warning(TEXTS["network_warning"][lang])

# --- Main App Logic ---
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

if api_configured:
    st.header(TEXTS["upload_header"][lang])
    st.info(TEXTS["upload_info"][lang])
    uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt", key="file_uploader")

    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            chat_df = parsers.parse(file_content)

            if isinstance(chat_df, pd.DataFrame):
                detected_format = parsers.detect_format(file_content)
                st.success(TEXTS["parsing_success"][lang].format(count=len(chat_df), format=detected_format))
                
                if st.button(TEXTS["analysis_button"][lang], key="start_analysis"):
                    with st.spinner(TEXTS["spinner_analysis"][lang]):
                        st.session_state.analysis_result = analyzer.run_full_analysis(chat_df)
                    st.success(TEXTS["analysis_complete"][lang])
            else:
                st.error(TEXTS["parsing_error"][lang])
        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")

    if st.session_state.analysis_result:
        display_results(lang)
