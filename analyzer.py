import streamlit as st
import openai
import re

# Streamlit secrets에서 API 키를 안전하게 로드
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    client = None

# LLM에게 역할을 부여하고, 분석 틀과 출력 형식을 지시하는 '마스터 프롬프트'
MASTER_PROMPT = """
You are Dr. Aiden, a world-class organizational psychologist and expert analyst at MirrorOrg. Your task is to analyze the provided team chat log and generate a concise, insightful "1-Page Summary Report" in MARKDOWN format.

**DO NOT** generate JSON or any other format. The entire output must be a single, readable Markdown document.

Follow this structure precisely, based on the "Project Echo" case study:

---

# **MirrorOrg 1-Page Diagnostic Report**

## **Part 1: Team Identity & Communication Style**
- Based on the dialogue, briefly summarize the team's overall communication patterns, decision-making style, and emotional tone. (3-4 sentences)

## **Part 2: Systemic Risk Assessment**
- Identify up to 3 critical systemic risks observed in the conversation. Present them in a Markdown table. Focus on structural issues, not individual faults.

| Risk Type | Description | Severity |
| :--- | :--- | :--- |
| (e.g., Emotional Burnout) | (e.g., Specific members show signs of fatigue, and this emotional labor is not being managed.) | (e.g., 🔴 High) |
| (e.g., Decision Bottleneck) | (e.g., Decisions seem overly reliant on one person, creating delays and single points of failure.) | (e.g., 🟡 Medium) |
| (e.g., Ambiguous Roles) | (e.g., Unclear responsibilities lead to redundant work or missed tasks.) | (e.g., 🟡 Medium) |

*Severity Guide: 🔴 High, 🟡 Medium, 🟢 Low*

## **Part 3: Key Recommendations**
- Provide 2-3 concrete, actionable recommendations to improve the team's resilience and communication effectiveness.
- **Recommendation 1:** (e.g., Introduce a 'silent hour' protocol to reduce communication fatigue.)
- **Recommendation 2:** (e.g., Clarify roles for the next project phase in a shared document.)

## **Part 4: Overall Conclusion**
- Provide a final, conclusive summary of the team's current state and potential. (2-3 sentences)

---

**Analyze the following chat log:**
```
{chat_log}
```
"""

def analyze_report(chat_log: str) -> str | None:
    """
    OpenAI API를 호출하여 대화 기록으로부터 조직 분석 리포트를 생성합니다.
    
    Args:
        chat_log: 분석할 대화 기록 문자열.

    Returns:
        Markdown 형식의 분석 리포트 문자열 또는 실패 시 None.
    """
    if not client:
        st.error("OpenAI API 클라이언트가 초기화되지 않았습니다. Streamlit secrets에 API 키를 설정했는지 확인하세요.")
        return None

    try:
        # 프롬프트에 실제 대화 기록을 삽입
        prompt = MASTER_PROMPT.format(chat_log=chat_log)

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o", # 또는 "gpt-4-turbo"
            messages=[
                {"role": "system", "content": "You are an expert organizational psychologist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # 일관성 있는 결과를 위해 온도를 낮게 설정
            max_tokens=2048,
            top_p=0.5,
        )
        
        report_content = response.choices[0].message.content
        
        # LLM이 가끔 불필요한 ```markdown 태그를 추가하는 경우 제거
        report_content = re.sub(r'^```markdown\s*', '', report_content)
        report_content = re.sub(r'\s*```$', '', report_content)

        return report_content.strip()

    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return None
