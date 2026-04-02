import re
from bs4 import BeautifulSoup

def analyze():
    with open("atc_ad_grid_dom.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Check all <a> tags
    all_a = soup.find_all("a")
    print(f"Total <a> tags: {len(all_a)}")
    
    hrefs = [a.get("href") for a in all_a if a.get("href")]
    print("Sample hrefs:")
    for h in set(hrefs):
        print("  " + h)
        
    # Check for custom attributes that might contain URLs
    # Google often uses properties like 'jsdata' or data attributes
    urls_in_text = re.findall(r'https?://[^\s"\'<>]+', html)
    
    # Filter out google, youtube, w3.org, etc.
    filtered = set()
    for u in urls_in_text:
        if "google" not in u and "youtube" not in u and "w3.org" not in u and "gstatic" not in u:
            filtered.add(u[:80])
            
    print(f"\nFound {len(filtered)} unique external-looking URLs in raw HTML text.")
    print("Samples:")
    for u in list(filtered)[:20]:
        print("  " + u)

if __name__ == "__main__":
    analyze()
