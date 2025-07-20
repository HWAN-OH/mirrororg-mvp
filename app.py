# app.py
# 역할: '분할 정복' 파이프라인을 실행하고, 최종 보고서를 렌더링합니다.
# 최종 버전: 1) 참여자 식별, 2) 종합 보고서 생성을 순차적으로 실행하여 안정성을 확보합니다.

import streamlit as st
import google.generativeai as genai

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
    "spinner_participants": {"ko": "1/2: 대화 참여자 식별 중...", "en": "1/2: Identifying participants..."},
    "spinner_report": {"ko": "2/2: 종합 보고서 생성 중... (1~2분 소요)", "en": "2/2: Generating comprehensive report... (takes 1-2 min)"},
    "analysis_complete": {"ko": "✅ 보고서 생성이 완료되었습니다!", "en": "✅ Report generation complete!"},
    "file_process_error": {"ko": "파일 처리 중 알 수 없는 오류가 발생했습니다", "en": "An unknown error occurred while processing the file"},
    "results_header": {"ko": "2. 종합 분석 보고서", "en": "2. Comprehensive Analysis Report"},
    "participant_error": {"ko": "대화 참여자를 식별하는 데 실패했습니다. LLM 응답:", "en": "Failed to identify participants. LLM Response:"}
}

# --- Page Config & Initialization ---
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state: st.session_state.lang = 'ko'
if 'report' not in st.session_state: st.session_state.report = None

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
                st.session_state.report = None
                st.session_state.uploaded_file_id = uploaded_file.file_id

            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")
            
            if st.button(TEXTS["analysis_button"][lang]):
                participants = None
                with st.spinner(TEXTS["spinner_participants"][lang]):
                    participants = analyzer.get_participants(file_content)
                
                if isinstance(participants, list):
                    with st.spinner(TEXTS["spinner_report"][lang]):
                        st.session_state.report = analyzer.generate_report(file_content, participants, lang=lang)
                    st.success(TEXTS["analysis_complete"][lang])
                else:
                    st.error(TEXTS["participant_error"][lang])
                    st.code(participants, language=None) # Show the raw error response

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
