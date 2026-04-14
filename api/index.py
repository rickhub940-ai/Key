import os, random, string, base64, json, requests
from flask import Flask, request, Response

app = Flask(__name__)

# ตัวแปรใน RAM สำหรับเก็บสถานะ Token
PENDING_TOKENS = {}  # {token: (key, hwid)}
USED_TOKENS = set()  # เก็บ Token ที่ใช้โหลดไฟล์ไปแล้ว

def generate_token():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

def get_github_content(path):
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("REPO_OWNER")
    repo = os.getenv("REPO_NAME")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        decoded = base64.b64decode(data['content']).decode('utf-8')
        return (json.loads(decoded) if path.endswith('.json') else decoded), data['sha']
    return None, None

@app.route('/')
def handle():
    u_key = request.args.get('key')
    u_hwid = request.args.get('hwid')
    u_token = request.args.get('token')

    # --- ด่านที่ 2: การขอรับไฟล์ Main Script ---
    if u_token:
        # 1. เช็คว่าใช้ซ้ำไหม
        if u_token in USED_TOKENS:
            return Response("game.Players.LocalPlayer:Kick('Rick Hub: This token has already been used!')", mimetype='text/plain')
        
        # 2. เช็คความถูกต้อง
        if u_token in PENDING_TOKENS and PENDING_TOKENS[u_token] == (u_key, u_hwid):
            # ทำลาย Token ทันที! (ย้ายไปหมวดใช้แล้ว)
            USED_TOKENS.add(u_token)
            del PENDING_TOKENS[u_token]
            
            # ดึงสคริปต์หลักมาส่งให้
            main_code, _ = get_github_content("main_script.lua")
            return Response(main_code or "print('Error: Main Missing')", mimetype='text/plain')
        
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid or Expired Token')", mimetype='text/plain')

    # --- ด่านที่ 1: ตรวจสอบ Whitelist และเจน Token ใหม่ ---
    whitelist, _ = get_github_content("whitelist.json")
    if not whitelist or u_key not in whitelist.get("keys", {}):
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Key')", mimetype='text/plain')

    # เช็ค HWID (ถ้าใน JSON มีค่าอยู่แล้วต้องตรงกัน)
    stored_hwid = whitelist["keys"][u_key].get("hwid")
    if stored_hwid and stored_hwid != "null" and stored_hwid != u_hwid:
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: HWID Mismatch')", mimetype='text/plain')

    # เจน Token ใหม่สำหรับด่านสอง
    new_token = generate_token()
    PENDING_TOKENS[new_token] = (u_key, u_hwid)

    # ส่ง Bridge ที่มี Token นี้ฝังอยู่กลับไป
    bridge_code = f"""
    local k, h, t = "{u_key}", "{u_hwid}", "{new_token}"
    local url = "https://your-app.vercel.app/?key="..k.."&hwid="..h.."&token="..t
    local success, result = pcall(function() return game:HttpGet(url) end)
    if success then loadstring(result)() end
    """
    return Response(bridge_code, mimetype='text/plain')
    
