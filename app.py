# app.py
# 역할: Streamlit UI를 구성하고, analyzer 모듈을 호출하여 결과를 시각화합니다.

import streamlit as st
import analyzer
import pandas as pd
import tiktoken
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- 기본 설정 및 텍스트 ---
# 한글 폰트 설정 (Streamlit Cloud에 기본 내장된 폰트 사용)
@st.cache_resource
def get_korean_font():
    font_path = None
    for font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
        if 'Nanum' in font or 'AppleGothic' in font or 'Malgun' in font:
            font_path = font
            break
    if font_path:
        return fm.FontProperties(fname=font_path)
    return None

korean_font = get_korean_font()


# 이름 영문 변환 (선택 사항)
NAME_MAP = { "오승환": "S.H. Oh", "박유미": "Y.M. Park", "현진": "Hyunjin", "박원준": "W.J. Park", "박법준": "B.J. Park", "김재용": "J.Y. Kim", "김진관": "J.G. Kim", "양석준": "S.J. Yang", "JD": "JD"}
def to_eng_name(name):
    return NAME_MAP.get(name, name)

NOTICE_KO = "※ 본 결과는 테스트/프로토타입 버전이며, 인물 평가는 아닌 '행동 기반 데이터' 기준 임시 분석입니다."
NOTICE_EN = "※ This result is a test/prototype version, based on behavioral data, not a personality judgment."
COPYRIGHT = "© 2025 Sunghwan Oh. All rights reserved."

TEXTS = {
    "page_title": {"ko": "MirrorOrg 네트워크 분석", "en": "MirrorOrg Network Analysis"},
    "main_title": {"ko": "🪞 MirrorOrg 조직 관계 네트워크 분석", "en": "🪞 MirrorOrg Organizational Network Analysis"},
    "sidebar_header": {"ko": "설정", "en": "Settings"},
    "language_selector": {"ko": "언어", "en": "Language"},
    "upload_header": {"ko": "1️⃣ 채팅 기록 업로드", "en": "1️⃣ Upload Chat History"},
    "file_uploader_label": {"ko": "분석할 .txt 파일을 선택하세요.", "en": "Choose a .txt file to analyze."},
    "chapter_header": {"ko": "2️⃣ 관계 네트워크 분석 실행", "en": "2️⃣ Run Relationship Network Analysis"},
    "analysis_button": {"ko": "관계 네트워크 분석 실행", "en": "Run Network Analysis"},
    "analysis_complete": {"ko": "✅ 분석이 완료되었습니다!", "en": "✅ Analysis complete!"},
    "results_header": {"ko": "3️⃣ 결과 확인", "en": "3️⃣ View Results"},
    "network_title": {"ko": "관계 네트워크 결과", "en": "Network Analysis Result"},
    "no_network_data": {"ko": "네트워크 데이터를 생성/시각화할 수 없습니다.", "en": "Could not generate or visualize network data."},
    "raw_llm_header": {"ko": "LLM 원본 응답 (디버깅용)", "en": "Raw LLM Response (for debugging)"},
}

# --- Streamlit 앱 구성 ---
st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")

# --- Session State 초기화 ---
if 'lang' not in st.session_state: st.session_state.lang = 'ko'
if 'network_data' not in st.session_state: st.session_state.network_data = None

# --- 사이드바 ---
with st.sidebar:
    st.header(f"{TEXTS['sidebar_header']['ko']} / {TEXTS['sidebar_header']['en']}")
    lang_choice = st.selectbox(
        label=f"{TEXTS['language_selector']['ko']} / {TEXTS['language_selector']['en']}",
        options=['한국어', 'English'],
        index=0 if st.session_state.lang == 'ko' else 1
    )
    st.session_state.lang = 'ko' if lang_choice == '한국어' else 'en'
    st.markdown("---")
    st.caption(f"{NOTICE_KO}\n\n{NOTICE_EN}")
    st.markdown("---")
    st.caption(COPYRIGHT)

lang = st.session_state.lang

# --- 메인 UI ---
st.title(TEXTS['main_title'][lang])

st.header(TEXTS["upload_header"][lang])
uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt", key="file_uploader_widget")

# 파일이 업로드되지 않으면 여기서 실행 중지
if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")

# --- 분석 실행 섹션 ---
st.header(TEXTS["chapter_header"][lang])

# 토큰 수 제한을 위한 함수
def get_short_content(content, max_lines=2000):
    lines = content.splitlines()
    if len(lines) > max_lines:
        st.warning(f"분석 데이터가 많아 최신 {max_lines}줄만 사용합니다.")
    return "\n".join(lines[-max_lines:])

if st.button(TEXTS['analysis_button'][lang], use_container_width=True):
    with st.spinner("관계 네트워크 분석 중..."):
        short_content = get_short_content(file_content)
        st.session_state.network_data = analyzer.analyze_network_json(short_content, lang=lang)
    st.toast(TEXTS["analysis_complete"][lang], icon="✅")

# --- 결과 확인 섹션 ---
if st.session_state.network_data:
    st.header(TEXTS["results_header"][lang])
    st.subheader(TEXTS['network_title'][lang])
    
    network_data = st.session_state.network_data

    # Case 1: 분석 성공 (결과가 리스트 형태)
    if isinstance(network_data, list):
        try:
            df = pd.DataFrame(network_data)
            st.markdown("**🔗 관계 네트워크 표**")
            st.dataframe(df)

            st.markdown("**🌐 네트워크 다이어그램**")
            G = nx.DiGraph()
            
            # 모든 노드를 먼저 추가
            nodes = set(df['source']).union(set(df['target']))
            for node in nodes:
                G.add_node(node)

            # 엣지 추가
            for _, row in df.iterrows():
                G.add_edge(row["source"], row["target"], weight=row.get("strength", 1.0), type=row["type"])

            # 시각화
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(12, 8))
            pos = nx.spring_layout(G, seed=42, k=0.9)
            
            edge_colors = ['#34a853' if G[u][v]['type'] == 'support' else '#ea4335' for u, v in G.edges()]
            
            nx.draw(G, pos, with_labels=True, node_size=3000, node_color="#e0e0e0", 
                    edge_color=edge_colors, width=2.0, font_size=10, font_weight="bold",
                    arrows=True, arrowsize=20, ax=ax, font_family=korean_font.get_name() if korean_font else None)
            
            st.pyplot(fig)

        except Exception as e:
            st.error(f"{TEXTS['no_network_data'][lang]}: {e}")
            st.json(network_data) # 오류 발생 시 원본 데이터 출력

    # Case 2: 분석 실패 (결과가 딕셔너리 형태, 오류 포함)
    elif isinstance(network_data, dict) and "error" in network_data:
        st.error(TEXTS['no_network_data'][lang])
        st.subheader(TEXTS['raw_llm_header'][lang])
        st.code(network_data.get("raw_response", "No raw response available."), language=None)
