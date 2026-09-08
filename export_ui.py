import streamlit as st
from export_utils import generate_html_report, send_telegram_report, send_email_report

def render_export_section(report_text: str, domain: str):
    """افزودن دکمه‌های دانلود و ارسال به انتهای پاسخ ایجنت"""
    st.markdown("---")
    st.subheader("📥 دریافت و اشتراک‌گذاری گزارش")

    col1, col2, col3 = st.columns(3)

    # دانلود HTML/PDF
    with col1:
        html_data = generate_html_report(report_text, domain)
        st.download_button(
            label="📄 دانلود گزارش (HTML/PDF)",
            data=html_data,
            file_name=f"dns_report_{domain}.html",
            mime="text/html",
            use_container_width=True
        )

    # ارسال به تلگرام
    with col2:
        with st.popover("📤 ارسال به تلگرام", use_container_width=True):
            bot_token = st.text_input("توکن ربات تلگرام:", type="password")
            chat_id = st.text_input("شناسه چت/کانال:", value="@my_channel")
            if st.button("ارسال پیام", key="tg_btn", use_container_width=True):
                if bot_token and chat_id:
                    if send_telegram_report(report_text, bot_token, chat_id):
                        st.success("با موفقیت ارسال شد!")
                    else:
                        st.error("خطا در ارسال تلگرام.")
                else:
                    st.warning("لطفاً مشخصات را کامل کنید.")

    # ارسال به ایمیل
    with col3:
        with st.popover("✉️ ارسال به ایمیل", use_container_width=True):
            target_email = st.text_input("ایمیل دریافت‌کننده:")
            if st.button("ارسال ایمیل", key="mail_btn", use_container_width=True):
                if target_email:
                    # در پروژه واقعی مشخصات SMTP را از st.secrets می‌خوانیم
                    smtp_user = st.secrets.get("SMTP_USER", "")
                    smtp_pass = st.secrets.get("SMTP_PASS", "")
                    if smtp_user and smtp_pass:
                        html_content = generate_html_report(report_text, domain)
                        if send_email_report(target_email, domain, html_content, smtp_user, smtp_pass):
                            st.success("ایمیل ارسال شد!")
                        else:
                            st.error("خطا در ارسال ایمیل.")
                    else:
                        st.error("تنظیمات SMTP سرور فعال نیست.")
                else:
                    st.warning("ایمیل را وارد کنید.")
