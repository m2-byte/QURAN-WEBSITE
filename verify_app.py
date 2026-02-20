import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def check_url(path, description):
    try:
        response = requests.get(f"{BASE_URL}{path}", timeout=5)
        if response.status_code == 200:
            print(f"[PASS] {description} ({path})")
            return True
        else:
            print(f"[FAIL] {description} ({path}) - Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] {description} ({path}) - Could not connect. Is the app running?")
        return False
    except Exception as e:
        print(f"[FAIL] {description} ({path}) - Error: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Quran Website...")
    
    # Check for key files presence
    files_to_check = [
        "app.py",
        "templates/base.html",
        "templates/index.html",
        "templates/quran/index.html",
        "templates/quran/surah.html",
        "templates/hadith/index.html",
        "templates/hadith/reader.html",
        "static/css/main.css",
        "static/css/vip.css",
        "static/js/main.js",
        "static/js/vip.js",
        "data/adhkar.json"
    ]
    
    import os
    all_pass = True
    print("\n[FileType]  Path")
    print("-" * 40)
    
    for f in files_to_check:
        if os.path.exists(f):
            print(f"[OK]        {f}")
        else:
            print(f"[MISSING]   {f}")
            all_pass = False
            
    if all_pass:
        print("\n✅ All key files present.")
    else:
        print("\n❌ Some files are missing.")
