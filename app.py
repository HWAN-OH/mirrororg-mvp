import streamlit as st
import google.generativeai as genai
import analyzer
import pandas as pd

# ... TEXTS 사전, 언어 설정, 사이드바, API키, 파일 업로드 등 기존 구조 동일 ...

# --- 결과 출력 부분만 집중적으로 표시 ---

    # --- 피로도 곡선 ---
    st.subheader(TEXTS["fatigue_title"][lang])
    fatigue_data = st.session_state.get('fatigue_data')
    if fatigue_data and isinstance(fatigue_data, list):
        try:
            lines = []
            for item in fatigue_data:
                for d in item["fatigue_timeline"]:
                    lines.append({"name": item["name"], "date": d["date"], "score": d["score"]})
            df = pd.DataFrame(lines)
            chart_data = df.pivot(index="date", columns="name", values="score")
            st.line_chart(chart_data)
        except Exception as e:
            st.error(f"{TEXTS['no_fatigue_data'][lang]}: {e}")
    elif fatigue_data and "raw_response" in fatigue_data:
        st.warning("LLM 원본 응답(raw):")
        st.code(fatigue_data["raw_response"])
        st.info(TEXTS["no_fatigue_data"][lang])
    else:
        st.info(TEXTS["no_fatigue_data"][lang])

    # --- 네트워크 ---
    st.subheader(TEXTS["network_title"][lang])
    network_data = st.session_state.get('network_data')
    if network_data and isinstance(network_data, list):
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            G = nx.Graph()
            for link in network_data:
                G.add_edge(link["source"], link["target"], weight=link["strength"])
            fig, ax = plt.subplots()
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, ax=ax, node_color='lightblue', edge_color='gray')
            st.pyplot(fig)
        except Exception as e:
            st.error(f"{TEXTS['no_network_data'][lang]}: {e}")
    elif network_data and "raw_response" in network_data:
        st.warning("LLM 원본 응답(raw):")
        st.code(network_data["raw_response"])
        st.info(TEXTS["no_network_data"][lang])
    else:
        st.info(TEXTS["no_network_data"][lang])

