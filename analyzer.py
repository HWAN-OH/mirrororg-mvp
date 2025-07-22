import streamlit as st
import openai
import re

# Streamlit secrets에서 API 키를 안전하게 로드
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    client = None

# --- 다국어 프롬프트 정의 ---

# 영어 프롬프트 (정체성 계수 맵 추가)
MASTER_PROMPT_EN = """
You are Dr. Aiden, a world-class organizational psychologist and expert analyst at MirrorOrg. Your task is to analyze the provided team chat log and generate a concise, insightful "1-Page Summary Report" in MARKDOWN format.

**DO NOT** generate JSON. The entire output must be a single, readable Markdown document.

Follow this structure precisely, based on the "Project Echo" case study:

---

# **MirrorOrg 1-Page Diagnostic Report**

## **Part 1: Identity Coefficient Map & Core Roles**
- Analyze the dialogue patterns (frequency, word choice, reactions) to parameterize each participant.
- Identify their core role within the team's dynamics.
- Present the results in a Markdown table. Rate each coefficient from 1 (Low) to 10 (High).

| Name | Emotion | Cognition | Expression | Value | Bias | Core Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (e.g., Julian) | 5 | 9 | 6 | 9 | 7 | (e.g., The Driver) |
| (e.g., Sophia) | 10 | 7 | 10 | 6 | 8 | (e.g., The Emotional Core) |
*Name, Core Role, and descriptions must be inferred from the chat log.*

## **Part 2: Team's General Communication Style**
- Based on the dialogue, briefly summarize the team's overall communication patterns, decision-making style, and emotional tone. (3-4 sentences)

## **Part 3: Systemic Risk Assessment**
- Identify up to 3 critical systemic risks. Focus on structural issues, not individual faults.

| Risk Type | Description | Severity |
| :--- | :--- | :--- |
| (e.g., Emotional Burnout) | (e.g., Specific members show signs of fatigue, and this emotional labor is not being managed.) | (e.g., 🔴 High) |
| (e.g., Decision Bottleneck) | (e.g., Decisions seem overly reliant on one person, creating delays.) | (e.g., 🟡 Medium) |

*Severity Guide: 🔴 High, 🟡 Medium, 🟢 Low*

## **Part 4: Key Recommendations**
- Provide 2-3 concrete, actionable recommendations to improve team resilience.
- **Recommendation 1:** (e.g., Introduce a 'silent hour' protocol.)
- **Recommendation 2:** (e.g., Clarify roles for the next project phase.)

## **Part 5: Overall Conclusion**
- Provide a final, conclusive summary of the team's current state and potential. (2-3 sentences)

---

**Analyze the following chat log:**
```
{chat_log}
```
"""

# 한국어 프롬프트 (정체성 계수 맵 추가)
MASTER_PROMPT_KO = """
당신은 MirrorOrg의 세계적인 조직 심리학자이자 수석 분석가인 '에이든 박사'입니다. 주어진 팀 채팅 기록을 분석하여, 간결하고 통찰력 있는 '1페이지 요약 보고서'를 MARKDOWN 형식으로 작성하는 것이 당신의 임무입니다.

**주의:** 절대로 JSON 형식으로 결과를 생성하지 마십시오. 전체 출력물은 반드시 읽기 쉬운 단일 마크다운 문서여야 합니다.

'프로젝트 에코' 사례 연구를 기반으로 다음 구조를 정확히 따르십시오:

---

# **MirrorOrg 1페이지 진단 보고서**

## **Part 1: 정체성 계수 맵 및 핵심 역할**
- 대화 기록에 나타난 발언의 빈도, 단어 선택, 반응 패턴 등을 분석하여, 각 등장인물을 5가지 핵심 계수로 파라미터화하고 핵심 역할을 정의합니다.
- 결과를 마크다운 테이블로 제시하십시오. 각 계수는 1(낮음)부터 10(높음)까지로 평가합니다.

| 이름 | 감정 | 사고 | 표현 | 가치 | 편향 | 핵심 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (예: Julian) | 5 | 9 | 6 | 9 | 7 | (예: The Driver) |
| (예: Sophia) | 10 | 7 | 10 | 6 | 8 | (예: The Emotional Core) |
*이름, 핵심 역할 및 설명은 반드시 채팅 기록을 통해 추론해야 합니다.*

## **Part 2: 팀의 전반적인 소통 스타일**
- 대화 내용을 바탕으로 팀의 전반적인 소통 패턴, 의사결정 방식, 감정적 분위기를 간략하게 요약합니다. (3-4 문장)

## **Part 3: 시스템적 리스크 평가**
- 대화에서 관찰된 최대 3가지의 핵심적인 시스템 리스크를 식별하여 마크다운 테이블 형식으로 제시합니다. 개인의 잘못이 아닌 구조적 문제에 초점을 맞춥니다.

| 리스크 유형 | 설명 | 심각도 |
| :--- | :--- | :--- |
| (예: 감정적 소진) | (예: 특정 구성원에게서 피로의 징후가 보이며, 이러한 감정 노동이 관리되지 않고 있습니다.) | (예: 🔴 높음) |
| (예: 의사결정 병목 현상) | (예: 의사결정이 한 사람에게 과도하게 의존하여 지연 및 단일 장애점을 유발합니다.) | (예: 🟡 중간) |

*심각도 가이드: 🔴 높음, 🟡 중간, 🟢 낮음*

## **Part 4: 핵심 권장 사항**
- 팀의 회복탄력성과 소통 효율성을 개선하기 위한 2-3가지 구체적이고 실행 가능한 권장 사항을 제공합니다.
- **권장 사항 1:** (예: 소통으로 인한 피로를 줄이기 위해 '집중 근무 시간' 프로토콜을 도입합니다.)
- **권장 사항 2:** (예: 다음 프로젝트 단계를 위해 공유 문서에서 역할을 명확히 정의합니다.)

## **Part 5: 종합 결론**
- 팀의 현재 상태와 잠재력에 대한 최종적이고 종합적인 요약을 제공합니다. (2-3 문장)

---

**다음 채팅 기록을 분석하십시오:**
```
{chat_log}
```
"""

def analyze_report(chat_log: str, lang: str = 'en') -> str | None:
    """
    OpenAI API를 호출하여 선택된 언어로 조직 분석 리포트를 생성합니다.
    """
    if not client:
        st.error("OpenAI API client is not initialized. Please check your Streamlit secrets.")
        return None

    prompt_template = MASTER_PROMPT_KO if lang == 'ko' else MASTER_PROMPT_EN
    
    try:
        prompt = prompt_template.format(chat_log=chat_log)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert organizational psychologist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2048,
            top_p=0.5,
        )
        
        report_content = response.choices[0].message.content
        
        report_content = re.sub(r'^```markdown\s*', '', report_content)
        report_content = re.sub(r'\s*```$', '', report_content)

        return report_content.strip()

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None
