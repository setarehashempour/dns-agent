import re

def extract_domain_or_ip(text: str) -> str | None:
    """استخراج دامنه یا IP معتبر از متن ورودی کاربر"""
    domain_pattern = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    
    match_domain = re.search(domain_pattern, text)
    if match_domain:
        return match_domain.group(0).lower()
        
    match_ip = re.search(ip_pattern, text)
    if match_ip:
        return match_ip.group(0)
        
    return None

def validate_user_input(user_input: str) -> tuple[bool, str, str | None]:
    """
    اعتبارسنجی ورودی کاربر قبل از ارسال به LLM
    خروجی: (مجاز بودن، پیام خطا/راهنما، دامنه یا آدرس استخراج‌شده)
    """
    text = user_input.strip()
    
    # ۱. بررسی ورودی‌های بسیار کوتاه یا خالی
    if len(text) < 3:
        return False, "لطفاً یک نام دامنه معتبر (مثلاً stellera.ir) یا سوال مرتبط با شبکه وارد کنید.", None
        
    extracted_target = extract_domain_or_ip(text)
    
    # ۲. لیست کلمات کلیدی تخصصی شبکه
    network_keywords = [
        'dns', 'ip', 'ping', 'port', 'cdn', 'mx', 'txt', 'spf', 'dkim', 'dmarc',
        'شبکه', 'دامنه', 'پورت', 'اسپم', 'سرور', 'قطعی', 'هدر', 'رکورد', 'ممیزی'
    ]
    
    has_keyword = any(kw in text.lower() for kw in network_keywords)
    
    # ۳. فیلتر ورودی‌های بی‌پایه (بدون دامنه و بدون کلمه کلیدی شبکه)
    if not extracted_target and not has_keyword:
        return (
            False, 
            "من دستیار تخصصی عیب‌یابی شبکه و DNS هستم. لطفاً یک نام دامنه معتبر ارسال کنید یا سوالی در زمینه دی‌ان‌اس و سرور بپرسید.", 
            None
        )
        
    return True, "OK", extracted_target

if __name__ == "__main__":
    # تست سریع گاردریل
    test_cases = [
        "سلام چطوری؟",
        "چرا ایمیل‌های stellera.ir اسپم میشن؟",
        "پورت 80 رو چک کن",
        "شعر حافظ بگو"
    ]
    
    for test in test_cases:
        valid, msg, target = validate_user_input(test)
        print(f"Input: '{test}' -> Valid: {valid} | Target: {target}")
