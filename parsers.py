{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/HWAN-OH/mirrororg-mvp/blob/main/parsers.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "# parsers.py\n",
        "# 역할: 업로드된 텍스트 파일을 파싱하여 표준화된 데이터프레임으로 변환합니다.\n",
        "\n",
        "import re\n",
        "from datetime import datetime\n",
        "import pandas as pd\n",
        "\n",
        "def parse_kakao(content: str) -> list[dict] | None:\n",
        "    \"\"\"\n",
        "    Parses KakaoTalk chat history from an exported .txt file.\n",
        "    \"\"\"\n",
        "    # KakaoTalk date line format: --------------- 2024년 7월 20일 토요일 ---------------\n",
        "    pattern = re.compile(r\"--------------- (\\d{4}년 \\d{1,2}월 \\d{1,2}일) \")\n",
        "    # KakaoTalk message format: [User Name] [오전/오후 H:MM] Message\n",
        "    line_pattern = re.compile(r\"\\[(.+?)\\] \\[(오전|오후) \\d{1,2}:\\d{1,2}\\] (.+)\")\n",
        "\n",
        "    chat_lines = content.split('\\n')\n",
        "    data = []\n",
        "    current_date = None\n",
        "\n",
        "    for line in chat_lines:\n",
        "        date_match = pattern.match(line)\n",
        "        if date_match:\n",
        "            try:\n",
        "                current_date_str = date_match.group(1)\n",
        "                current_date = datetime.strptime(current_date_str, \"%Y년 %m월 %d일\").date()\n",
        "            except ValueError:\n",
        "                continue # Ignore lines that look like date lines but aren't\n",
        "        elif current_date and line_pattern.match(line):\n",
        "            try:\n",
        "                match = line_pattern.match(line)\n",
        "                speaker, _, message = match.groups()\n",
        "                data.append({\n",
        "                    \"date\": current_date,\n",
        "                    \"speaker\": speaker,\n",
        "                    \"message\": message.strip()\n",
        "                })\n",
        "            except (AttributeError, IndexError, ValueError):\n",
        "                continue # Ignore malformed message lines\n",
        "\n",
        "    return data if data else None\n",
        "\n",
        "def detect_format(content: str) -> str:\n",
        "    \"\"\"\n",
        "    Detects the chat format based on content patterns.\n",
        "    Currently supports KakaoTalk.\n",
        "    \"\"\"\n",
        "    # A very specific pattern for KakaoTalk date separators\n",
        "    if re.search(r\"--------------- \\d{4}년 \\d{1,2}월 \\d{1,2}일 \", content):\n",
        "        return \"kakaotalk\"\n",
        "    # Add other format detections here in the future (e.g., Slack)\n",
        "    return \"unknown\"\n",
        "\n",
        "def parse(content: str) -> pd.DataFrame | None:\n",
        "    \"\"\"\n",
        "    Main parsing function. Detects format and calls the appropriate parser.\n",
        "    \"\"\"\n",
        "    detected_format = detect_format(content)\n",
        "\n",
        "    if detected_format == \"kakaotalk\":\n",
        "        parsed_data = parse_kakao(content)\n",
        "    # Add other parsers here\n",
        "    # elif detected_format == \"slack\":\n",
        "    #     parsed_data = parse_slack(content)\n",
        "    else:\n",
        "        return None\n",
        "\n",
        "    if not parsed_data:\n",
        "        return None\n",
        "\n",
        "    return pd.DataFrame(parsed_data)"
      ],
      "outputs": [],
      "execution_count": null,
      "metadata": {
        "id": "8GFLf1_Ina6R"
      }
    }
  ],
  "metadata": {
    "colab": {
      "provenance": [],
      "include_colab_link": true
    },
    "kernelspec": {
      "display_name": "Python 3",
      "name": "python3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 0
}