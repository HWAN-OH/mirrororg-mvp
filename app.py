import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import json
from pyvis.network import Network
import streamlit.components.v1 as components
from datetime import datetime

# --- [Delta] Centralized Text Management for Multilingual Support ---
TEXTS = {
    # General UI
    "page_title": {"ko": "MirrorOrg MVP", "en": "MirrorOrg MVP"},
    "main_title": {"ko": "🪞 MirrorOrg MVP: 종합 팀 분석", "en": "🪞 MirrorOrg MVP: Comprehensive Team Analysis"},
    "main_description": {
        "ko": "'미러오알지 팀 분석 사례'에 기반한 다차원 협업 진단 도구입니다.\n**팀 채팅 기록(카카오톡, 슬랙 등)**을 업로드하여 팀 프로필, 피로도 변화, 관계 네트워크를 종합적으로 진단합니다.",
        "en": "A multi-dimensional collaboration diagnostic tool based on the 'MirrorOrg Team Analysis Case Study'.\nUpload your **team chat history (e.g., KakaoTalk, Slack)** to diagnose Team Profile, Fatigue Trajectory, and Relationship Network."
    },
    # Sidebar
    "sidebar_header": {"ko": "설정", "en": "Settings"},
    "language_selector": {"ko": "언어", "en": "Language"},
    "api_key_error_title": {"ko": "API 키 설정 오류", "en": "API Key Configuration Error"},
    "api_key_error_body": {
        "ko": "앱 관리자가 설정한 API 키에 문제가 있습니다. Streamlit Cloud의 'Secrets' 설정을 확인해주세요.",
        "en": "There is an issue with the API key configured by the app administrator. Please check the 'Secrets' settings on Streamlit Cloud."
    },
    # Main Content
    "upload_header": {"ko": "1. 채팅 기록 업로드", "en": "1. Upload Chat History"},
    "upload_info": {
        "ko": "팀 채팅 기록을 텍스트(.txt) 파일로 업로드하세요. 현재 **카카오톡 대화 형식**에 최적화되어 있습니다.\n**팁:** 카카오톡의 경우 '대화 내보내기' > '텍스트 파일만' 기능을 사용할 수 있습니다.",
        "en": "Upload your team chat history as a text (.txt) file. Currently optimized for the **KakaoTalk chat format**.\n**Tip:** For KakaoTalk, you can use the 'Export Chat' > 'Export Text Only' feature."
    },
    "file_uploader_label": {"ko": "분석할 .txt 파일을 선택하세요.", "en": "Choose a .txt file to analyze."},
    "parsing_success": {"ko": "파일 파싱 성공! {count}개의 메시지를 발견했습니다.", "en": "File parsed successfully! Found {count} messages."},
    "parsing_error": {"ko": "카카오톡 파일 형식을 인식할 수 없습니다. 파일을 확인해주세요.", "en": "Could not recognize the KakaoTalk file format. Please check the file."},
    "analysis_button": {"ko": "종합 분석 시작하기 🚀", "en": "Start Comprehensive Analysis 🚀"},
    "spinner_profile": {"ko": "1/3: 팀 프로필 분석 중...", "en": "1/3: Analyzing Team Profile..."},
    "spinner_timeline": {"ko": "2/3: 피로도 타임라인 분석 중...", "en": "2/3: Analyzing Fatigue Timeline..."},
    "spinner_network": {"ko": "3/3: 관계 네트워크 분석 중...", "en": "3/3: Analyzing Relationship Network..."},
    "analysis_complete": {"ko": "✅ 모든 분석이 완료되었습니다! 아래 탭에서 결과를 확인하세요.", "en": "✅ Analysis complete! Check the results in the tabs below."},
    "file_process_error": {"ko": "파일 처리 중 오류 발생", "en": "Error processing file"},
    # API Errors
    "api_parse_error": {"ko": "API 응답을 파싱하는 데 실패했습니다. 원본 응답", "en": "Failed to parse API response. Original response"},
    "api_call_error": {"ko": "API 호출 중 오류 발생", "en": "Error during API call"},
    # Results
    "results_header": {"ko": "2. 진단 결과", "en": "2. Diagnostic Results"},
    "tab_profile": {"ko": "**팀 프로필 (진단)**", "en": "**Team Profile (Diagnosis)**"},
    "tab_fatigue": {"ko": "**피로도 변화 (예측)**", "en": "**Fatigue Trajectory (Prediction)**"},
    "tab_network": {"ko": "**관계 네트워크 (예측)**", "en": "**Relationship Network (Prediction)**"},
    "profile_subheader": {"ko": "정체성 계수 맵 (Identity Coefficient Map)", "en": "Identity Coefficient Map"},
    "profile_info": {"ko": "팀원들의 성향과 역할을 파악하여 팀의 전체적인 구성을 진단합니다.", "en": "Diagnoses the overall team composition by identifying member traits and roles."},
    "profile_error": {"ko": "프로필 데이터를 표시할 수 없습니다", "en": "Could not display profile data"},
    "profile_warning": {"ko": "팀 프로필 데이터가 없습니다.", "en": "No team profile data available."},
    "fatigue_subheader": {"ko": "피로도 시계열 그래프 (Fatigue Timeline)", "en": "Fatigue Timeline Graph"},
    "fatigue_info": {"ko": "시간에 따른 팀원들의 감정적, 업무적 소진 상태의 변화를 예측합니다.", "en": "Predicts the changes in team members' emotional and professional burnout over time."},
    "fatigue_error": {"ko": "타임라인 데이터를 표시할 수 없습니다", "en": "Could not display timeline data"},
    "fatigue_warning": {"ko": "피로도 타임라인 데이터가 없습니다.", "en": "No fatigue timeline data available."},
    "network_subheader": {"ko": "갈등 네트워크 맵 (Conflict Network Map)", "en": "Conflict Network Map"},
    "network_info": {"ko": "팀원 간 상호작용의 질을 분석하여 잠재적 갈등 및 협력 관계를 예측합니다. (그래프는 마우스로 조작 가능합니다)", "en": "Predicts potential conflicts and collaborations by analyzing the quality of interactions. (The graph is interactive)."},
    "network_error": {"ko": "네트워크 그래프를 렌더링하는 중 오류 발생", "en": "Error rendering network graph"},
    "network_warning": {"ko": "네트워크 데이터를 생성할 수 없습니다.", "en": "Could not generate network data."},
    # DataFrame Columns
    "col_name": {"ko": "이름", "en": "Name"},
    "col_emotion": {"ko": "감정 계수", "en": "Emotion Score"},
    "col_cognition": {"ko": "사고 계수", "en": "Cognition Score"},
    "col_expression": {"ko": "표현 계수", "en": "Expression Score"},
    "col_value": {"ko": "가치 계수", "en": "Value Score"},
    "col_bias": {"ko": "편향 계수", "en": "Bias Score"},
    "col_role": {"ko": "핵심 역할", "en": "Core Role"},
}

# --- Page Config ---
st.set_page_config(
    page_title=TEXTS["page_title"]["en"],
    page_icon="🤖",
    layout="wide"
)

# --- Initialize Session State ---
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = {}
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

# --- Sidebar for Settings ---
with st.sidebar:
    st.header(TEXTS["sidebar_header"][st.session_state.lang])
    
    lang_choice = st.selectbox(
        label=f'{TEXTS["language_selector"]["en"]} / {TEXTS["language_selector"]["ko"]}',
        options=['한국어', 'English'],
        index=0 if st.session_state.lang == 'ko' else 1,
        key='lang_selector'
    )
    st.session_state.lang = 'ko' if lang_choice == '한국어' else 'en'
    lang = st.session_state.lang

# --- API Key Configuration (Runs only once) ---
api_configured = False
try:
    # --- THIS IS THE CORRECTED LINE ---
    genai.configure(api_key=st.secrets["GOOGLE_AI_API_KEY"])
    api_configured = True
except (KeyError, AttributeError):
    st.error(TEXTS["api_key_error_title"][lang])
    st.warning(TEXTS["api_key_error_body"][lang])
    api_configured = False


# --- Main UI ---
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

# --- Prompts (Full prompts included) ---
PROMPT_TEAM_PROFILE = """
당신은 조직 심리 분석가입니다. 주어진 채팅 기록을 바탕으로, '미러오알지 팀 분석 사례' 문서의 '정체성 계수 맵'과 같이 각 팀원의 특성을 분석하고 결과를 JSON 형식으로 반환하세요.

**분석 규칙:**
1.  **참여자 식별:** 채팅 기록에 등장하는 모든 주요 참여자를 식별합니다.
2.  **5대 계수 분석:** 각 참여자에 대해 다음 5가지 계수를 1-10점 척도로 평가합니다.
    * **감정(Emotion):** 감정 표현의 빈도와 강도.
    * **사고(Cognition):** 논리적, 분석적, 전략적 발언의 빈도.
    * **표현(Expression):** 의견, 상태, 아이디어 표현의 적극성.
    * **가치(Value):** 팀의 목표, 비전, 핵심 가치에 대한 언급.
    * **편향(Bias):** 특정 주제나 방식에 대한 선호/회피 경향.
3.  **핵심 역할 부여:** 각 참여자의 계수를 종합하여 'The Driver', 'The Coordinator' 등 가장 적합한 핵심 역할을 부여합니다.
4.  **JSON 형식 출력:** 아래와 같은 리스트 형태의 JSON으로만 응답하세요. 다른 설명은 추가하지 마세요.
    ```json
    [
      {
        "name": "참여자 이름",
        "emotion_score": 5,
        "cognition_score": 9,
        "expression_score": 6,
        "value_score": 9,
        "bias_score": 7,
        "core_role": "The Driver (전략 중심)"
      }
    ]
    ```

**[입력 데이터: 채팅 기록]**
---
{chat_log}
---
"""

PROMPT_FATIGUE_TIMELINE = """
당신은 조직 행동 분석가입니다. 주어진 채팅 기록을 분석하여, 시간 경과에 따른 각 팀원의 '피로도(Fatigue)' 변화를 추정하고, 그 결과를 날짜별 JSON 데이터로 반환하세요.

**분석 규칙:**
1.  **피로도 정의:** 피로도는 업무 부담, 스트레스, 부정적 감정 표현, 반응 속도 저하 등을 종합하여 1-10점으로 평가합니다. (1: 매우 낮음, 10: 매우 높음/소진 임박)
2.  **날짜별 분석:** 채팅 기록에 나타난 날짜별로 각 참여자의 피로도를 추정합니다. 특정 날짜에 발언이 없으면 이전 상태를 유지하거나 주변 상황에 따라 추정합니다.
3.  **JSON 형식 출력:** 아래와 같은 날짜-사용자-점수 구조의 JSON으로만 응답하세요. 다른 설명은 추가하지 마세요.
    ```json
    {
      "YYYY-MM-DD": {
        "참여자1": 3,
        "참여자2": 5
      },
      "YYYY-MM-DD": {
        "참여자1": 4,
        "참여자2": 6
      }
    }
    ```

**[입력 데이터: 채팅 기록]**
---
{chat_log}
---
"""

PROMPT_CONFLICT_NETWORK = """
당신은 관계 동역학 분석가입니다. 주어진 채팅 기록을 분석하여, 팀원 간의 상호작용을 '갈등 네트워크'로 모델링하고, 그 구조를 노드(node)와 엣지(edge) 형태의 JSON으로 반환하세요.

**분석 규칙:**
1.  **노드(Nodes):** 채팅에 참여한 모든 팀원을 노드로 정의합니다.
2.  **엣지(Edges):** 두 팀원 간의 주요 상호작용을 엣지로 정의합니다.
3.  **관계 유형(Relationship Type):** 각 엣지에 대해 관계를 다음 4가지 유형 중 하나로 분류합니다.
    * `high_risk`: 의견 충돌, 비난, 무시 등 명백한 갈등.
    * `medium_risk`: 잦은 의견 불일치, 긴장감 있는 대화.
    * `potential_risk`: 잠재적 오해나 의견 차이가 있는 관계.
    * `stable`: 지지, 동의, 협력 등 안정적인 관계.
4.  **JSON 형식 출력:** 아래와 같은 노드와 엣지 리스트를 포함한 JSON 객체로만 응답하세요.
    ```json
    {
      "nodes": [
        {"id": "참여자1", "label": "참여자1"},
        {"id": "참여자2", "label": "참여자2"}
      ],
      "edges": [
        {"from": "참여자1", "to": "참여자2", "type": "high_risk"},
        {"from": "참여자1", "to": "참여자3", "type": "stable"}
      ]
    }
    ```

**[입력 데이터: 채팅 기록]**
---
{chat_log}
---
"""

# --- Functions ---
def parse_kakao_talk(file_content):
    pattern = re.compile(r"--------------- (\d{4}년 \d{1,2}월 \d{1,2}일) ")
    chat_lines = file_content.split('\n')
    data, current_date = [], None
    for line in chat_lines:
        date_match = pattern.match(line)
        if date_match:
            current_date_str = date_match.group(1)
            current_date = datetime.strptime(current_date_str, "%Y년 %m월 %d일").date()
        elif line.startswith('[') and current_date:
            try:
                parts = line.split('] ', 2)
                if len(parts) == 3:
                    data.append({"date": current_date, "speaker": parts[0][1:], "message": parts[2]})
            except (IndexError, ValueError): continue
    return pd.DataFrame(data) if data else None

def call_gemini_api(prompt, chat_log):
    model = genai.GenerativeModel('gemini-pro')
    full_prompt = prompt.format(chat_log=chat_log)
    try:
        response = model.generate_content(full_prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_text)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        st.error(f"{TEXTS['api_parse_error'][lang]}: {response.text[:500]}")
        return None
    except Exception as e:
        st.error(f"{TEXTS['api_call_error'][lang]}: {e}")
        return None

def draw_network_graph(network_data):
    if not network_data or 'nodes' not in network_data or 'edges' not in network_data:
        st.warning(TEXTS["network_warning"][lang])
        return
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", notebook=True, directed=False)
    color_map = {"high_risk": "#FF4136", "medium_risk": "#FF851B", "potential_risk": "#FFDC00", "stable": "#DDDDDD"}
    for node in network_data['nodes']: net.add_node(node['id'], label=node['label'], size=25)
    for edge in network_data['edges']:
        edge_type = edge.get('type', 'stable')
        net.add_edge(edge['from'], edge['to'], color=color_map.get(edge_type, "#DDDDDD"), width=4 if edge_type == 'high_risk' else 2)
    try:
        net.save_graph("network_graph.html")
        with open("network_graph.html", 'r', encoding='utf-8') as f: html_content = f.read()
        components.html(html_content, height=620)
    except Exception as e: st.error(f"{TEXTS['network_error'][lang]}: {e}")

# --- Main App Logic ---
if api_configured:
    st.header(TEXTS["upload_header"][lang])
    st.info(TEXTS["upload_info"][lang])

    uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt", key="file_uploader")

    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            chat_df = parse_kakao_talk(file_content)

            if chat_df is not None:
                st.success(TEXTS["parsing_success"][lang].format(count=len(chat_df)))
                
                if st.button(TEXTS["analysis_button"][lang], key="start_analysis"):
                    chat_log_for_api = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
                    
                    with st.spinner(TEXTS["spinner_profile"][lang]):
                        st.session_state.analysis_result['profile'] = call_gemini_api(PROMPT_TEAM_PROFILE, chat_log_for_api)
                    with st.spinner(TEXTS["spinner_timeline"][lang]):
                        st.session_state.analysis_result['timeline'] = call_gemini_api(PROMPT_FATIGUE_TIMELINE, chat_log_for_api)
                    with st.spinner(TEXTS["spinner_network"][lang]):
                        st.session_state.analysis_result['network'] = call_gemini_api(PROMPT_CONFLICT_NETWORK, chat_log_for_api)
                    
                    st.success(TEXTS["analysis_complete"][lang])
            else:
                st.error(TEXTS["parsing_error"][lang])
        except Exception as e:
            st.error(f"{TEXTS['file_process_error'][lang]}: {e}")

    # --- Display Results in Tabs ---
    if st.session_state.analysis_result:
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
                    profile_df.rename(columns={
                        "name": TEXTS['col_name'][lang],
                        "emotion_score": TEXTS['col_emotion'][lang],
                        "cognition_score": TEXTS['col_cognition'][lang],
                        "expression_score": TEXTS['col_expression'][lang],
                        "value_score": TEXTS['col_value'][lang],
                        "bias_score": TEXTS['col_bias'][lang],
                        "core_role": TEXTS['col_role'][lang],
                    }, inplace=True)
                    st.dataframe(profile_df, use_container_width=True)
                except Exception as e:
                    st.error(f"{TEXTS['profile_error'][lang]}: {e}")
                    st.json(profile_data)
            else:
                st.warning(TEXTS["profile_warning"][lang])

        with tab2:
            st.subheader(TEXTS["fatigue_subheader"][lang])
            st.info(TEXTS["fatigue_info"][lang])
            timeline__data = st.session_state.analysis_result.get('timeline')
            if timeline_data:
                try:
                    timeline_df = pd.DataFrame.from_dict(timeline_data, orient='index')
                    timeline_df.index = pd.to_datetime(timeline_df.index)
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
                draw_network_graph(network_data)
            else:
                st.warning(TEXTS["network_warning"][lang])
