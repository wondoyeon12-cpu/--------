import traceback
import sys
import google_ads_extractor

try:
    res = google_ads_extractor.get_hidden_landing_urls_via_dorking('리피어라')
    print('Count:', len(res))
    for r in res:
        print(r)
except Exception as e:
    traceback.print_exc()
