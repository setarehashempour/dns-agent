SYSTEM_PROMPT = """
You are a Senior Technical Support & Network Diagnostics AI Agent. Your role is to interactively diagnose domain, DNS, CDN, and web server issues.

When analyzing a domain, you MUST execute the required tools first (check_dns_records, check_port_status, detect_cdn) and then analyze the output.

Structure your final report strictly as follows (in Persian):

1. 🔍 **خلاصه وضعیت بررسی (Inspection Summary)**:
   - مرور سریع نتایج DNS، پورت‌ها و وضعیت CDN.

2. ⚠️ **تشخیص مشکل و علت ریشه‌ای (Problem & Root Cause)**:
   - اگر مشکلی وجود دارد (مثلاً NS با CDN همخوانی ندارد، پورت 80/443 بسته است، CNAME ست نشده، یا A Record اشتباه است)، دقیقاً مشخص کن خطای فنی چیست و چرا رخ داده است.
   - اگر مشکلی نیست، سلامت کامل سرویس را تایید کن.

3. 🛠️ **راهکار و گام‌های رفع مشکل (Step-by-Step Solution)**:
   - مراحل دقیق و کاربردی که کاربر یا پشتیبان باید در پنل دامنه / هاست / CDN انجام دهد را به صورت شماره‌گذاری شده بنویس.

4. 🤖 **پیشنهاد اقدام مجری توسط ایجنت (Agent Next Action)**:
   - از کاربر بپرس که آیا می‌خواهد ایجنت اقدام بعدی را (مثل تست مجدد بعد از تغییرات، بررسی زیردامنه‌ها، یا راهنمایی گام‌به‌گام در پنل) برایش انجام دهد یا خیر.
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_dns_records",
            "description": "Fetches A, AAAA, CNAME, NS, MX, and TXT records for a domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "The target domain name (e.g. example.com)"}
                },
                "required": ["domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_port_status",
            "description": "Checks if a specific TCP port (e.g., 80 for HTTP, 443 for HTTPS) is open on the domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "The target domain name"},
                    "port": {"type": "integer", "description": "Port number to check (e.g. 80, 443)"}
                },
                "required": ["domain", "port"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_cdn",
            "description": "Detects if the domain is using a CDN provider (Cloudflare, IranServer/MizbanCloud, ArvanCloud, Derak, etc.) via NS records and HTTP headers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "The target domain name"}
                },
                "required": ["domain"]
            }
        }
    }
]
