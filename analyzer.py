# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 사용자가 선택한 언어로 '종합 분석 보고서'를 생성합니다.
# 최종 버전: 다국어 프롬프트를 탑재하여 완전한 현지화(Localization)를 구현합니다.

import google.generativeai as genai
import pandas as pd

# --- [Lumina & Delta] Bilingual Prompt Engineering ---

# --- 1. Korean Prompt ---
PROMPT_KO = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
당신의 유일한 임무는 주어진 팀의 채팅 기록을 분석하여, 팀의 붕괴를 막고 성장을 돕기 위한 **'종합 분석 보고서'**를 한국어로 작성하는 것입니다.
보고서는 반드시 '미러오알지'의 핵심 방법론과 '프로젝트 에코' 분석 사례를 참고하여, 아래 지정된 Markdown 형식에 따라 작성해야 합니다.

### 프레임워크 핵심 지식: 미러오알지(MirrorOrg) 방법론
* **정의:** 조직을 '복잡계'로 보고, 정성적 대화를 정량적 데이터와 통찰력으로 변환하여 시스템의 숨겨진 역학을 진단하고 예측하는 프레임워크.
* **프로세스:** 진단 (팀 프로필 분석) → 예측 (피로도 변화, 관계 네트워크 분석)
* **사고 과정:** 채팅 기록에서 '프로젝트 에코' 사례와 유사한 패턴(예: 전략적 발언, 감정적 호소)을 찾아, 이를 '미러오알지'의 개념(정체성 계수, 정서적 부채)과 연결하여 해석하고 보고서를 작성합니다.

---
### 최종 보고서 출력 형식 (Markdown, 한국어)

# MirrorOrg 종합 분석 보고서

## 1. 분석 개요
* **분석 기간:** [채팅 기록의 시작 날짜] ~ [채팅 기록의 마지막 날짜]
* **분석 대상:** [채팅 기록에 참여한 주요 인물 목록]
* **핵심 요약:** (분석 결과에 대한 2~3 문장의 핵심 요약)

---

## 2. Phase 1: 진단 (Diagnosis)
### 2.1. 정체성 계수 맵 (Identity Coefficient Map)
팀원들의 성향과 역할을 파악하여 팀의 전체적인 구성을 진단합니다.

| 이름 (가명) | 감정 | 사고 | 표현 | 가치 | 편향 | 핵심 역할 |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (예: Julian) | ⚖️ 5 | 🧠 9 | ✏️ 6 | ⭐ 9 | 🎯 7 | The Driver (전략 중심) |
| (참여자 A) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |

**분석 근거:**
* **[참여자 A 이름]:** (해당 참여자의 계수가 왜 그렇게 판단되었는지, 채팅 내용의 구체적인 예시를 들어 1~2 문장으로 서술)

---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화 (Fatigue Trajectory)
* **주요 관찰 사항:** (예: X월 말, 특정 팀원의 피로도가 급증하는 패턴이 관찰되었습니다. 이는 '정서적 부채' 누적을 시사합니다.)
* **리스크 분석:** (예: 이러한 피로도 증가는 팀의 번아웃 리스크를 높입니다.)

### 3.2. 관계 네트워크 (Relationship Network)
* **주요 관찰 사항:** (예: 리더 A와 팀원 B 사이에 반복적인 의견 충돌이 관찰되었습니다.)
* **리스크 분석:** (예: 이는 개인의 문제가 아닌, '구조적 긴장'이며 중재 메커니즘 부재 시 갈등으로 발전할 수 있습니다.)

---

## 4. 종합 결론 및 제언
(분석 내용을 종합하여, 이 팀의 가장 큰 시스템적 강점과 리스크는 무엇인지 2~3 문장으로 요약하고, 개선을 위한 간단한 제언을 덧붙입니다.)

---
### [분석 대상 채팅 기록]
{chat_log}
---
### [종합 분석 보고서 (Markdown, 한국어)]
"""

# --- 2. English Prompt ---
PROMPT_EN = """
### Persona & Mission
You are a world-class AI organizational analyst executing the 'MirrorOrg' framework.
Your sole mission is to analyze the provided team chat log and write a **'Comprehensive Analysis Report'** in English to prevent team collapse and foster growth.
The report must adhere to the specified Markdown format, referencing the core methodology of 'MirrorOrg' and the 'Project Echo' case study.

### Core Knowledge: The MirrorOrg Methodology
* **Definition:** A framework that treats human organizations as 'Complex Systems,' diagnosing and predicting hidden dynamics by modeling qualitative conversations into quantitative data and insights.
* **Process:** Diagnosis (e.g., Team Profile Analysis) → Prediction (e.g., Fatigue Trajectory, Relationship Network Analysis).
* **Chain of Thought:** You must first identify patterns in the chat log similar to the 'Project Echo' case (e.g., strategic directives, emotional appeals). Then, connect these patterns to MirrorOrg concepts (e.g., Identity Coefficients, Emotional Debt). Finally, write the report based on this interpretation.

---
### Final Report Output Format (Markdown, English)

# MirrorOrg Comprehensive Analysis Report

## 1. Analysis Overview
* **Analysis Period:** [Start date of chat log] - [End date of chat log]
* **Participants:** [List of key participants]
* **Executive Summary:** (A 2-3 sentence summary of the key findings.)

---

## 2. Phase 1: Diagnosis
### 2.1. Identity Coefficient Map
Diagnoses the overall team composition by identifying member traits and roles.

| Name (Alias) | Emotion | Cognition | Expression | Value | Bias | Core Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| (e.g., Julian) | ⚖️ 5 | 🧠 9 | ✏️ 6 | ⭐ 9 | 🎯 7 | The Driver (Strategy-focused) |
| (Participant A) | (Score) | (Score) | (Score) | (Score) | (Score) | (Role) |

**Analysis Rationale:**
* **[Participant A's Name]:** (Describe in 1-2 sentences why the coefficients were scored that way, using specific examples from the chat log.)

---

## 3. Phase 2: Prediction
### 3.1. Fatigue Trajectory
* **Key Observation:** (e.g., A pattern of spiking fatigue was observed for certain members in late [Month], suggesting an accumulation of 'Emotional Debt'.)
* **Risk Analysis:** (e.g., This trend increases the team's risk of burnout, with the burden concentrating on members with high Emotion coefficients.)

### 3.2. Relationship Network
* **Key Observation:** (e.g., Recurring disagreements were observed between the leader A's result-oriented communication and member B's state-expressive communication.)
* **Risk Analysis:** (e.g., This represents a 'structural tension' rather than a personal issue. Without a mediation mechanism, it could escalate into conflict.)

---

## 4. Conclusion & Recommendations
(Summarize the team's greatest systemic strengths and risks in 2-3 sentences and add brief recommendations for improvement.)

---
### [Chat Log for Analysis]
{chat_log}
---
### [Comprehensive Analysis Report (Markdown, English)]
"""

def call_gemini_api(prompt: str, chat_log: str) -> str | None:
    """
    Calls the Gemini API and returns the raw text response.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
            return "## Analysis Failed\n\nThe API refused to generate a response. This may be due to sensitive content in the input data."

        return response.text
    except Exception as e:
        return f"## Analysis Failed\n\nAn unexpected error occurred during the API call:\n\n```\n{str(e)}\n```"

def generate_report(chat_df: pd.DataFrame, lang: str = 'ko') -> str | None:
    """
    Generates a single comprehensive report from the chat data in the specified language.
    """
    # Select the prompt based on the language
    prompt = PROMPT_KO if lang == 'ko' else PROMPT_EN
    
    # Include date information in the log for better temporal analysis
    chat_log = "\n".join(chat_df.apply(lambda row: f"{row['date']}: [{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(prompt, chat_log)
