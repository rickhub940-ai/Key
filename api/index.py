import os
import requests
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, request, Response

app = Flask(__name__)

# ดึงค่าจาก Environment Variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
WHITELIST_FILE = "whitelist.json"
MAIN_SCRIPT_FILE = "main_script.lua"
BRIDGE_SCRIPT_FILE = "bridge.lua"

def get_github_file(path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        decoded = base64.b64decode(data['content']).decode('utf-8')
        return (json.loads(decoded) if path.endswith('.json') else decoded), data['sha']
    return None, None

def update_github(path, content, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content_encoded = base64.b64encode(json.dumps(content, indent=4).encode('utf-8')).decode('utf-8')
    payload = {"message": "System: Whitelist Update", "content": content_encoded, "sha": sha}
    requests.put(url, headers=headers, json=payload)

@app.route('/')
def handle_request():
    # รับค่าจาก Header เพื่อความปลอดภัย
    user_key = request.headers.get('X-Key')
    user_hwid = request.headers.get('X-HWID')

    # จังหวะที่ 1: ถ้าไม่มีข้อมูล Header ส่งมา (ครั้งแรกที่กด loadstring)
    if not user_key or not user_hwid:
        bridge_code, _ = get_github_file(BRIDGE_SCRIPT_FILE)
        return Response(bridge_code if bridge_code else "print('Error: Bridge Not Found')", mimetype='text/plain')

    # จังหวะที่ 2: ตรวจสอบ Whitelist
    data, sha = get_github_file(WHITELIST_FILE)
    if not data: return Response("print('Database Error')", mimetype='text/plain')

    keys = data.get("keys", {})
    if user_key not in keys:
        return Response("game.Players.LocalPlayer:Kick('Invalid Key - Rick Hub')", mimetype='text/plain')

    info = keys[user_key]
    now = datetime.now()

    # ตรวจสอบวันหมดอายุ
    if info["expiration"] not in ["permanent", "1", "7"]:
        try:
            expire_date = datetime.strptime(info["expiration"], "%Y-%m-%d")
            if now > expire_date:
                del data["keys"][user_key]
                update_github(WHITELIST_FILE, data, sha)
                return Response("game.Players.LocalPlayer:Kick('Key Expired!')", mimetype='text/plain')
        except: pass

    # ผูก HWID
    if info["hwid"] is None:
        info["hwid"] = user_hwid
        if info["expiration"] in ["1", "7"]:
            days = int(info["expiration"])
            info["expiration"] = (now + timedelta(days=days)).strftime("%Y-%m-%d")
        update_github(WHITELIST_FILE, data, sha)
    
    # เช็ค HWID และส่ง Main Script
    if info["hwid"] == user_hwid:
        main_code, _ = get_github_file(MAIN_SCRIPT_FILE)
        return Response(main_code, mimetype='text/plain')
    
    return Response("game.Players.LocalPlayer:Kick('HWID Mismatch')", mimetype='text/plain')

def handler(event, context):
    return app(event, context)
    
