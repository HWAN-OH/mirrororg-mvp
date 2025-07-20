import streamlit as st
import analyzer
import pandas as pd

TEXTS = {
    "page_title": {"ko": "MirrorOrg 단계별 MVP", "en": "MirrorOrg Stepwise MVP"},
    "main_title": {"ko": "🪞 MirrorOrg 단계별 팀 분석", "en": "🪞 MirrorOrg Stepwise Team Analysis"},
    "main_description": {
        "ko": "① 파일 업로드 → ② 챕터별 분석 실행 → ③ 결과 확인의 순서로 안전하고 직관적인 팀 분석을 제공합니다.",
        "en": "Upload file → Run each chapter → View result. This safe, clear flow ensures robust team analysis."
    },
    "sidebar_header": {"ko": "설정", "en": "Settings"},
    "language_selector": {"ko": "언어", "en": "Language"},
    "upload_header": {"ko": "1️⃣ 채팅 기록 업로드", "en": "1️⃣ Upload Chat History"},
    "upload_info": {
        "ko": "팀 채팅 기록을 .txt 파일로 업로드하세요. 업로드 전까지 아래 단계는 비활성화됩니다.",
        "en": "Upload your team chat history as a .txt file. Steps below are disabled until upload."
    },
    "file_uploader_label": {"ko": "분석할 .txt 파일을 선택하세요.", "en": "Choose a .txt file to analyze."},
    "chapter_header": {"ko": "2️⃣ 챕터별 분석 실행", "en": "2️⃣ Run Each Analysis Chapter"},
    "chapter1_btn": {"ko": "챕터 1: 종합 보고서", "en": "Chapter 1: Comprehensive Report"},
    "chapter2_btn": {"ko": "챕터 2: 피로도 곡선", "en": "Chapter 2: Fatigue Trajectory"},
    "chapter3_btn": {"ko": "챕터 3: 관계 네트워크", "en": "Chapter 3: Relationship Network"},
    "analysis_complete": {"ko": "✅ 분석이 완료되었습니다!", "en": "✅ Analysis complete!"},
    "results_header": {"ko": "3️⃣ 결과 확인", "en": "3️⃣ View Results"},
    "fatigue_title": {"ko": "챕터 2 결과: 피로도 곡선", "en": "Chapter 2 Result: Fatigue Trajectory"},
    "network_title": {"ko": "챕터 3 결과: 관계 네트워크", "en": "Chapter 3 Result: Relationship Network"},
    "no_fatigue_data": {"ko": "피로도 곡선 데이터를 시각화할 수 없습니다.", "en": "Fatigue trajectory data could not be visualized."},
    "no_network_data": {"ko": "관계 네트워크 데이터를 시각화할 수 없습니다.", "en": "Network data could not be visualized."},
    "report_title": {"ko": "챕터 1 결과: 종합 보고서", "en": "Chapter 1 Result: Comprehensive Report"},
    "raw_llm": {"ko": "LLM 원본 응답(raw)", "en": "LLM Raw Response"},
}

# 1. Page config & 언어 설정
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

# 3. Main UI
st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

st.header(TEXTS["upload_header"][lang])
st.info(TEXTS["upload_info"][lang])
uploaded_file = st.file_uploader(TEXTS["file_uploader_label"][lang], type="txt")

if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일이 업로드되었습니다.")

# 4. 챕터별 분석 실행
st.header(TEXTS["chapter_header"][lang])
col1, col2, col3 = st.columns(3)

# 챕터1: 종합 보고서
with col1:
    if st.button(TEXTS["chapter1_btn"][lang], use_container_width=True):
        with st.spinner("보고서 생성 중..."):
            st.session_state.report = analyzer.generate_report(file_content, lang=lang)
        st.toast(TEXTS["analysis_complete"][lang], icon="✅")

# 챕터2: 피로도 곡선
with col2:
    if st.button(TEXTS["chapter2_btn"][lang], use_container_width=True):
        with st.spinner("피로도 분석 중..."):
            st.session_state.fatigue_data = analyzer.analyze_fatigue_json(file_content, lang=lang)
        st.toast(TEXTS["analysis_complete"][lang], icon="✅")

# 챕터3: 관계 네트워크
with col3:
    if st.button(TEXTS["chapter3_btn"][lang], use_container_width=True):
        with st.spinner("관계 네트워크 분석 중..."):
            st.session_state.network_data = analyzer.analyze_network_json(file_content, lang=lang)
        st.toast(TEXTS["analysis_complete"][lang], icon="✅")

# 5. 결과 확인(챕터별 데이터가 생성된 후에만!)
st.header(TEXTS["results_header"][lang])

if st.session_state.get('report'):
    st.subheader(TEXTS["report_title"][lang])
    st.markdown(st.session_state.report, unsafe_allow_html=True)
    st.divider()

if st.session_state.get('fatigue_data'):
    st.subheader(TEXTS["fatigue_title"][lang])
    fatigue_data = st.session_state.get('fatigue_data')
    if fatigue_data and isinstance(fatigue_data, list):
        try:
            lines = []
            for item in fatigue_data:
                if "name" not in item or "fatigue_timeline" not in item:
                    st.error(f"필드 누락: {item}")
                    continue
                for d in item["fatigue_timeline"]:
                    if "date" not in d or "score" not in d:
                        st.error(f"날짜/점수 누락: {d}")
                        continue
                    lines.append({"name": item["name"], "date": d["date"], "score": d["score"]})
            if not lines:
                st.warning("시각화할 데이터가 없음")
            else:
                df = pd.DataFrame(lines)
                chart_data = df.pivot(index="date", columns="name", values="score")
                st.line_chart(chart_data)
        except Exception as e:
            st.error(f"{TEXTS['no_fatigue_data'][lang]}: {e}")
    elif fatigue_data and "raw_response" in fatigue_data:
        st.warning(TEXTS["raw_llm"][lang] + ":")
        st.code(fatigue_data["raw_response"])
        st.info(TEXTS["no_fatigue_data"][lang])
    else:
        st.info(TEXTS["no_fatigue_data"][lang])

if st.session_state.get('network_data'):
    st.subheader(TEXTS["network_title"][lang])
    network_data = st.session_state.get('network_data')
    if network_data and isinstance(network_data, list):
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            G = nx.Graph()
            for link in network_data:
                if "source" not in link or "target" not in link:
                    st.error(f"필드 누락: {link}")
                    continue
                G.add_edge(link["source"], link["target"], weight=link.get("strength", 1), type=link.get("type", ""))
            fig, ax = plt.subplots()
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, ax=ax, node_color='lightblue', edge_color='gray')
            st.pyplot(fig)
        except Exception as e:
            st.error(f"{TEXTS['no_network_data'][lang]}: {e}")
    elif network_data and "raw_response" in network_data:
        st.warning(TEXTS["raw_llm"][lang] + ":")
        st.code(network_data["raw_response"])
        st.info(TEXTS["no_network_data"][lang])
    else:
        st.info(TEXTS["no_network_data"][lang])
