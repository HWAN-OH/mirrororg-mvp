import streamlit as st
import pandas as pd
import re
import os
from analyzer import analyze_chat

st.set_page_config(page_title="MirrorOrg - 조직 분석 MVP", layout="wide")

st.markdown("## 🧠 MirrorOrg 진단 툴")

lang = st.radio("Select Language / 언어 선택", options=["한국어", "English"], index=0, key="lang")

uploaded_file = st.file_uploader("📁 분석할 카카오톡 파일을 업로드하세요", type="txt")

if uploaded_file:
    content = uploaded_file.read().decode("utf-8")

    # 대화 전처리: 날짜 패턴 기준으로 최근 2000줄 추출
    lines = content.split("\n")
    filtered_lines = [line for line in lines if re.match(r"\d{4}년 \d{1,2}월 \d{1,2}일", line)]
    short_content = "\n".join(filtered_lines[-2000:]) if len(filtered_lines) > 0 else "\n".join(lines[-2000:])

    result = analyze_chat(short_content)

    # 에러 처리
    if "error" in result:
        st.error("분석 실패: " + result["error"])

    # 조직 진단 케이스
    elif "identities" in result:
        st.success("✅ 조직 진단 결과를 기반으로 분석되었습니다.")

        def render_identity_table(identities):
            df = pd.DataFrame(identities)
            df.set_index("name", inplace=True)
            st.dataframe(df.style.format("{:.1f}"))

        st.markdown("### 🧾 정체성 계수 분석")
        render_identity_table(result["identities"])

        st.markdown("### 🔍 갈등 구조 분석")
        st.json(result.get("conflicts", {}))

        st.markdown("### 🧪 시스템 리스크 총평")
        st.json(result.get("systemic_risk", {}))

        st.markdown("### 💡 회복탄력성 제언")
        st.json(result.get("suggestions", {}))

        st.markdown("### 📌 결론")
        st.write(result.get("conclusion", "(결론 없음)"))

    # 역할 분석 fallback 케이스
    elif "role_analysis" in result:
        st.warning("⚠️ 대화량이 적어 역할 분석으로 대체되었습니다.")
        st.markdown("### 👥 역할 기반 대화 분석")
        for item in result["role_analysis"]:
            st.markdown(f"- **{item['name']}** → *{item['role']}* : {item['reason']}")

    else:
        st.error("분석에 실패했습니다. 대화 내용이 충분히 풍부한지 확인해주세요.")

    st.markdown("---")
    st.markdown("ⓒ 2025 MirrorOrg. 모든 분석은 성향 이해를 위한 참고 용도로 제공되며 평가 목적이 아닙니다.")
