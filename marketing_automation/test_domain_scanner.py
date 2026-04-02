import domain_scanner

urls = ["https://news.healthystr.co.kr?g=nv6", "https://thepine.co.kr/smart/KCMIFf250812/NP_GDN_05_og_2_2"]
for u in urls:
    print(f"Scanning {u}")
    res = domain_scanner.deep_scan_sub_urls(u)
    print(f"Result: {res}")
