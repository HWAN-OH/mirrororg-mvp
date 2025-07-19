# parsers.py
# 역할: 업로드된 텍스트 파일을 파싱하여 표준화된 데이터프레임으로 변환합니다.

import re
from datetime import datetime
import pandas as pd

def parse_kakao(content: str) -> list[dict] | None:
    """
    Parses KakaoTalk chat history from an exported .txt file.
    """
    # KakaoTalk date line format: --------------- 2024년 7월 20일 토요일 ---------------
    pattern = re.compile(r"--------------- (\d{4}년 \d{1,2}월 \d{1,2}일) ")
    # KakaoTalk message format: [User Name] [오전/오후 H:MM] Message
    line_pattern = re.compile(r"\[(.+?)\] \[(오전|오후) \d{1,2}:\d{1,2}\] (.+)")
    
    chat_lines = content.split('\n')
    data = []
    current_date = None
    
    for line in chat_lines:
        date_match = pattern.match(line)
        if date_match:
            try:
                current_date_str = date_match.group(1)
                current_date = datetime.strptime(current_date_str, "%Y년 %m월 %d일").date()
            except ValueError:
                continue # Ignore lines that look like date lines but aren't
        elif current_date and line_pattern.match(line):
            try:
                match = line_pattern.match(line)
                speaker, _, message = match.groups()
                data.append({
                    "date": current_date,
                    "speaker": speaker,
                    "message": message.strip()
                })
            except (AttributeError, IndexError, ValueError):
                continue # Ignore malformed message lines
    
    return data if data else None

def detect_format(content: str) -> str:
    """
    Detects the chat format based on content patterns.
    Currently supports KakaoTalk.
    """
    # A very specific pattern for KakaoTalk date separators
    if re.search(r"--------------- \d{4}년 \d{1,2}월 \d{1,2}일 ", content):
        return "kakaotalk"
    # Add other format detections here in the future (e.g., Slack)
    return "unknown"

def parse(content: str) -> pd.DataFrame | None:
    """
    Main parsing function. Detects format and calls the appropriate parser.
    """
    detected_format = detect_format(content)

    if detected_format == "kakaotalk":
        parsed_data = parse_kakao(content)
    # Add other parsers here
    # elif detected_format == "slack":
    #     parsed_data = parse_slack(content)
    else:
        return None

    if not parsed_data:
        return None
        
    return pd.DataFrame(parsed_data)
