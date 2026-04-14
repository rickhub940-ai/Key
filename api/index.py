import os, random, string, base64, json, requests
from flask import Flask, request, Response

app = Flask(__name__)

# เก็บสถานะ Token ใน RAM (ใช้แล้วทิ้ง)
PENDING_TOKENS = {}  
USED_TOKENS = set()  

def generate_token():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

def get_github_content(path):
    try:
        token = os.getenv("GITHUB_TOKEN")
        owner = os.getenv("REPO_OWNER")
        repo = os.getenv("REPO_NAME")
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            decoded = base64.b64decode(data['content']).decode('utf-8')
            return json.loads(decoded) if path.endswith('.json') else decoded
    except Exception as e:
        print(f"Error fetching GitHub: {e}")
    return None

@app.route('/')
def handle():
    # รับค่าและตัดช่องว่างทิ้งป้องกัน Invalid Key จาก Space
    u_key = request.args.get('key', '').strip()
    u_hwid = request.args.get('hwid', '').strip()
    u_token = request.args.get('token', '').strip()

    # --- ด่านที่ 2: ดึงไฟล์สคริปต์หลัก (เช็ค Token) ---
    if u_token:
        if u_token in USED_TOKENS:
            return Response("game.Players.LocalPlayer:Kick('Rick Hub: Token Already Used!')", mimetype='text/plain')
        
        if u_token in PENDING_TOKENS and PENDING_TOKENS[u_token] == (u_key, u_hwid):
            USED_TOKENS.add(u_token)
            del PENDING_TOKENS[u_token]
            
            main_code = get_github_content("main_script.lua")
            return Response(main_code or "print('Error: Main Script Missing')", mimetype='text/plain')
        
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Session')", mimetype='text/plain')

    # --- ด่านที่ 1: ตรวจสอบ Whitelist และเจน Token ---
    whitelist = get_github_content("whitelist.json")
    
    # แก้ไข: เช็คโครงสร้าง JSON ให้ลึกถึง keys
    if not whitelist or "keys" not in whitelist:
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Database Error')", mimetype='text/plain')

    all_keys = whitelist.get("keys", {})
    
    if u_key not in all_keys:
        return Response(f"game.Players.LocalPlayer:Kick('Rick Hub: Invalid Key [{u_key}]')", mimetype='text/plain')

    # เช็ค HWID
    info = all_keys[u_key]
    stored_hwid = info.get("hwid")
    if stored_hwid and stored_hwid not in ["null", None, ""] and stored_hwid != u_hwid:
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: HWID Mismatch')", mimetype='text/plain')

    # ผ่านด่านแรก -> สร้าง One-Time Token
    new_token = generate_token()
    PENDING_TOKENS[new_token] = (u_key, u_hwid)

    # ส่ง Bridge Code กลับไป (ใส่ลิ้งค์คุณให้แล้ว)
    bridge_code = f"""
    local k, h, t = "{u_key}", "{u_hwid}", "{new_token}"
    local url = "https://key-eta-one.vercel.app/?key="..k.."&hwid="..h.."&token="..t
    local s, r = pcall(function() return game:HttpGet(url) end)
    if s then loadstring(r)() end
    """
    return Response(bridge_code, mimetype='text/plain')
    
