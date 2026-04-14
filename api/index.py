import os, requests, base64, json, random, string
from flask import Flask, request, Response

app = Flask(__name__)

def generate_random_token(length=24):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def get_github_file(path):
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
def handle_request():
    # เปลี่ยนมาใช้ request.args เพื่อรับค่าจาก URL (?key=...&hwid=...)
    u_key = request.args.get('key')
    u_hwid = request.args.get('hwid')

    # จังหวะที่ 1: ถ้าไม่มี key ส่งมา ให้ส่ง bridge.lua ไปก่อน
    if not u_key:
        code, _ = get_github_file("bridge.lua")
        return Response(code if code else "print('Error: No Bridge')", mimetype='text/plain')

    # จังหวะที่ 2: ตรวจสอบ Whitelist
    data, sha = get_github_file("whitelist.json")
    if not data or u_key not in data.get("keys", {}):
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Key')", mimetype='text/plain')

    # ตรวจ HWID (แบบง่าย)
    info = data["keys"][u_key]
    if info.get("hwid") and info["hwid"] != u_hwid:
        return Response("game.Players.LocalPlayer:Kick('Rick Hub: HWID Mismatch')", mimetype='text/plain')

    # ผ่าน! ส่ง Main Script + สุ่ม Token
    main, _ = get_github_file("main_script.lua")
    if main:
        token = generate_random_token(24)
        return Response(f"_G.Auth = '{token}';\n" + main, mimetype='text/plain')
    
    return Response("print('Error: Main Script Not Found')", mimetype='text/plain')

def handler(event, context):
    return app(event, context)
    
