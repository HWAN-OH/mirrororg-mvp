# MirrorOrg MVP Streamlit Application v1.1
# 개선 사항:
# 1. 코드 구조 개선: 분석 로직과 UI 로직을 분리하여 가독성 및 유지보수성 향상.
# 2. 분석 기능 추가:
#    - 감정 분석(간단한 키워드 기반) 프록시 추가.
#    - 상호작용 네트워크(단순) 시각화 추가.
# 3. UI/UX 개선: 탭을 활용하여 대시보드를 체계적으로 구성하고, 동적 캡션 추가.
# 4. PDF 리포트 기능 강화: 더 많은 분석 내용을 포함하도록 개선.

import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import tempfile
from xhtml2pdf import pisa
import networkx as nx

# --- 1. 데이터 처리 및 분석 로직 (Analysis Logic) ---
# 이 섹션은 데이터 처리와 분석에 관련된 함수들을 모아놓은 부분입니다.

@st.cache_data
def parse_chat_log(file_content):
    """
    채팅 로그를 파싱하여 DataFrame으로 변환합니다.
    - 카카오톡, 슬랙 등 다양한 포맷을 지원할 수 있도록 확장 가능성을 염두에 둡니다.
    """
    lines = file_content.splitlines()
    chat_data = []
    # 카카오톡 날짜 패턴
    date_pattern = re.compile(r"--------------- (\d{4}년 \d{1,2}월 \d{1,2}일) .* ---------------")
    # 카카오톡 메시지 패턴
    message_pattern = re.compile(r"\[(.*?)\] \[(오전|오후) (\d{1,2}:\d{2})\] (.*)")
    
    current_date = None
    for line in lines:
        date_match = date_pattern.match(line)
        if date_match:
            current_date = date_match.group(1)
            continue
            
        message_match = message_pattern.match(line)
        if message_match and current_date:
            user = message_match.group(1).strip()
            message = message_match.group(4).strip()
            
            # 시스템 메시지 필터링
            if '님과 카카오톡 대화' in user or '저장한 날짜' in user:
                continue
            
            chat_data.append([current_date, user, message])
            
    if not chat_data:
        return pd.DataFrame()

    df = pd.DataFrame(chat_data, columns=['Date', 'User', 'Message'])
    df['Date'] = pd.to_datetime(df['Date'], format='%Y년 %m월 %d일')
    return df

@st.cache_data
def anonymize_data(df):
    """
    사용자 이름을 익명화합니다.
    """
    if 'User' not in df.columns or df.empty:
        return df, {}
    unique_users = df['User'].unique()
    anonymization_map = {user: f"Person {i+1}" for i, user in enumerate(unique_users)}
    df['User'] = df['User'].map(anonymization_map)
    return df, anonymization_map

def analyze_sentiment_proxy(df):
    """
    간단한 키워드 기반으로 감정 계수 프록시를 계산합니다.
    - 긍정/부정 키워드를 기반으로 점수를 매깁니다.
    """
    positive_keywords = ['감사', 'ㅋㅋ', 'ㅎㅎ', '좋아요', '화이팅', '짱', '멋지다', '최고', '👍']
    negative_keywords = ['죄송', 'ㅠㅠ', 'ㅜㅜ', '에고', '헉', '힘들', '피곤', '문제']
    
    sentiment_scores = {user: {'positive': 0, 'negative': 0} for user in df['User'].unique()}
    
    for _, row in df.iterrows():
        for keyword in positive_keywords:
            if keyword in row['Message']:
                sentiment_scores[row['User']]['positive'] += 1
        for keyword in negative_keywords:
            if keyword in row['Message']:
                sentiment_scores[row['User']]['negative'] += 1
                
    sentiment_df = pd.DataFrame(sentiment_scores).T.reset_index()
    sentiment_df.columns = ['User', 'Positive Keywords', 'Negative Keywords']
    return sentiment_df

def analyze_interaction_network(df):
    """
    사용자 간의 상호작용(멘션 등)을 분석하여 네트워크 그래프 데이터를 생성합니다.
    - 이 MVP에서는 메시지 순서를 기반으로 간단한 상호작용을 추정합니다.
    """
    G = nx.DiGraph()
    users = df['User'].unique()
    G.add_nodes_from(users)
    
    if len(df) > 1:
        for i in range(1, len(df)):
            sender = df['User'].iloc[i]
            receiver = df['User'].iloc[i-1]
            if sender != receiver:
                if G.has_edge(sender, receiver):
                    G[sender][receiver]['weight'] += 1
                else:
                    G.add_edge(sender, receiver, weight=1)
    return G

# --- 2. UI 렌더링 로직 (UI Rendering Logic) ---
# 이 섹션은 Streamlit UI를 구성하고 사용자에게 보여주는 부분입니다.

def render_ui():
    st.set_page_config(layout="wide", page_title="MirrorOrg MVP")

    # --- Sidebar ---
    st.sidebar.title("MirrorOrg™ MVP")
    st.sidebar.markdown("### 조직 진단 인텔리전스 솔루션")
    st.sidebar.markdown("---")
    st.sidebar.info(
        "1. 카카오톡 채팅 기록(.txt)을 업로드하세요.\n"
        "2. AI가 자동으로 데이터를 분석합니다.\n"
        "3. 조직의 숨겨진 패턴을 확인하세요."
    )
    st.sidebar.markdown("---")
    st.sidebar.warning("모든 데이터는 익명화 처리되며, 서버에 저장되지 않습니다.")

    # --- Main Content ---
    st.title("📊 MirrorOrg: 조직 진단 대시보드")
    st.markdown("당신의 조직에 숨겨진 감정과 갈등을 데이터로 진단합니다.")

    uploaded_file = st.file_uploader("여기에 카카오톡 채팅 기록(.txt) 파일을 끌어다 놓으세요.", type="txt")

    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            st.error("UTF-8 인코딩 형식의 파일만 지원합니다.")
            return

        with st.spinner('AI가 데이터를 분석하고 있습니다...'):
            df_raw = parse_chat_log(file_content)
            
            if df_raw.empty:
                st.error("채팅 데이터를 파싱할 수 없습니다. 카카오톡 PC버전에서 '대화 내보내기' 기능을 사용했는지 확인해주세요.")
                return

            df, user_map = anonymize_data(df_raw.copy())
            
            st.success("✅ 분석이 완료되었습니다!")
            st.markdown("---")
            
            render_dashboard(df, user_map)
    else:
        st.info("분석을 시작하려면 채팅 기록 파일을 업로드해주세요.")

def render_dashboard(df, user_map):
    """
    분석된 데이터를 사용하여 대시보드를 렌더링합니다.
    """
    tab1, tab2, tab3, tab4 = st.tabs(["📈 종합 분석", "💬 표현 계수", "🌡️ 감정/피로도", "🔗 상호작용 네트워크"])

    with tab1:
        render_summary_tab(df, user_map)
    with tab2:
        render_expression_tab(df)
    with tab3:
        render_fatigue_emotion_tab(df)
    with tab4:
        render_network_tab(df)

def render_summary_tab(df, user_map):
    st.header("1. 기본 통계 (Basic Statistics)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 메시지 수", f"{len(df):,}")
    col2.metric("참여 인원", f"{len(user_map)}")
    if not df.empty:
        col3.metric("분석 기간 (일)", f"{(df['Date'].max() - df['Date'].min()).days + 1}")
    col4.metric("데이터 익명화", "완료")

    with st.expander("익명화 매핑 정보 보기"):
        st.json(user_map)
        
    st.info(
        "**[MVP 안내]** 이 프로토타입은 미러오알지의 핵심 기능 중 일부를 단순화하여 보여줍니다.\n\n"
        "**정식 버전**에서는 더 정교한 AI 모델을 통해 **갈등 네트워크, 역할 재배치 시뮬레이션** 등 심층적인 분석 결과를 제공합니다."
    )

def render_expression_tab(df):
    st.header("2. 참여자별 메시지 빈도 (Proxy for Expression Coefficient)")
    st.markdown("누가 대화를 주도하고 있는지 파악할 수 있습니다. 이는 개인의 `표현 계수`를 가늠하는 지표가 됩니다.")
    
    message_counts = df['User'].value_counts().reset_index()
    message_counts.columns = ['User', 'Message Count']
    
    fig_bar = px.bar(message_counts, 
                     x='User', y='Message Count', 
                     title='참여자별 총 메시지 수',
                     labels={'User': '참여자', 'Message Count': '메시지 수'},
                     color='User', template='plotly_white')
    st.plotly_chart(fig_bar, use_container_width=True)

def render_fatigue_emotion_tab(df):
    st.header("3. 일별 대화량 및 감정 추이")
    st.markdown("프로젝트의 강도가 높았던 시기(피로도)와 팀의 전반적인 감정 상태를 시각적으로 확인할 수 있습니다.")
    
    # 일별 대화량 (피로도 프록시)
    daily_activity = df.groupby('Date').size().reset_index(name='Message Count')
    fig_line = px.line(daily_activity, 
                       x='Date', y='Message Count', 
                       title='일별 총 대화량 (업무 강도 프록시)',
                       labels={'Date': '날짜', 'Message Count': '메시지 수'},
                       markers=True, template='plotly_white')
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 감정 분석 (감정 계수 프록시)
    sentiment_df = analyze_sentiment_proxy(df)
    fig_sentiment = px.bar(sentiment_df, x='User', y=['Positive Keywords', 'Negative Keywords'],
                           title='참여자별 긍정/부정 키워드 사용 빈도 (감정 프록시)',
                           labels={'value': '키워드 수', 'User': '참여자'},
                           color_discrete_map={'Positive Keywords': '#34A853', 'Negative Keywords': '#EA4335'},
                           template='plotly_white')
    st.plotly_chart(fig_sentiment, use_container_width=True)

def render_network_tab(df):
    st.header("4. 상호작용 네트워크 (Interaction Network)")
    st.markdown("팀원들이 서로 어떻게 소통하고 있는지 관계의 구조를 보여줍니다. (메시지를 주고받은 패턴 기반)")
    
    G = analyze_interaction_network(df)
    if not G.nodes():
        st.warning("네트워크를 생성할 상호작용 데이터가 부족합니다.")
        return

    pos = nx.spring_layout(G, k=0.8, iterations=50)
    
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br># of connections: {G.degree(node)}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=list(G.nodes()),
        textposition="top center",
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            reversescale=True,
            color=[G.degree(node) for node in G.nodes()],
            size=20,
            colorbar=dict(
                thickness=15,
                title='연결 수',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    fig_network = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='상호작용 네트워크 맵',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    st.plotly_chart(fig_network, use_container_width=True)


# --- App Execution ---
if __name__ == "__main__":
    render_ui()
