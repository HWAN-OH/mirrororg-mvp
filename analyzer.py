import streamlit as st
import analyzer
from collections import Counter

st.set_page_config(page_title="MirrorOrg 조직 진단 요약 / Organizational Summary", layout="wide")
st.title("🪞 MirrorOrg 조직 진단 요약 / Organizational Summary")

with st.sidebar:
    st.markdown("## 📝 분석 목적 / Purpose")
    st.markdown("""
    이 도구는 MirrorMind 방식에 따라 구성원 간의 상호작용을 분석하여 **성향의 차이**를 시각화합니다.  
    **이 분석은 우열 평가나 인사 목적이 아니며**, 심층적 이해와 조직 내 커뮤니케이션 개선을 위한 것입니다.

    ---
    This tool visualizes interpersonal dynamics using the MirrorMind methodology, highlighting **differences in tendencies**,  
    **not for evaluation or HR purposes**, but to enhance understanding and communication within the organization.
    """)

    st.markdown("## ⚖️ 저작권 / Copyright")
    st.markdown("""
    © 2025 Sunghwan Oh. All rights reserved.  
    Unauthorized reproduction or redistribution is prohibited.
    """)

    st.markdown("## 🌐 언어 전환 / Language")
    lang = st.radio("Select Language", options=["한국어", "English"], index=0, key="language_radio")

uploaded_file = st.file_uploader("분석할 .txt 파일을 업로드하세요 (Upload a .txt file for analysis)", type="txt")
if not uploaded_file:
    st.stop()

file_content = uploaded_file.getvalue().decode("utf-8")
st.success(f"'{uploaded_file.name}' 파일이 성공적으로 업로드되었습니다 / Successfully uploaded")

def get_short_content(content, max_lines=2000):
    lines = content.splitlines()
    return "\n".join(lines[-max_lines:]) if len(lines) > max_lines else content

def generate_text_summary(network_data):
    if not isinstance(network_data, list):
        return "⚠️ 오류: 분석 결과가 올바른 JSON 리스트 형식이 아닙니다. / Invalid format returned."
    supports = [x for x in network_data if x.get("type") == "support"]
    conflicts = [x for x in network_data if x.get("type") == "conflict"]
    all_names = [x["source"] for x in network_data] + [x["target"] for x in network_data]
    name_counts = Counter(all_names)
    support_to = Counter([x["target"] for x in supports])
    conflict_to = Counter([x["target"] for x in conflicts])
    leader = support_to.most_common(1)[0][0] if support_to else "없음 / None"
    top_conflict = conflict_to.most_common(1)[0][0] if conflict_to else "없음 / None"
    top_people = [name for name, _ in name_counts.most_common(3)]

    summary = f"""
### 🧾 조직 진단 요약 / Organizational Diagnosis Summary (MirrorMind 기반)

- 📌 **리더 / Leader**: `{leader}`
- ⚠️ **갈등 집중 인물 / Conflict-prone figure**: `{top_conflict}`
- 👥 **핵심 인물들 / Key Figures**: {', '.join(top_people)}

---

### 🔍 종합 제언 / Insights & Suggestions

- 리더는 중재자 역할을 강화해야 합니다.  
  → The leader should strengthen their mediator role.

- 갈등이 집중된 인물은 피드백 방식 조정이 필요합니다.  
  → Conflict-heavy personas need feedback and role recalibration.

- 지지 네트워크 확장이 조직 안정성에 도움이 됩니다.  
  → Expanding the support network enhances team stability.
    """
    return summary

if st.button("진단 실행 (Run Diagnosis)", use_container_width=True):
    with st.spinner("분석 중... / Analyzing..."):
        short_content = get_short_content(file_content)
        result = analyzer.analyze_network_json(short_content)

    st.subheader("📄 GPT 원본 응답 / Raw GPT Response")
    st.code(result.get("raw_response", "응답 없음 / No response"))

    st.subheader("🧪 사용된 GPT 프롬프트 / Prompt")
    st.code(result.get("prompt", "프롬프트 없음 / No prompt"))

    if "data" in result:
        if not isinstance(result["data"], list):
            st.error("❌ 결과 데이터 형식 오류: 예상한 리스트가 아님 / Invalid format")
        else:
            st.markdown(generate_text_summary(result["data"]))
    elif "error" in result:
        st.error("❌ 진단 실패 / Diagnosis Failed: JSON 분석 실패")
