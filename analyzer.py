# analyzer.py
# 역할: 파싱된 데이터를 받아 LLM API와 통신하고, 분석 결과를 생성합니다.
# 최종 버전: '요약' 단계를 폐기하고, 각 프롬프트를 가장 단순하고 직접적인 명령으로 재구성하여 AI의 작업 부하를 최소화합니다.

import google.generativeai as genai
import json
import pandas as pd
import re

# --- [Delta] Radically Simplified Prompts ---

PROMPT_TEAM_PROFILE = """
### TASK
Analyze the provided chat log to determine the 5 Identity Coefficients for each participant.

### RULES
1.  Identify all participants.
2.  For each person, score Emotion, Cognition, Expression, Value, and Bias on a scale of 1-10.
3.  Assign a Core Role based on the scores.
4.  You MUST respond with ONLY a valid JSON array, exactly like the example. Do not include any other text or explanations.

### EXAMPLE OUTPUT
```json
[
  {"name": "라이언", "emotion_score": 3, "cognition_score": 8, "expression_score": 9, "value_score": 7, "bias_score": 6, "core_role": "The Driver"},
  {"name": "어피치", "emotion_score": 8, "cognition_score": 4, "expression_score": 7, "value_score": 3, "bias_score": 5, "core_role": "The Empath"}
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
1.  Fatigue is scored from 1 (very low) to 10 (burnout).
2.  Estimate a score for each person for each day present in the log.
3.  You MUST respond with ONLY a valid JSON object where keys are dates (YYYY-MM-DD), exactly like the example.

### EXAMPLE OUTPUT
```json
{
  "2025-07-20": {
    "라이언": 5,
    "어피치": 9
  },
  "2025-07-21": {
    "라이언": 3,
    "어피치": 4
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
1.  All participants are nodes.
2.  Interactions between them are edges.
3.  Classify each edge's relationship type as one of: `high_risk`, `medium_risk`, `potential_risk`, `stable`.
4.  You MUST respond with ONLY a valid JSON object with "nodes" and "edges" keys, exactly like the example.

### EXAMPLE OUTPUT
```json
{
  "nodes": [
    {"id": "라이언", "label": "라이언"},
    {"id": "어피치", "label": "어피치"}
  ],
  "edges": [
    {"from": "라이언", "to": "어피치", "type": "medium_risk"}
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

def analyze_profile(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_TEAM_PROFILE, chat_log)

def analyze_timeline(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_FATIGUE_TIMELINE, chat_log)

def analyze_network(chat_df: pd.DataFrame) -> dict | list | str | None:
    chat_log = "\n".join(chat_df.apply(lambda row: f"[{row['speaker']}] {row['message']}", axis=1))
    return call_gemini_api(PROMPT_CONFLICT_NETWORK, chat_log)

