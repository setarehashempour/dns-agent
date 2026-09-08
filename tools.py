import socket
import ssl
import urllib.request
import dns.resolver

def check_dns_records(domain: str) -> dict:
    """استعلام رکوردهای وب با پشتیبانی از نمایش کامل تمام NSها"""
    records = {"A": [], "AAAA": [], "CNAME": [], "NS": []}
    
    resolver = dns.resolver.Resolver(configure=True)
    resolver.timeout = 3
    resolver.lifetime = 3

    if domain.endswith('.ir'):
        resolver.nameservers = ['185.51.200.2', '185.51.200.1', '1.1.1.1', '8.8.8.8']
    else:
        resolver.nameservers = ['8.8.8.8', '1.1.1.1', '4.2.2.4']

    for record_type in records.keys():
        success = False
        try:
            answers = resolver.resolve(domain, record_type)
            if record_type == "NS":
                # استخراج تمام نیم‌سرورها به جای فقط یک مورد
                records[record_type] = [str(rdata.target).rstrip('.') for rdata in answers]
            else:
                records[record_type] = [str(rdata) for rdata in answers]
            success = True
        except Exception:
            pass

        if not success and domain.endswith('.ir'):
            try:
                fallback_resolver = dns.resolver.Resolver(configure=True)
                fallback_resolver.timeout = 2
                fallback_resolver.lifetime = 2
                answers = fallback_resolver.resolve(domain, record_type)
                if record_type == "NS":
                    records[record_type] = [str(rdata.target).rstrip('.') for rdata in answers]
                else:
                    records[record_type] = [str(rdata) for rdata in answers]
            except Exception:
                pass

    return records

def check_port_status(domain: str, port: int) -> dict:
    try:
        with socket.create_connection((domain, port), timeout=3):
            return {"port": port, "status": "open"}
    except Exception:
        return {"port": port, "status": "closed_or_filtered"}

def detect_cdn(domain: str) -> dict:
    cdn_signatures = {
        "IranServer / MizbanCloud": ["mizbancloud", "iranserver", "mizban", "f95.com", "mizbancloud.com"],
        "ArvanCloud": ["arvancloud", "arvan", "x-arvan-cloud", "arvancloud.ir", "ns-arvan"],
        "Derak Cloud": ["derakcloud", "derak.cloud", "derak"],
        "ParsPack CDN": ["parspack"],
        "Cloudflare": ["cloudflare", "cf-ray"],
        "Akamai": ["akamai", "akamaized"],
        "Amazon CloudFront": ["cloudfront"],
        "Fastly": ["fastly"],
        "Imperva / Incapsula": ["incapsula"]
    }

    detected_cdns = []
    server_header = "Unknown"

    try:
        ns_answers = dns.resolver.resolve(domain, 'NS')
        for rdata in ns_answers:
            ns_str = str(rdata.target).lower()
            for provider, sigs in cdn_signatures.items():
                if any(sig in ns_str for sig in sigs):
                    if provider not in detected_cdns:
                        detected_cdns.append(provider)
    except Exception:
        pass

    try:
        cname_answers = dns.resolver.resolve(domain, 'CNAME')
        for rdata in cname_answers:
            cname_str = str(rdata.target).lower()
            for provider, sigs in cdn_signatures.items():
                if any(sig in cname_str for sig in sigs):
                    if provider not in detected_cdns:
                        detected_cdns.append(provider)
    except Exception:
        pass

    for proto in ["https://", "http://"]:
        try:
            req = urllib.request.Request(
                f"{proto}{domain}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=4, context=ctx) as response:
                headers = dict(response.headers)
                server_header = headers.get("Server", headers.get("server", "Unknown"))

                headers_str = str(headers).lower()
                for provider, sigs in cdn_signatures.items():
                    if any(sig in headers_str for sig in sigs):
                        if provider not in detected_cdns:
                            detected_cdns.append(provider)
            break
        except Exception:
            continue

    return {
        "cdn_detected": len(detected_cdns) > 0,
        "providers": detected_cdns if detected_cdns else ["None / Direct Server"],
        "server_header": server_header
    }
