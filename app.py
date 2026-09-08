import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from openai import OpenAI
from agent_config import SYSTEM_PROMPT, TOOLS_SCHEMA
from tools import check_dns_records, check_port_status, detect_cdn
from guardrails import validate_user_input

# --- توابع کمکی خروجی‌گرفتن و ارسال گزارش ---
def convert_markdown_to_html(text: str) -> str:
    """تبدیل علامت‌های مارک‌داون ایجنت به کدهای واقعی HTML"""
    try:
        import markdown
        return markdown.markdown(text, extensions=['tables', 'fenced_code', 'nl2br'])
    except Exception:
        import re
        html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = re.sub(r'### (.*)', r'<h3>\1</h3>', html)
        html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        return html.replace('\n', '<br>')

def generate_html_report(report_text: str, domain: str) -> str:
    """تولید فایل HTML شکیل و مرتب برای دانلود و چاپ PDF"""
    parsed_content = convert_markdown_to_html(report_text)
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <title>گزارش عیب‌یابی شبکه - {domain}</title>
    <style>
        body {{ 
            font-family: Tahoma, Arial, sans-serif; 
            padding: 30px; 
            background: #0f172a; 
            color: #f8fafc; 
            line-height: 1.8; 
            direction: rtl;
            text-align: right;
        }}
        h3 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 8px; margin-top: 25px; }}
        .content {{ background: #1e293b; padding: 25px; border-radius: 10px; border: 1px solid #334155; }}
        code {{ 
            direction: ltr; 
            display: inline-block; 
            background: #0f172a; 
            color: #38bdf8; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-family: monospace; 
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
            background: #0f172a; 
            border-radius: 8px; 
            overflow: hidden; 
        }}
        th, td {{ 
            border: 1px solid #334155; 
            padding: 12px; 
            text-align: right; 
            word-break: break-word; 
        }}
        th {{ background: #2563eb; color: #ffffff; font-weight: bold; }}
        tr:nth-child(even) {{ background: #1e293b; }}
        .btn {{ 
            display: inline-block; 
            background: #0284c7; 
            color: white; 
            padding: 12px 24px; 
            border-radius: 6px; 
            border: none; 
            font-size: 15px; 
            margin-top: 20px; 
            cursor: pointer; 
            font-weight: bold;
        }}
        .btn:hover {{ background: #0369a1; }}
        @media print {{ 
            body {{ background: #ffffff; color: #000000; padding: 10px; }} 
            .content {{ background: #ffffff; border: 1px solid #ccc; color: #000000; }} 
            th {{ background: #e2e8f0; color: #000000; }}
            td {{ border-color: #cbd5e1; }}
            code {{ background: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; }}
            .btn {{ display: none; }} 
        }}
    </style>
</head>
<body>
    <h2>📊 گزارش عیب‌یابی شبکه و DNS برای: {domain}</h2>
    <div class="content">{parsed_content}</div>
    <button class="btn" onclick="window.print()">🖨️ چاپ یا ذخیره به‌صورت PDF</button>
</body>
</html>"""

def send_telegram_report(report_text: str, bot_token: str, chat_id: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"📊 <b>گزارش عیب‌یابی شبکه</b>\n\n{report_text[:3800]}",
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def send_email_report(to_email: str, domain: str, body_html: str, smtp_user: str, smtp_pass: str) -> bool:
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = f"گزارش عیب‌یابی شبکه - {domain}"
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

def render_export_section(report_text: str, domain: str, key_prefix: str = "exp"):
    """رندر دکمه‌های خروجی و اشتراک‌گذاری در UI Streamlit"""
    st.markdown("---")
    st.caption("📥 **خروجی و اشتراک‌گذاری گزارش:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        html_data = generate_html_report(report_text, domain)
        st.download_button(
            label="📄 دانلود HTML / PDF",
            data=html_data,
            file_name=f"dns_report_{domain}.html",
            mime="text/html",
            use_container_width=True,
            key=f"{key_prefix}_dl"
        )

    with col2:
        with st.popover("📤 ارسال به تلگرام", use_container_width=True):
            tg_token = st.text_input("توکن ربات تلگرام:", type="password", key=f"{key_prefix}_tgt")
            tg_chat = st.text_input("شناسه چت/کانال:", value="@my_channel", key=f"{key_prefix}_tgc")
            if st.button("ارسال تلگرام", key=f"{key_prefix}_tgb", use_container_width=True):
                if tg_token and tg_chat:
                    if send_telegram_report(report_text, tg_token, tg_chat):
                        st.success("با موفقیت ارسال شد!")
                    else:
                        st.error("خطا در ارسال تلگرام.")
                else:
                    st.warning("اطلاعات را کامل کنید.")

    with col3:
        with st.popover("✉️ ارسال به ایمیل", use_container_width=True):
            # دریافت ایمن تنظیمات از secrets بدون ایجاد کراش
            default_smtp_u = ""
            default_smtp_p = ""
            try:
                default_smtp_u = st.secrets.get("SMTP_USER", "")
                default_smtp_p = st.secrets.get("SMTP_PASS", "")
            except Exception:
                pass
            
            if not default_smtp_u:
                default_smtp_u = os.getenv("SMTP_USER", "")
            if not default_smtp_p:
                default_smtp_p = os.getenv("SMTP_PASS", "")

            target_email = st.text_input("ایمیل دریافت‌کننده:", key=f"{key_prefix}_em")
            smtp_u = st.text_input("ایمیل فرستنده (Gmail):", value=default_smtp_u, key=f"{key_prefix}_s_u")
            smtp_p = st.text_input("رمز برنامه (App Password):", value=default_smtp_p, type="password", key=f"{key_prefix}_s_p")

            if st.button("ارسال ایمیل", key=f"{key_prefix}_emb", use_container_width=True):
                if target_email and smtp_u and smtp_p:
                    html_c = generate_html_report(report_text, domain)
                    if send_email_report(target_email, domain, html_c, smtp_u, smtp_p):
                        st.success("ایمیل با موفقیت ارسال شد!")
                    else:
                        st.error("خطا در ارسال ایمیل. از صحت App Password اطمینان حاصل کنید.")
                else:
                    st.warning("لطفاً تمامی فیلدهای ایمیل را پر کنید.")

# --- پیکربندی صفحه ---
st.set_page_config(page_title="DNS & Network Diagnostic Agent", page_icon="🌐", layout="centered")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

    html, body, [class*="css"], .stMarkdown, p, div, h1, h2, h3, h4 {
        font-family: 'Vazirmatn', sans-serif !important;
    }

    .stChatMessage, div[data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        line-height: 1.8 !important;
    }

    code {
        direction: ltr !important;
        display: inline-block;
        font-family: 'Fira Code', monospace !important;
        background: #1e293b !important;
        color: #38bdf8 !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-weight: 600;
    }

    table {
        width: 100% !important;
        direction: rtl !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        margin: 15px 0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #334155 !important;
    }
    th {
        background: #2563eb !important;
        color: #ffffff !important;
        padding: 12px 14px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #1d4ed8 !important;
    }
    td {
        padding: 12px 14px !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        font-weight: 500 !important;
        border-bottom: 1px solid #334155 !important;
    }
    tr:last-child td {
        border-bottom: none !important;
    }
    table td {
        word-break: break-all !important;
        max-width: 410px;
        white-space: normal !important;
    }
    table td:nth-child(2) {
        white-space: nowrap !important;
        word-break: normal !important;
        min-width: 110px;
        text-align: center !important;
    }
    .status-box {
        direction: rtl !important;
        text-align: right !important;
        padding: 14px 18px !important;
        border-radius: 8px !important;
        margin: 15px 0 !important;
        font-weight: 500 !important;
        line-height: 1.7 !important;
    }

    .status-success {
        background-color: #064e3b !important;
        border-right: 5px solid #10b981 !important;
        color: #a7f3d0 !important;
    }

    .status-warning {
        background-color: #451a03 !important;
        border-right: 5px solid #f59e0b !important;
        color: #fde68a !important;
    }

    .status-danger {
        background-color: #450a0a !important;
        border-right: 5px solid #ef4444 !important;
        color: #fca5a5 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 WebCheck AI")
st.caption("Automated DNS records analysis, port status checks, and CDN detection")

AVAILABLE_TOOLS = {
    "check_dns_records": check_dns_records,
    "check_port_status": check_port_status,
    "detect_cdn": detect_cdn
}

api_key = os.getenv("AVALAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter AvalAI / OpenAI API Key:", type="password")

if st.sidebar.button("🗑️ پاکسازی گفتگو (Reset Chat)"):
    st.session_state["messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.pop("last_target_domain", None)
    st.rerun()

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# نمایش تاریخچه پیام‌ها
for idx, msg in enumerate(st.session_state.messages):
    role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
    content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)

    if role == "user":
        st.chat_message("user").write(content)
    elif role == "assistant" and content and not msg.get("tool_calls"):
        with st.chat_message("assistant"):
            st.markdown(content, unsafe_allow_html=True)
            if idx == len(st.session_state.messages) - 1:
                domain = st.session_state.get("last_target_domain", "target_domain")
                render_export_section(content, domain, key_prefix=f"hist_{idx}")

# دریافت ورودی جدید
if user_input := st.chat_input("پیام خود یا نام دامنه را وارد کنید..."):
    if not api_key:
        st.error("Please enter an API key in the sidebar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    is_valid, alert_msg, target_domain = validate_user_input(user_input)

    if target_domain:
        st.session_state["last_target_domain"] = target_domain

    if not is_valid:
        with st.chat_message("assistant"):
            st.warning(alert_msg)
        st.session_state.messages.append({"role": "assistant", "content": alert_msg})
    else:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.avalai.ir/v1"
        )

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            with st.spinner("🔍 در حال بررسی شبکه و تحلیل زیرساخت... لطفاً شکیبا باشید"):
                while True:
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=st.session_state.messages,
                            tools=TOOLS_SCHEMA,
                            tool_choice="auto"
                        )
                    except Exception as e:
                        st.error(f"API Connection Error: {e}")
                        break

                    response_message = response.choices[0].message
                    st.session_state.messages.append(response_message.model_dump())

                    if response_message.tool_calls:
                        for tool_call in response_message.tool_calls:
                            fn_name = tool_call.function.name
                            try:
                                fn_args = json.loads(tool_call.function.arguments)
                            except Exception:
                                fn_args = {}

                            tool_func = AVAILABLE_TOOLS.get(fn_name)
                            if tool_func:
                                tool_output = tool_func(**fn_args)
                            else:
                                tool_output = {"error": "Tool not found"}

                            st.session_state.messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": fn_name,
                                "content": json.dumps(tool_output)
                            })
                    else:
                        message_placeholder.markdown(response_message.content, unsafe_allow_html=True)
                        domain = st.session_state.get("last_target_domain", target_domain or "target_domain")
                        render_export_section(response_message.content, domain, key_prefix="live")
                        break
