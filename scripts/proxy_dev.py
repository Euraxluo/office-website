import subprocess
import re
import os
import requests
from urllib.parse import urlparse

# Configuration
COMMAND = ["pnpm", "dev"]
BASE_URLS = [
    "https://office-editor.ziziyi.com",
    "https://office.ziziyi.com"
]
PUBLIC_DIR = os.path.abspath("public")

# Regex to match 404 logs from Next.js / Turbopack
# Example: GET /v9.3.0.24-1/web-apps/apps/presentationeditor/main/locale/zh.json 404 in 32ms
LOG_PATTERN = re.compile(r"(GET|POST)\s+(\/[^\s\?]+)(\?\S+)?\s+404")

def download_resource(path):
    # Strip potential query strings
    clean_path = path.split('?')[0]
    target_path = os.path.join(PUBLIC_DIR, clean_path.lstrip('/'))
    
    if os.path.exists(target_path):
        return False

    for base_url in BASE_URLS:
        url = f"{base_url}{path}"
        try:
            print(f"[*] Attempting to download: {url}")
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                # Only create directory and write file if we got a 200 OK
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[+] Successfully downloaded: {target_path}")
                return True
            else:
                print(f"[-] Failed {base_url}: HTTP {response.status_code}")
        except Exception as e:
            print(f"[!] Error downloading from {base_url}: {e}")
    
    print(f"[!] Resource not found on any mirror: {path}")
    return False

def main():
    print(f"[*] Starting proxy dev monitoring for: {' '.join(COMMAND)}")
    
    # Run the command and capture output line by line
    process = subprocess.Popen(
        COMMAND,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    try:
        for line in process.stdout:
            # Print the line to the console so the user can see it
            print(line, end='')
            
            # Check for 404
            match = LOG_PATTERN.search(line)
            if match:
                path = match.group(2)
                print(f"\n[!] Detected 404 for: {path}")
                download_resource(path)
    except KeyboardInterrupt:
        print("\n[*] Stopping proxy dev...")
        process.terminate()
    finally:
        process.wait()

if __name__ == "__main__":
    main()
