import streamlit as st
import analyzer
import pandas as pd
import time
import tiktoken

# 한글→영문 이름 자동 치환 매핑 + 로마자 표기(미등록시)
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
try:
    from hangul_romanize import Transliter
    from hangul_romanize.rule import academic
    transliter = Transliter(academic)
    def to_eng_name(name):
        if name in NAME_MAP:
            return NAME_MAP[name]
        return transliter.translit(name)
except ImportError:
    def to_eng_name(name):
        return NAME_MAP.get(name, name)

NOTICE = (
    "※ 본 결과는 테스트/프로토타입 버전이며, 인물 평가는 아닌 '행동 기반 데이터' 기준 임시 분석입니다. "
    "실제 인물 평가로 오용될 수 없습니다. 결과 활용 전 추가 근거 및 맥락 설명을 참고하세요."
)
COPYRIGHT = "© 2025 Sunghwan Oh. All rights reserved. This MirrorOrg MVP is a test/experimental project. Not for commercial use."

TEXTS = {
    "page_title": {"ko": "MirrorOrg 단계별 MVP", "en": "MirrorOrg Stepwise MVP"},
    # ... (이전과 동일)
}

st.set_page_config(page_title=TEXTS["page_title"]["en"], page_icon="🤖", layout="wide")
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

with st.sidebar:
    st.header(TEXTS["sidebar_header"][st.session_state.lang])
    lang_choice = st.selectbox(
        label=f'{TEXTS["language_selector"]["en"]} / {TEXTS["language_selector"]["ko"]}',
        options=['한국어', 'English'],
        index=0 if st.session_state.lang == 'ko' else 1
    )
    st.session_state.lang = 'ko' if lang_choice == '한국어' else 'en'
    st.markdown("---")
    st.caption(NOTICE)
    st.markdown("---")
    st.caption(COPYRIGHT)

lang = st.session_state.lang

st.title(TEXTS["main_title"][lang])
st.markdown(TEXTS["main_description"][lang])

st.header(TEXTS["upload_header"][lang])
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
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(TEXTS["chapter1_btn"][lang], use_container_width=True):
        with st.spinner("보고서 생성 중... (최대 1분 소요될 수 있음)"):
            short_content = get_short_content(file_content)
            start = time.time()
            report = analyzer.generate_report(short_content, lang=lang, sample_mode=True)
            elapsed = time.time() - start
            if elapsed > 60:
                st.warning("분석이 오래 걸려 최신 2000줄 샘플 분석으로 자동 전환합니다.")
                short_content = get_short_content(file_content)
                report = analyzer.generate_report(short_content, lang=lang, sample_mode=True)
                st.info("샘플(최근 2000줄) 분석 결과입니다.")
            st.session_state.report = report
        st.toast(TEXTS["analysis_complete"][lang], icon="✅")

with col2:
    if st.button(TEXTS["chapter2_btn"][lang], use_container_width=True):
        with st.spinner("피로도 분석 중..."):
            st.session_state.fatigue_data = analyzer.analyze_fatigue_json(get_short_content(file_content), lang=lang)
        st.toast(TEXTS["analysis_complete"][lang], icon="✅")

with col3:
    if st.button(TEXTS["chapter3_btn"][lang], use_container_width=True):
        with st.spinner("관계 네트워크 분석 중..."):
            st.session_state.network_data = analyzer.analyze_network_json(get_short_content(file_content), lang=lang)
        st.toast(TEXTS["analysis_complete"][lang], icon="✅")

st.header(TEXTS["results_header"][lang])

if st.session_state.get('report'):
    st.subheader(TEXTS["report_title"][lang])
    st.markdown(st.session_state.report, unsafe_allow_html=True)
    st.caption(NOTICE)
    st.divider()

if st.session_state.get('fatigue_data'):
    st.subheader(TEXTS["fatigue_title"][lang])
    fatigue_data = st.session_state.get('fatigue_data')
    if fatigue_data and isinstance(fatigue_data, list):
        try:
            lines = []
            for item in fatigue_data:
                eng_name = to_eng_name(item["name"])
                for d in item["fatigue_timeline"]:
                    lines.append({"name": eng_name, "date": d["date"], "score": d["score"]})
            if not lines:
                st.warning("시각화할 데이터가 없음")
            else:
                df = pd.DataFrame(lines)
                chart_data = df.pivot(index="date", columns="name", values="score")
                st.line_chart(chart_data)
                st.caption(NOTICE)
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
                source = to_eng_name(link["source"])
                target = to_eng_name(link["target"])
                G.add_edge(source, target, weight=link.get("strength", 1), type=link.get("type", ""))
            fig, ax = plt.subplots()
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, ax=ax, node_color='lightblue', edge_color='gray')
            st.pyplot(fig)
            st.caption(NOTICE)
        except Exception as e:
            st.error(f"{TEXTS['no_network_data'][lang]}: {e}")
    elif network_data and "raw_response" in network_data:
        st.warning(TEXTS["raw_llm"][lang] + ":")
        st.code(network_data["raw_response"])
        st.info(TEXTS["no_network_data"][lang])
    else:
        st.info(TEXTS["no_network_data"][lang])
