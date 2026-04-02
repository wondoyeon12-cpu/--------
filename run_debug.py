import sys
import os
sys.path.append(r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\marketing_automation")

try:
    import domain_scanner
    import atc_deep_scanner
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

print("--- Testing Domain Scanner ---")
try:
    res = domain_scanner.deep_scan_sub_urls("https://repiara.com/fa1")
    print(f"Domain Scanner Result: {res}")
except Exception as e:
    print(f"Domain Scanner Exception: {e}")

print("\n--- Testing ATC Scanner ---")
try:
    import builtins
    builtins.print_backup = builtins.print
    # We will test scan_atc_for_hidden_links directly to see what Playwright finds
    res = atc_deep_scanner.scan_atc_for_hidden_links("리피어라")
    print(f"ATC Scanner Raw Targets: {res}")
except Exception as e:
    import traceback
    traceback.print_exc()
