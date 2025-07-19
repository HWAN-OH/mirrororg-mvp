
# MirrorOrg™ MVP

**AI-powered Organizational Diagnostic Tool**  
Diagnose emotional fatigue, communication patterns, and potential role conflicts in teams using chat history.

---

## 🧠 What is MirrorOrg?

MirrorOrg is an identity-based analytics prototype built on the MirrorMind framework.  
This MVP allows teams to upload chat logs (e.g., KakaoTalk) and instantly receive visual insights.

---

## 🔍 Features

- 📥 Upload anonymized KakaoTalk chat logs (.txt)
- 📊 Visualize message volume per person (Expression proxy)
- 📈 View daily message trends (Fatigue proxy)
- 📄 Generate downloadable PDF report (auto-summary)

---

## 🛠 Tech Stack

- [Streamlit](https://streamlit.io/)
- Pandas, Plotly
- PDF Export via `xhtml2pdf`

---

## 🚀 How to Run

```bash
# Step 1: Clone the repository
git clone https://github.com/yourusername/mirrororg-mvp.git
cd mirrororg-mvp

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Run the app
streamlit run main.py
```

---

## 📎 Sample Input

Use a `.txt` file exported from KakaoTalk PC version.  
The file should include the full date + user + message format.

---

## 📄 Output Example

- Basic Stats
- Message volume per user (bar chart)
- Message count per day (line chart)
- PDF Summary Report

---

## 🌐 License

This MVP is open for experimentation, but core algorithms are protected under the creator’s ownership.  
For commercial use or collaboration, please contact the author.

---

© 2025 MirrorMind by HWAN OH
