import socket
import dns.resolver
import requests

def check_dns_records(domain: str) -> dict:
    """استعلام دقیق رکوردهای اصلی DNS بدون وابستگی به dig"""
    records = {}
    record_types = ['A', 'AAAA', 'CNAME', 'NS', 'MX', 'TXT']
    
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records[rtype] = [str(rdata) for rdata in answers]
        except Exception:
            records[rtype] = []
    return records

def check_port_status(domain: str, port: int = 80, timeout: int = 3) -> dict:
    """تست اتصال به پورت‌های کلیدی سرور (Read-Only)"""
    try:
        sock = socket.create_connection((domain, port), timeout=timeout)
        sock.close()
        return {"port": port, "status": "open"}
    except Exception as e:
        return {"port": port, "status": "closed", "error": str(e)}

def detect_cdn(domain: str) -> dict:
    """تشخیص حضور CDN از روی هدرهای پاسخ HTTP (پشتیبانی از ارائه‌دهندگان ایرانی و خارجی)"""
    try:
        response = requests.get(f"http://{domain}", timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        server_header = response.headers.get("Server", "").lower()
        
        # دیکشنری نگاشت هدر سرور به نام کامل CDN
        cdn_providers = {
            "mizbancloud": "IranServer / MizbanCloud (میزبان کلود)",
            "iranserver": "IranServer (ایران سرور)",
            "arvancloud": "ArvanCloud (آروان کلود)",
            "derak": "Derak Cloud (درک کلود)",
            "parspack": "ParsPack (پارس پک)",
            "hostiran": "HostIran (هاست ایران)",
            "cloudflare": "Cloudflare",
            "sucuri": "Sucuri",
            "akamai": "Akamai",
            "fastly": "Fastly"
        }
        
        detected_cdn_name = "Unknown"
        is_cdn = False
        
        for key, name in cdn_providers.items():
            if key in server_header:
                is_cdn = True
                detected_cdn_name = name
                break
                
        return {
            "cdn_detected": is_cdn,
            "cdn_name": detected_cdn_name if is_cdn else "بدون CDN / سرور مستقیم",
            "server_header": response.headers.get("Server", "Unknown")
        }
    except Exception as e:
        return {"cdn_detected": False, "cdn_name": "ناموفق در بررسی", "error": str(e)}
if __name__ == "__main__":
    test_domain = "google.com"
    print("=== 1. DNS Records ===")
    print(check_dns_records(test_domain))
    print("\n=== 2. Port 80 Status ===")
    print(check_port_status(test_domain, 80))
    print("\n=== 3. Port 443 Status ===")
    print(check_port_status(test_domain, 443))
    print("\n=== 4. CDN Detection ===")
    print(detect_cdn(test_domain))
