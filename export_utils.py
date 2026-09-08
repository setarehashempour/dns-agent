import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_html_report(report_text: str, domain: str) -> str:
    """تولید قالب HTML استاندارد با دکمه چاپ/ذخیره به PDF"""
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <title>گزارش عیب‌یابی شبکه - {domain}</title>
    <style>
        body {{ font-family: Tahoma, Arial, sans-serif; padding: 25px; background: #0f172a; color: #f8fafc; line-height: 1.8; }}
        h2 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
        .content {{ background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; }}
        .btn {{ display: inline-block; background: #0284c7; color: white; padding: 10px 20px; border-radius: 6px; border: none; font-size: 14px; margin-top: 15px; cursor: pointer; }}
        .btn:hover {{ background: #0369a1; }}
        @media print {{ 
            body {{ background: #ffffff; color: #000000; }} 
            .content {{ background: #ffffff; border: 1px solid #ccc; color: #000000; }} 
            .btn {{ display: none; }} 
        }}
    </style>
</head>
<body>
    <h2>📊 گزارش عیب‌یابی شبکه و DNS برای: {domain}</h2>
    <div class="content">{report_text}</div>
    <button class="btn" onclick="window.print()">🖨️ چاپ یا ذخیره به‌صورت PDF</button>
</body>
</html>"""

def send_telegram_report(report_text: str, bot_token: str, chat_id: str) -> bool:
    """ارسال گزارش به چت یا کانال تلگرام"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"📊 <b>گزارش جدید عیب‌یابی شبکه</b>\n\n{report_text[:3800]}",
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def send_email_report(to_email: str, domain: str, body_html: str, smtp_user: str, smtp_pass: str) -> bool:
    """ارسال ایمیل حاوی گزارش HTML"""
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
