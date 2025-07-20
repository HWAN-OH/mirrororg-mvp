# app.py
import streamlit as st
import google.generativeai as genai
import analyzer
import pandas as pd

# (기존 TEXTS, config, sidebar 등 생략, 기존 코드 그대로 유지)
# ... TEXTS/언어설정/사이드바/파일업로드 등 기존 코드 동일 ...

# --- Main App UI ---
st.title("🪞 MirrorOrg MVP: 종합 팀 분석")
st.markdown("팀 채팅 기록(.txt)을 업로드하고, 종합 분석 보고서와 함께 피로도 곡선과 관계 네트워크를 시각화합니다.")

api_configured = False
try:
    genai.configure(api_key=st.secrets["GOOGLE_AI_API_KEY"])
    api_configured = True
except (KeyError, AttributeError):
    st.error("API Key 오류: 관리자에게 문의하세요.")

if api_configured:
    uploaded_file = st.file_uploader("분석할 .txt 파일을 선택하세요.", type="txt")
    if uploaded_file:
        file_content = uploaded_file.getvalue().decode("utf-8")
        st.success(f"'{uploaded_file.name}' 파일 업로드 완료.")

        if st.button("종합 분석 보고서 생성하기"):
            with st.spinner("보고서 생성 중... (최대 2분 소요)"):
                st.session_state.report = analyzer.generate_report(file_content)
            st.success("✅ 보고서 생성 완료!")

        # --- 분석 보고서 표시 ---
        if 'report' in st.session_state and st.session_state.report:
            st.header("2. 종합 분석 보고서")
            st.markdown("---")
            st.markdown(st.session_state.report, unsafe_allow_html=True)

        # --- 피로도 곡선 시각화 ---
        st.subheader("3.1 피로도 변화 (Fatigue Trajectory)")
        fatigue_data = analyzer.analyze_fatigue_json(file_content)
        if fatigue_data and isinstance(fatigue_data, list):
            lines = []
            for item in fatigue_data:
                for d in item["fatigue_timeline"]:
                    lines.append({"이름": item["name"], "날짜": d["date"], "피로도": d["score"]})
            df = pd.DataFrame(lines)
            chart_data = df.pivot(index="날짜", columns="이름", values="피로도")
            st.line_chart(chart_data)
        else:
            st.info("피로도 곡선 데이터를 생성할 수 없습니다.")

        # --- 관계 네트워크 시각화 ---
        st.subheader("3.2 관계 네트워크 (Relationship Network)")
        network_data = analyzer.analyze_network_json(file_content)
        if network_data and isinstance(network_data, list):
            import networkx as nx
            import matplotlib.pyplot as plt
            G = nx.Graph()
            for link in network_data:
                G.add_edge(link["source"], link["target"], weight=link["strength"])
            fig, ax = plt.subplots()
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, ax=ax, node_color='lightblue', edge_color='gray')
            st.pyplot(fig)
        else:
            st.info("관계 네트워크 데이터를 생성할 수 없습니다.")
