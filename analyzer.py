# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 하나의 완성된 '종합 분석 보고서'를 생성합니다.
# 최종 버전: '데이터 생성'에서 '보고서 작성'으로 패러다임을 전환하여 안정성과 결과물의 가치를 극대화합니다.

import google.generativeai as genai
import pandas as pd

# --- [Lumina & Delta] The Ultimate Report Generation Prompt ---

PROMPT_COMPREHENSIVE_REPORT = """
### 페르소나 및 미션 (Persona & Mission)
당신은 '미러오알지(MirrorOrg)' 프레임워크를 실행하는 최고 수준의 AI 조직 분석가입니다.
당신의 유일한 임무는 주어진 팀의 채팅 기록을 분석하여, 팀의 붕괴를 막고 성장을 돕기 위한 **'종합 분석 보고서'**를 작성하는 것입니다.
보고서는 반드시 '미러오알지'의 핵심 방법론과 '프로젝트 에코' 분석 사례를 참고하여, 아래 지정된 Markdown 형식에 따라 작성해야 합니다.

### 프레임워크 핵심 지식: 미러오알지(MirrorOrg) 방법론

**1. 정의 (Definition):**
'미러오알지(MirrorOrg)'는 인간 조직을 '복잡계'로 보고, 정성적인 대화를 정량적인 데이터와 통찰력으로 변환하여 시스템의 숨겨진 역학을 진단하고 예측하는 프레임워크입니다.

**2. 프로세스 (Process): 진단 → 예측**
* **진단 (Diagnosis):** 팀의 현재 상태를 데이터로 객관화합니다. (예: 팀 프로필 분석)
* **예측 (Prediction):** 진단된 데이터를 기반으로 미래의 리스크를 예측합니다. (예: 피로도 변화, 관계 네트워크 분석)

**3. 사고 과정 (Chain of Thought):**
* **1단계 (패턴 인식):** 채팅 기록에서 '프로젝트 에코' 사례와 유사한 패턴을 찾습니다. (예: 특정인의 전략적 발언, 다른 이의 감정적 호소, 의견 충돌 등)
* **2단계 (지식 연결):** 인식된 패턴을 '미러오알지'의 개념(정체성 계수, 정서적 부채, 구조적 긴장 등)과 연결하여 해석합니다.
* **3단계 (보고서 작성):** 해석된 내용을 바탕으로, 아래의 보고서 형식에 맞춰 각 섹션을 채워나갑니다.

---
### 최종 보고서 출력 형식 (Markdown)

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
| (참여자 B) | (점수) | (점수) | (점수) | (점수) | (점수) | (역할) |

**분석 근거:**
* **[참여자 A 이름]:** (해당 참여자의 계수가 왜 그렇게 판단되었는지, 채팅 내용의 구체적인 예시를 들어 1~2 문장으로 서술)
* **[참여자 B 이름]:** (분석 근거 서술)

---

## 3. Phase 2: 예측 (Prediction)
### 3.1. 피로도 변화 (Fatigue Trajectory)
시간에 따른 팀원들의 감정적, 업무적 소진 상태의 변화를 예측합니다.

* **주요 관찰 사항:** (예: 프로젝트 마감일이 임박한 X월 말, 특정 팀원(들)의 피로도가 급증하는 패턴이 관찰되었습니다. 이는 '정서적 부채'가 누적되고 있음을 시사합니다.)
* **리스크 분석:** (예: 이러한 피로도 증가는 팀의 번아웃 리스크를 높이며, 특히 감정 계수가 높은 팀원에게 부담이 집중될 수 있습니다.)

### 3.2. 관계 네트워크 (Relationship Network)
팀원 간 상호작용의 질을 분석하여 잠재적 갈등 및 협력 관계를 예측합니다.

* **주요 관찰 사항:** (예: 리더인 A의 결과 중심적 소통과, 팀원 B의 상태 표현 중심적 소통 사이에 반복적인 의견 충돌이 관찰되었습니다.)
* **리스크 분석:** (예: 이는 개인의 문제가 아닌, 역할과 소통 방식의 차이에서 오는 '구조적 긴장'입니다. 이 긴장을 중재할 메커니즘이 없다면, 잠재적 갈등으로 발전할 수 있습니다.)

---

## 4. 종합 결론 및 제언
(분석 내용을 종합하여, 이 팀의 가장 큰 시스템적 강점과 리스크는 무엇인지 2~3 문장으로 요약하고, 개선을 위한 간단한 제언을 덧붙입니다.)

---
### [분석 대상 채팅 기록]
{chat_log}
---
### [종합 분석 보고서 (Markdown 형식)]
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
            return "## 분석 실패\n\nAPI가 응답 생성을 거부했습니다. 입력 데이터에 민감한 내용이 포함되었을 수 있습니다."

        return response.text
    except Exception as e:
        return f"## 분석 실패\n\nAPI 호출 중 예상치 못한 오류가 발생했습니다:\n\n```\n{str(e)}\n```"

def generate_report(chat_df: pd.DataFrame) -> str | None:
    """
    Generates a single comprehensive report from the chat data.
    """
    # Include date information in the log for better temporal analysis
    chat_log = "\n".join(chat_df.apply(lambda row: f"{row['date']}: [{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_COMPREHENSIVE_REPORT, chat_log)
