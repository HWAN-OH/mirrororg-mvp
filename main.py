
# MirrorOrg MVP Streamlit Application

import streamlit as st
import pandas as pd
import re
import plotly.express as px
from collections import Counter

# --- Helper Functions ---

def parse_kakao_log(file_content):
    lines = file_content.splitlines()
    chat_data = []
    date_pattern = re.compile(r"--------------- (\d{4}년 \d{1,2}월 \d{1,2}일) .* ---------------")
    message_pattern = re.compile(r"\[(.*?)\] \[(오전|오후) (\d{1,2}:\d{2})\] (.*)")
    current_date = None
    for line in lines:
        date_match = date_pattern.match(line)
        if date_match:
            current_date = date_match.group(1)
            continue
        message_match = message_pattern.match(line)
        if message_match and current_date:
            user = message_match.group(1)
            if '님과 카카오톡 대화' in user or '저장한 날짜' in user:
                continue
            message = message_match.group(4)
            chat_data.append([current_date, user, message])
    if not chat_data:
        return pd.DataFrame(columns=['Date', 'User', 'Message'])
    df = pd.DataFrame(chat_data, columns=['Date', 'User', 'Message'])
    df['Date'] = pd.to_datetime(df['Date'], format='%Y년 %m월 %d일')
    return df

def anonymize_users(df):
    if 'User' not in df.columns:
        return df, {}
    unique_users = df['User'].unique()
    anonymization_map = {user: f"Person {i+1}" for i, user in enumerate(unique_users)}
    df['User'] = df['User'].map(anonymization_map)
    return df, anonymization_map

# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="MirrorOrg MVP")

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

st.title("📊 MirrorOrg: 조직 진단 대시보드")
st.markdown("당신의 조직에 숨겨진 감정과 갈등을 데이터로 진단합니다.")

uploaded_file = st.file_uploader("여기에 카카오톡 채팅 기록(.txt) 파일을 끌어다 놓으세요.", type="txt")

if uploaded_file is not None:
    try:
        file_content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error("UTF-8 인코딩 형식의 파일만 지원합니다.")
        st.stop()

    with st.spinner('데이터를 분석하는 중입니다...'):
        df = parse_kakao_log(file_content)
        if df.empty:
            st.error("채팅 데이터를 파싱할 수 없습니다.")
            st.stop()

        df_anonymized, user_map = anonymize_users(df.copy())

        st.success("✅ 분석이 완료되었습니다!")
        st.markdown("---")

        st.header("1. 기본 통계")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 메시지 수", f"{len(df_anonymized):,}")
        col2.metric("참여 인원", f"{len(user_map)}")
        if not df_anonymized.empty:
            col3.metric("분석 기간 (일)", f"{(df_anonymized['Date'].max() - df_anonymized['Date'].min()).days + 1}")
        col4.metric("데이터 익명화", "완료")

        with st.expander("익명화 매핑 정보 보기"):
            st.write(user_map)

        st.markdown("---")

        st.header("2. 참여자별 메시지 빈도")
        message_counts = df_anonymized['User'].value_counts().reset_index()
        message_counts.columns = ['User', 'Message Count']
        fig_bar = px.bar(message_counts, x='User', y='Message Count', title='참여자별 총 메시지 수', labels={'User': '참여자', 'Message Count': '메시지 수'}, color='User')
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        st.header("3. 일별 대화량 추이")
        daily_activity = df_anonymized.groupby('Date').size().reset_index(name='Message Count')
        fig_line = px.line(daily_activity, x='Date', y='Message Count', title='일별 총 대화량', labels={'Date': '날짜', 'Message Count': '메시지 수'}, markers=True)
        fig_line.update_layout(xaxis_title='날짜', yaxis_title='일일 메시지 수')
        st.plotly_chart(fig_line, use_container_width=True)

        st.info(
            "**[MVP 안내]** 이 프로토타입은 미러오알지의 핵심 기능 중 일부(표현 계수, 피로도)를 단순화하여 보여줍니다.\n\n"
            "**정식 버전**에서는 더 정교한 AI 모델을 통해 감정 곡선, 갈등 네트워크, 역할 재배치 시뮬레이션 등을 제공합니다."
        )
else:
    st.info("분석을 시작하려면 채팅 기록 파일을 업로드해주세요.")


import tempfile
from xhtml2pdf import pisa

def generate_pdf(summary_html):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pisa_status = pisa.CreatePDF(summary_html, dest=tmp_pdf)
        if pisa_status.err:
            return None
        return tmp_pdf.name

# --- PDF Report Section ---
st.markdown("---")
st.header("📄 리포트 다운로드")

if st.button("📥 PDF 리포트 생성하기"):
    with st.spinner("PDF 리포트를 생성 중입니다..."):
        summary_html = f"""
        <html><body>
        <h2>MirrorOrg 요약 리포트</h2>
        <p><strong>총 메시지 수:</strong> {len(df_anonymized):,}</p>
        <p><strong>참여 인원 수:</strong> {len(user_map)}</p>
        <p><strong>분석 기간:</strong> {(df_anonymized['Date'].max() - df_anonymized['Date'].min()).days + 1}일</p>
        <h3>참여자별 메시지 수</h3>
        <ul>
        {''.join(f'<li>{row["User"]}: {row["Message Count"]}건</li>' for _, row in message_counts.iterrows())}
        </ul>
        </body></html>
        """
        pdf_path = generate_pdf(summary_html)
        if pdf_path:
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📄 PDF 리포트 다운로드",
                    data=pdf_file,
                    file_name="mirrororg_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("PDF 생성에 실패했습니다.")
