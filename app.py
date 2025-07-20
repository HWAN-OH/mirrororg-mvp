# app.py
# 역할: 전체 워크플로우를 관리하고, 사용자 인터페이스를 렌더링합니다.
# 최종 버전: '요약 -> 분석' 2단계 프로세스를 실행합니다.

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
    "analysis_button": {"ko": "종합 분석 시작하기", "en": "Start Comprehensive Analysis"},
    "spinner_summary": {"ko": "1/4: 대화 내용 요약 중...", "en": "1/4: Summarizing chat log..."},
    "spinner_profile": {"ko": "2/4: 팀 프로필 분석 중...", "en": "2/4: Analyzing team profile..."},
    "spinner_timeline": {"ko": "3/4: 피로도 타임라인 분석 중...", "en": "3/4: Analyzing fatigue timeline..."},
    "spinner_network": {"ko": "4/4: 관계 네트워크 분석 중...", "en": "4/4: Analyzing relationship network..."},
    "analysis_complete": {"ko": "✅ 모든 분석이 완료되었습니다!", "en": "✅ Analysis complete!"},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "2. 진단 결과", "en": "2. Diagnostic Results"},
    "summary_header": {"ko": "대화록 요약", "en": "Chat Log Summary"},
    "tab_profile": {"ko": "**팀 프로필**", "en": "**Team Profile**"},
    "tab_fatigue": {"ko": "**피로도 변화**", "en": "**Fatigue Trajectory**"},
    "tab_network": {"ko": "**관계 네트워크**", "en": "**Relationship Network**"},
    "profile_warning": {"ko": "팀 프로필 데이터가 없습니다.", "en": "No team profile data available."},
    "fatigue_warning": {"ko": "피로도 타임라인 데이터가 없습니다.", "en": "No fatigue timeline data available."},
    "network_warning": {"ko": "네트워크 데이터를 생성할 수 없습니다.", "en": "Could not generate network data."},
    "raw_response_error": {"ko": "LLM이 유효한 JSON을 반환하지 않았습니다. 아래는 LLM의 원본 응답입니다.", "en": "The LLM did not return valid JSON. Below is the raw response from the LLM."}
}

# --- Page Config & Initialization ---
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state: st.session_state.lang = 'ko'
if 'results' not in st.session_state: st.session_state.results = {}

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
    # ... (Same as before)
    if not isinstance(network_data, dict) or 'nodes' not in network_data:
        st.warning(TEXTS["network_warning"][lang])
        if isinstance(network_data, str): st.code(network_data)
        return
    # ... (rest of the function is the same)
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
            file_content = uploaded_file.getvalue().decode("utf-8")
            chat_df = parsers.parse(file_content)

            if isinstance(chat_df, pd.DataFrame):
                detected_format = parsers.detect_format(file_content)
                st.success(TEXTS["parsing_success"][lang].format(count=len(chat_df), format=detected_format))
                
                if st.button(TEXTS["analysis_button"][lang]):
                    st.session_state.results = {} # Clear previous results
                    with st.spinner(TEXTS["spinner_summary"][lang]):
                        summary = analyzer.summarize_chat(chat_df)
                        st.session_state.results['summary'] = summary
                    
                    if isinstance(summary, str) and len(summary) > 10: # Check if summary is valid
                        with st.spinner(TEXTS["spinner_profile"][lang]):
                            st.session_state.results['profile'] = analyzer.analyze_profile(summary)
                        with st.spinner(TEXTS["spinner_timeline"][lang]):
                            st.session_state.results['timeline'] = analyzer.analyze_timeline(summary)
                        with st.spinner(TEXTS["spinner_network"][lang]):
                            st.session_state.results['network'] = analyzer.analyze_network(summary)
                        st.success(TEXTS["analysis_complete"][lang])
                    else:
                        st.error("Failed to generate a valid summary from the chat log.")

            else:
                st.error(TEXTS["parsing_error"][lang])
        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")

    # --- Display Results ---
    if st.session_state.results:
        st.header(TEXTS["results_header"][lang])
        
        with st.expander(TEXTS["summary_header"][lang]):
            st.markdown(st.session_state.results.get('summary', "No summary available."))

        tab1, tab2, tab3 = st.tabs([TEXTS["tab_profile"][lang], TEXTS["tab_fatigue"][lang], TEXTS["tab_network"][lang]])

        with tab1:
            profile_data = st.session_state.results.get('profile')
            if isinstance(profile_data, list):
                st.dataframe(pd.DataFrame(profile_data), use_container_width=True)
            else:
                st.warning(TEXTS["profile_warning"][lang])
                if isinstance(profile_data, str): st.code(profile_data)

        with tab2:
            timeline_data = st.session_state.results.get('timeline')
            if isinstance(timeline_data, dict) and 'error' not in timeline_data:
                try:
                    df = pd.DataFrame.from_dict(timeline_data, orient='index')
                    df.index = pd.to_datetime(df.index).strftime('%Y-%m-%d')
                    st.line_chart(df.sort_index())
                except Exception:
                    st.warning(TEXTS["fatigue_warning"][lang])
                    st.json(timeline_data)
            else:
                st.warning(TEXTS["fatigue_warning"][lang])
                if isinstance(timeline_data, str): st.code(timeline_data)

        with tab3:
            network_data = st.session_state.results.get('network')
            draw_network_graph(network_data, lang)
