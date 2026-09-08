# 🌐 Smart DNS & Network Diagnostic Agent

An AI-powered network troubleshooting agent built with Python, Streamlit, and AvalAI.

## 🚀 Features
- **ReAct Agent Architecture:** Powered by `gpt-4o-mini` via AvalAI.
- **Dynamic Tool Calling:** Live execution of `check_dns_records`, `check_port_status`, and `detect_cdn`.
- **Interactive UI:** Built with Streamlit featuring RTL layout and live execution status.

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone [https://github.com/setarehashempour/dns-agent.git](https://github.com/setarehashempour/dns-agent.git)
cd dns-agent
```
### 2. Set Up Virtual Environment

Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a .env file in the root directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the Application
```bash
streamlit run app.py
```


