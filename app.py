import streamlit as st
import analyzer
import pandas as pd
import time
import tiktoken
import networkx as nx
import matplotlib.pyplot as plt

# (이름 변환 로직은 그대로 두거나, 필요 없으면 삭제)
NAME_MAP = {
    "오승환": "Seunghwan Oh",
    "박유미": "Yumi Park",
    "현진": "Hyunjin",
    "박원준": "Wonjoon Park",
    "박법준": "Beobjun Park",
    "김재용": "Jaeyong Kim",
    "김진관": "Jingwan Kim",
    "양석준": "Seokjun Yang",
    "JD": "JD"
}
def to_eng_name(name):
    return NAME_MAP.get(name, name)

NOTICE_KO = "※ 본 결과는 테스트/프로토타입 버전이며, 인물 평가는 아닌 '행동 기반 데이터' 기준 임시 분석입니다. 실제 인물 평가로 오용될 수 없습니다. 결과 활용 전 추가 근거 및 맥락 설명을 참고하세요."
NOTICE_EN = "※ This result is a test/prototype version, based on behavioral data, not a personality judgment. Cannot be used as a real person evaluation. Please refer to additional context before applying the results."
COPYRIGHT = "© 2025 Sunghwan Oh. All rights reserved. This MirrorOrg MVP is a test/experimental project. Not for commercial use."

TEXTS = {
    "page_title": {"ko": "MirrorOrg 네트워크 분석 MVP", "en": "MirrorOrg Network Analysis MVP"},
    "main_title": {"ko": "🪞 MirrorOrg 조직 관계 네트워크 분석", "en": "🪞 MirrorOrg Organizational Network Analysis"},
    "main_description": {
        "ko": "① 파일 업로드 → ② 관계 네트워크 분석 실행 → ③ 결과 확인의 안전하고 직관적 흐름을 제공합니다.",
        "en": "Upload file → Run network analysis → View result. Simple and safe workflow."
    },
    "sidebar_header": {"ko": "설정", "en": "Settings"},
    "language_selector": {"ko": "언어", "en": "Language"},
    "upload_header": {"ko": "1️⃣ 채팅 기록 업로드", "en": "1️⃣ Upload Chat History"},
    "upload_info": {
        "ko": "팀 채팅 기록을 .txt 파일로 업로드하세요. 업로드 전까지 아래 단계는 비활성화됩니다.",
        "en": "Upload your team chat history as a .txt file. Steps below are disabled until upload."
    },
    "file_uploader_label": {"ko": "분석할 .txt 파일을 선택하세요.", "en": "Choose a .txt file to analyze."},
    "chapter_header": {"ko": "2️⃣ 관계 네트워크 분석 실행", "en": "2️⃣ Run Relationship Network Analysis"},
    "chapter3_btn": {"ko": "관계 네트워크 분석", "en": "Run Network Analysis"},
    "analysis_complete": {"ko": "✅ 분석이 완료되었습니다!", "en": "✅ Analysis complete!"},
    "results_header": {"ko": "3️⃣ 결과 확인", "en": "3️⃣ View Results"},
    "network_title": {"ko": "관계 네트워크 결과", "en": "Network Analysis Result"},
    "no_network_data": {"ko": "관계 네트워크 데이터를 시각화할 수 없습니다.", "en": "Network data could not be visualized."},
    "raw_llm": {"ko": "LLM 원본 응답(raw)", "en": "LLM Raw Response"},
}

st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

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

st.title(f"{TEXTS['main_title']['ko']} / {TEXTS['main_title']['en']}")
st.markdown(f"{TEXTS['main_description']['ko']}<br/>{TEXTS['main_description']['en']}", unsafe_allow_html=True)

st.header(f"{TEXTS['upload_header'][lang]}")
st.info(TEXTS["upload_info"][lang])
uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt")

if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일이 업로드되었습니다.")

MAX_TOKENS = 14000
MAX_LINES = 2000

def count_tokens(text, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def get_short_content(file_content):
    lines = file_content.splitlines()
    if len(lines) > MAX_LINES:
        st.warning(f"분석 데이터가 많아 최신 {MAX_LINES}줄(약 2개월치)만 사용합니다.")
    short_text = "\n".join(lines[-MAX_LINES:])
    while count_tokens(short_text) > MAX_TOKENS and len(lines) > 50:
        lines = lines[-(len(lines)//2):]
        short_text = "\n".join(lines)
    if count_tokens(short_text) > MAX_TOKENS:
        st.warning("파일이 너무 커서 더 작게 잘라 샘플 분석합니다.")
    return short_text

st.header(TEXTS["chapter_header"][lang])
if st.button(f"{TEXTS['chapter3_btn']['ko']} / {TEXTS['chapter3_btn']['en']}", use_container_width=True):
    with st.spinner("관계 네트워크 분석 중... / Running network analysis..."):
        st.session_state.network_data = analyzer.analyze_network_json(get_short_content(file_content), lang=lang)
    st.toast(TEXTS["analysis_complete"][lang], icon="✅")

st.header(TEXTS["results_header"][lang])

if st.session_state.get('network_data'):
    st.subheader(f"{TEXTS['network_title']['ko']} / {TEXTS['network_title']['en']}")
    network_data = st.session_state.get('network_data')
    if network_data and isinstance(network_data, list):
        try:
            # 1. 표로 보기 (영문명 자동 변환)
            lines = []
            for rel in network_data:
                src = to_eng_name(rel.get("source", ""))
                tgt = to_eng_name(rel.get("target", ""))
                strength = rel.get("strength")
                typ = rel.get("type")
                lines.append({
                    "Source": src,
                    "Target": tgt,
                    "Strength": strength,
                    "Type": typ
                })
            df = pd.DataFrame(lines)
            st.markdown("**🔗 관계 네트워크 표 / Relationship Table**")
            st.dataframe(df)

            # 2. 네트워크 그래프 시각화
            st.markdown("**🌐 네트워크 다이어그램 / Network Diagram**")
            G = nx.DiGraph()
            for rel in lines:
                G.add_edge(rel["Source"], rel["Target"], weight=rel["Strength"], label=rel["Type"])
            pos = nx.spring_layout(G, seed=42, k=0.7)
            plt.figure(figsize=(6, 4))
            edge_colors = ['#34a853' if d['label']=='support' else '#ea4335' for _, _, d in G.edges(data=True)]
            nx.draw(G, pos, with_labels=True, node_size=1500, node_color="#f3f3f3", edge_color=edge_colors, font_size=12, font_weight="bold", arrows=True)
            nx.draw_networkx_edge_labels(G, pos, edge_labels={(u,v): d['label'] for u,v,d in G.edges(data=True)}, font_color='gray', font_size=10)
            st.pyplot(plt)
            st.caption(f"{NOTICE_KO}\n\n{NOTICE_EN}")
        except Exception as e:
            st.error(f"{TEXTS['no_network_data'][lang]}: {e}")
    elif network_data and "raw_response" in network_data:
        st.warning(f"{TEXTS['raw_llm']['ko']} / {TEXTS['raw_llm']['en']}:")
        st.code(network_data["raw_response"])
        st.info(f"{TEXTS['no_network_data']['ko']} / {TEXTS['no_network_data']['en']}")
    else:
        st.info(f"{TEXTS['no_network_data']['ko']} / {TEXTS['no_network_data']['en']}")
