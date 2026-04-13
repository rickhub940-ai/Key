import os
import requests
import base64
import json
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, Response

app = Flask(__name__)

# --- ฟังก์ชันช่วย (Helper Functions) ---

def generate_random_token(length=24):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def get_github_file(path):
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("REPO_OWNER")
    repo = os.getenv("REPO_NAME")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            decoded = base64.b64decode(data['content']).decode('utf-8')
            return (json.loads(decoded) if path.endswith('.json') else decoded), data['sha']
    except Exception:
        pass
    return None, None

def update_github(path, content, sha):
    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("REPO_OWNER")
    repo = os.getenv("REPO_NAME")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    content_encoded = base64.b64encode(json.dumps(content, indent=4).encode('utf-8')).decode('utf-8')
    payload = {"message": "System: Auto Update", "content": content_encoded, "sha": sha}
    requests.put(url, headers=headers, json=payload)

# --- Main Route ---

@app.route('/')
def handle_request():
    try:
        u_key = request.headers.get('X-Key')
        u_hwid = request.headers.get('X-Hwid')

        # รอบที่ 1: ถ้าไม่มี Header (คนรันเพิ่งกด loadstring)
        if not u_key:
            code, _ = get_github_file("bridge.lua")
            if code:
                return Response(code, mimetype='text/plain')
            return Response("print('Error: bridge.lua not found in GitHub')", mimetype='text/plain')

        # รอบที่ 2: ตรวจสอบความปลอดภัย
        data, sha = get_github_file("whitelist.json")
        if not data:
            return Response("print('Error: Could not read whitelist.json')", mimetype='text/plain')

        keys = data.get("keys", {})
        if u_key not in keys:
            return Response("game.Players.LocalPlayer:Kick('Rick Hub: Invalid Key')", mimetype='text/plain')

        info = keys[u_key]
        
        # ระบบจัดการ HWID
        if info.get("hwid") is None:
            info["hwid"] = u_hwid
            update_github("whitelist.json", data, sha)
        elif info.get("hwid") != u_hwid:
            return Response("game.Players.LocalPlayer:Kick('Rick Hub: HWID Mismatch')", mimetype='text/plain')

        # ผ่าน! ส่งสคริปต์หลักพร้อม Token สุ่ม
        main, _ = get_github_file("main_script.lua")
        if main:
            dynamic_token = generate_random_token(24)
            # ฉีด Token เข้าไปที่บรรทัดบนสุด
            protected_code = f"_G.Auth = '{dynamic_token}';\n{main}"
            return Response(protected_code, mimetype='text/plain')
        
        return Response("print('Error: main_script.lua not found')", mimetype='text/plain')

    except Exception as e:
        # ถ้าพัง ให้ส่ง Error กลับไปบอกในเกมเลยว่าพังตรงไหน
        return Response(f"print('Server Error: {str(e)}')", mimetype='text/plain')

def handler(event, context):
    return app(event, context)
    
