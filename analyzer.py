# analyzer.py
# 역할: 원본 채팅 기록을 직접 분석하여, 각 시각화에 필요한 데이터를 개별적으로 생성합니다.
# 최종 버전: 프롬프트를 극도로 단순화하여 LLM의 작업 부하를 최소화하고, 데이터 생성에만 집중하도록 합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Delta & Lumina] Radically Simplified & Direct Prompts ---

PROMPT_TEAM_PROFILE = """
### TASK
Analyze the provided chat log to determine the 5 Identity Coefficients and a Core Role for each participant.

### RULES
1.  Identify all unique participants from the chat log.
2.  For each person, score the following coefficients on a scale of 1-10: `emotion_score`, `cognition_score`, `expression_score`, `value_score`, `bias_score`.
3.  Assign a concise `core_role` based on their communication patterns (e.g., "The Driver", "The Mediator", "The Empath").
4.  Your response MUST be ONLY a valid JSON array. Do not include any text, explanations, or markdown formatting before or after the JSON.

### EXAMPLE OUTPUT FORMAT
```json
[
  {
    "name": "Participant A",
    "emotion_score": 5,
    "cognition_score": 9,
    "expression_score": 6,
    "value_score": 9,
    "bias_score": 7,
    "core_role": "The Driver"
  }
]
```

### CHAT LOG TO ANALYZE
{chat_log}
---
### JSON OUTPUT
"""

PROMPT_FATIGUE_TIMELINE = """
### TASK
Analyze the provided chat log to estimate the daily fatigue level for each participant.

### RULES
1.  Fatigue is scored from 1 (very low) to 10 (near burnout).
2.  Estimate a score for each person for each day they are mentioned or active in the log.
3.  Your response MUST be ONLY a valid JSON object where keys are dates in "YYYY-MM-DD" format. Do not include any text, explanations, or markdown formatting before or after the JSON.

### EXAMPLE OUTPUT FORMAT
```json
{
  "2023-10-20": {
    "Participant A": 5,
    "Participant B": 9
  },
  "2023-10-21": {
    "Participant A": 3,
    "Participant B": 4
  }
}
```

### CHAT LOG TO ANALYZE
{chat_log}
---
### JSON OUTPUT
"""

PROMPT_CONFLICT_NETWORK = """
### TASK
Analyze the provided chat log to model the relationships between participants as a network graph.

### RULES
1.  All participants are nodes. An interaction between two people is an edge.
2.  Classify each edge's relationship `type` as one of the following strings: "high_risk", "medium_risk", "potential_risk", "stable".
3.  Your response MUST be ONLY a valid JSON object with "nodes" and "edges" keys. Do not include any text, explanations, or markdown formatting before or after the JSON.

### EXAMPLE OUTPUT FORMAT
```json
{
  "nodes": [
    {"id": "Participant A", "label": "Participant A"},
    {"id": "Participant B", "label": "Participant B"}
  ],
  "edges": [
    {"from": "Participant A", "to": "Participant B", "type": "medium_risk"}
  ]
}
```

### CHAT LOG TO ANALYZE
{chat_log}
---
### JSON OUTPUT
"""

def call_gemini_api(prompt: str, chat_log: str) -> dict | list | str | None:
    """
    Calls the Gemini API. If JSON parsing fails, returns the raw text for debugging.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        safety_settings = [{"category": f"HARM_CATEGORY_{cat}", "threshold": "BLOCK_NONE"} for cat in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        full_prompt = prompt.format(chat_log=chat_log)
        response = model.generate_content(full_prompt, safety_settings=safety_settings)

        if not response.parts:
            return {"error": "API response was blocked or empty."}

        raw_text = response.text
        match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
        json_text = match.group(1) if match else raw_text.strip()
        
        if not json_text:
            return {"error": "API returned an empty response after cleaning."}
            
        return json.loads(json_text)
    except json.JSONDecodeError:
        return raw_text 
    except Exception as e:
        return {"error": f"An unexpected API error occurred: {str(e)}"}

def analyze_profile(raw_chat_content: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_TEAM_PROFILE, raw_chat_content)

def analyze_timeline(raw_chat_content: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_FATIGUE_TIMELINE, raw_chat_content)

def analyze_network(raw_chat_content: str) -> dict | list | str | None:
    return call_gemini_api(PROMPT_CONFLICT_NETWORK, raw_chat_content)
