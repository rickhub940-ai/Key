import os, random, string, base64, json, requests
from flask import Flask, request, Response

app = Flask(__name__)

# ตัวแปรใน RAM สำหรับเก็บสถานะ (ใช้แล้วทิ้ง)
# หมายเหตุ: ถ้า Vercel รีสตาร์ทค่าจะหาย แต่ปลอดภัยสำหรับการรันสคริปต์ใหม่
PENDING_TOKENS = {}  # {token: (key, hwid)}
USED_TOKENS = set()  # เก็บ Token ที่โหลดไฟล์ไปแล้ว

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
        return (json.loads(decoded) if path.endswith('.json') else decoded)
    return None

@app.route('/')
def handle():
    u_key = request.args.get('key')
    u_hwid = request.args.get('hwid')
    u_token = request.args.get('token')

    # --- ด่านที่ 2: ดึงไฟล์สคริปต์หลัก (เช็ค Token) ---
    if u_token:
        # เช็คว่า Token นี้เคยใช้ไปแล้วหรือยัง
        if u_token in USED_TOKENS:
            return Response("game.Players.LocalPlayer:Kick('Rick Hub: This token is expired or reused!')", mimetype='text/plain')
        
        # เช็คว่า Token ถูกต้องและตรงกับ Key/HWID ไหม
        if u_token in PENDING_TOKENS and PENDING_TOKENS[u_token] == (u_key, u_hwid):
            # ทำลาย Token ทันที!
            USED_TOKENS.add(u_token)
            del PENDING_TOKENS[u_token]
            
            # ดึงไฟล์หลักจาก GitHub มาส่งให้
            main_code = get_github_content("main_script.lua")
            return Response(main_code or "print('Error: Main Script Missing')", mimetype='text/plain')
        
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Session')", mimetype='text/plain')

    # --- ด่านที่ 1: ตรวจสอบ Whitelist และเจน Token ---
    whitelist = get_github_content("whitelist.json")
    if not whitelist or u_key not in whitelist.get("keys", {}):
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Key')", mimetype='text/plain')

    # เช็ค HWID (ถ้าใน JSON มีค่าที่ไม่ใช่ null ต้องตรงกัน)
    stored_hwid = whitelist["keys"][u_key].get("hwid")
    if stored_hwid and stored_hwid not in ["null", None] and stored_hwid != u_hwid:
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: HWID Mismatch')", mimetype='text/plain')

    # สร้าง Token สำหรับใช้ในด่านที่สอง
    new_token = generate_token()
    PENDING_TOKENS[new_token] = (u_key, u_hwid)

    # ส่งโค้ด Bridge กลับไป (ด่านแรก)
    bridge_code = f"""
    local k, h, t = "{u_key}", "{u_hwid}", "{new_token}"
    local url = "https://key-eta-one.vercel.app/?key="..k.."&hwid="..h.."&token="..t
    local s, r = pcall(function() return game:HttpGet(url) end)
    if s then loadstring(r)() end
    """
    return Response(bridge_code, mimetype='text/plain')
    
