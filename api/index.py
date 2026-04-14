import os, requests, base64, json, random, string
from flask import Flask, request, Response

app = Flask(__name__)

# ฟังก์ชันสุ่ม Token 24 หลัก
def generate_token():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(24))

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
def main_handler():
    # รับค่าจาก URL ตรงๆ ตามที่ต้องการ
    u_key = request.args.get('key')
    u_hwid = request.args.get('hwid')

    # รอบแรก: ถ้าไม่มีคีย์ส่งมา ให้ส่ง bridge.lua ไปก่อน
    if not u_key:
        bridge_code = get_github_content("bridge.lua")
        return Response(bridge_code or "print('Error: Bridge not found')", mimetype='text/plain')

    # รอบสอง: เช็ค Whitelist และ HWID
    whitelist = get_github_content("whitelist.json")
    if not whitelist or u_key not in whitelist.get("keys", {}):
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Key')", mimetype='text/plain')

    target_info = whitelist["keys"][u_key]
    if target_info.get("hwid") and target_info["hwid"] != u_hwid:
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: HWID Mismatch')", mimetype='text/plain')

    # ผ่านด่าน! ส่ง Main Script พร้อมฉีด Token สุ่ม
    main_script = get_github_content("main_script.lua")
    if main_script:
        token = generate_token()
        # ฉีด Token เข้าไปใน _G.Auth เพื่อให้สคริปต์หลักไปเช็คต่อ
        protected_code = f"_G.Auth = '{token}';\n{main_script}"
        return Response(protected_code, mimetype='text/plain')
    
    return Response("print('Error: Main Script missing')", mimetype='text/plain')
    
