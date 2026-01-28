import webbrowser, requests, os
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("UPSTOX_API_KEY")
SECRET   = os.getenv("UPSTOX_SECRET")
REDIRECT = "http://127.0.0.1:8000/callback"

print("=" * 52)
print("   UPSTOX TOKEN REFRESH")
print("=" * 52)
print()
print("Step 1: Opening browser for Upstox login...")
print()

url = (
    f"https://api.upstox.com/v2/login/authorization/dialog"
    f"?client_id={API_KEY}"
    f"&redirect_uri={REDIRECT}"
    f"&response_type=code"
)
webbrowser.open(url)

print("Step 2: After login, Upstox redirects to:")
print(f"  http://127.0.0.1:8000/callback?code=XXXXXX")
print()
print("Copy ONLY the code value after '?code='")
print()

code = input("Paste the code here: ").strip()

print()
print("Fetching new access token...")

resp = requests.post(
    "https://api.upstox.com/v2/login/authorization/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "code":          code,
        "client_id":     API_KEY,
        "client_secret": SECRET,
        "redirect_uri":  REDIRECT,
        "grant_type":    "authorization_code"
    }
)

data = resp.json()
token = data.get("access_token")

if token:
    # Update .env file automatically
    env_path = os.path.join(os.getcwd(), ".env")
    with open(env_path, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("UPSTOX_ACCESS_TOKEN="):
            new_lines.append(f"UPSTOX_ACCESS_TOKEN={token}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"UPSTOX_ACCESS_TOKEN={token}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)

    print()
    print("Token updated in .env successfully!")
    print(f"Preview: {token[:40]}...")
    print()
    print("Restart your backend server now:")
    print("  uvicorn backend.main:app --reload --port 8000")
else:
    print()
    print("Error getting token:", data.get("message", data))
    print("Try again or check API key and secret in .env")