import streamlit as st
import analyzer_full_auto as analyzer
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from fpdf import FPDF
import tempfile
from collections import Counter

@st.cache_resource
def get_korean_font():
    for font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
        if 'Nanum' in font or 'Malgun' in font or 'AppleGothic' in font:
            return fm.FontProperties(fname=font)
    return None

font_prop = get_korean_font()

st.set_page_config(page_title="MirrorOrg 네트워크 분석", layout="wide")
st.title("🪞 MirrorOrg 조직 관계 네트워크 분석")

uploaded_file = st.file_uploader("분석할 .txt 파일을 업로드하세요", type="txt")
if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다.")

def get_short_content(content, max_lines=2000):
    lines = content.splitlines()
    return "\n".join(lines[-max_lines:]) if len(lines) > max_lines else content

def generate_text_summary(network_data):
    supports = [x for x in network_data if x["type"] == "support"]
    conflicts = [x for x in network_data if x["type"] == "conflict"]
    all_names = [x["source"] for x in network_data] + [x["target"] for x in network_data]
    name_counts = Counter(all_names)
    support_to = Counter([x["target"] for x in supports])
    conflict_to = Counter([x["target"] for x in conflicts])
    leader = support_to.most_common(1)[0][0] if support_to else "없음"
    top_conflict = conflict_to.most_common(1)[0][0] if conflict_to else "없음"
    top_people = [name for name, _ in name_counts.most_common(3)]
    summary = f"""● **팀 전체 요약**
이 팀의 리더는 '{leader}'(이)가 가장 많은 지지를 받고 있습니다.
가장 갈등이 집중된 인물은 '{top_conflict}'입니다.

● **관계 네트워크 특징**
- 지지 관계: {len(supports)}건, 갈등 관계: {len(conflicts)}건
- 핵심 인물(참여 및 언급 수 TOP3): {', '.join(top_people)}
- 전체 네트워크에서 갈등은 '{top_conflict}'에 집중되어 있으며, 이는 향후 팀 리스크 요인입니다.

● **제언 및 인사이트**
리더 '{leader}'가 팀의 중재자 역할을 할 필요가 있으며,
갈등이 많은 '{top_conflict}'에 대한 중재와 피드백이 필요합니다.
지지 네트워크를 확장하는 것이 팀 안정성에 긍정적으로 작용할 것입니다.
"""
    return summary

if st.button("관계 네트워크 분석 실행", use_container_width=True):
    with st.spinner("분석 중..."):
        short_content = get_short_content(file_content)
        result = analyzer.analyze_network_json(short_content)

    if "data" in result:
        df = pd.DataFrame(result["data"])
        st.subheader("🔗 관계 네트워크 표")
        st.dataframe(df)

        st.markdown("### 📊 관계 네트워크 자동 요약")
        summary_text = generate_text_summary(result["data"])
        st.markdown(summary_text, unsafe_allow_html=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt="MirrorOrg 관계 네트워크 요약 보고서")
            pdf.ln(5)
            for line in summary_text.split("\n"):
                pdf.multi_cell(0, 10, txt=line)
            pdf.ln(5)
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 10, txt="■ 관계 목록", ln=True)
            for idx, row in df.iterrows():
                line = f"{row['source']} → {row['target']} ({row['type']}, 강도: {row['strength']})"
                pdf.cell(0, 10, txt=line, ln=True)
            pdf.output(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                st.download_button("📄 PDF 보고서 다운로드", data=f, file_name="network_report.pdf")

        st.subheader("🌐 네트워크 다이어그램")
        G = nx.DiGraph()
        for _, row in df.iterrows():
            G.add_edge(row["source"], row["target"], weight=row.get("strength", 1.0), type=row["type"])
        fig, ax = plt.subplots(figsize=(10, 7))
        pos = nx.spring_layout(G, seed=42)
        edge_colors = ["#34a853" if d["type"] == "support" else "#ea4335" for _, _, d in G.edges(data=True)]
        nx.draw(G, pos, with_labels=True, node_color="#f0f0f0", edge_color=edge_colors,
                node_size=2000, font_size=10, font_family=font_prop.get_name() if font_prop else None,
                width=2, arrows=True, arrowsize=20, ax=ax)
        st.pyplot(fig)

        st.subheader("📄 LLM 원본 응답 (디버깅용)")
        st.code(result["raw_response"])
        st.subheader("🧪 사용된 프롬프트")
        st.code(result["prompt"])

    elif "error" in result:
        st.error("❌ 네트워크 데이터를 생성할 수 없습니다.")
        st.subheader("📄 LLM 원본 응답 (디버깅용)")
        st.code(result.get("raw_response", "응답 없음"))
        st.subheader("🧪 사용된 프롬프트")
        st.code(result.get("prompt", "없음"))