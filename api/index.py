import os
import requests
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, request, Response

app = Flask(__name__)

# ดึงค่าจาก Environment Variables ใน Vercel
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

# ชื่อไฟล์ต่างๆ บน GitHub
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
    payload = {
        "message": "System: Auto Update Whitelist",
        "content": content_encoded,
        "sha": sha
    }
    requests.put(url, headers=headers, json=payload)

@app.route('/')
def handle_request():
    user_key = request.args.get('key')
    user_hwid = request.args.get('hwid')

    # --- จังหวะที่ 1: ส่ง Bridge Script (ดึงจากไฟล์ bridge.lua บน GitHub) ---
    if not user_key or not user_hwid:
        bridge_code, _ = get_github_file(BRIDGE_SCRIPT_FILE)
        if bridge_code:
            # ส่งโค้ดที่ OBF แล้วจาก bridge.lua กลับไปให้ Roblox
            return Response(bridge_code, mimetype='text/plain')
        else:
            return Response("print('Error: bridge.lua not found on GitHub')", mimetype='text/plain')

    # --- จังหวะที่ 2: ตรวจสอบ Key และ HWID ---
    data, sha = get_github_file(WHITELIST_FILE)
    if not data:
        return Response("print('Error: Database Connection Failed')", mimetype='text/plain')

    keys = data.get("keys", {})
    if user_key not in keys:
        return Response("game.Players.LocalPlayer:Kick('Invalid Key - Rick Hub')", mimetype='text/plain')

    info = keys[user_key]
    now = datetime.now()

    # 1. เช็ควันหมดอายุ และ ลบคีย์ทิ้งทันทีถ้าหมดเวลา
    if info["expiration"] not in ["permanent", "1", "7"]:
        try:
            expire_date = datetime.strptime(info["expiration"], "%Y-%m-%d")
            if now > expire_date:
                del data["keys"][user_key]
                update_github(WHITELIST_FILE, data, sha)
                return Response("game.Players.LocalPlayer:Kick('Key Expired and Deleted!')", mimetype='text/plain')
        except:
            pass

    # 2. ผูก HWID และ คำนวณวันหมดอายุ (สำหรับคีย์ใหม่)
    if info["hwid"] is None:
        info["hwid"] = user_hwid
        if info["expiration"] in ["1", "7"]:
            days = int(info["expiration"])
            info["expiration"] = (now + timedelta(days=days)).strftime("%Y-%m-%d")
        
        # อัปเดตข้อมูลกลับไปที่ GitHub
        update_github(WHITELIST_FILE, data, sha)
        
        # ส่งสคริปต์หลักให้รันทันที
        main_code, _ = get_github_file(MAIN_SCRIPT_FILE)
        return Response(main_code, mimetype='text/plain')

    # 3. ตรวจสอบว่า HWID ตรงกับที่เคยผูกไว้หรือไม่
    if info["hwid"] == user_hwid:
        main_code, _ = get_github_file(MAIN_SCRIPT_FILE)
        return Response(main_code, mimetype='text/plain')
    else:
        return Response("game.Players.LocalPlayer:Kick('HWID Mismatch - Contact Admin')", mimetype='text/plain')

# สำหรับ Vercel Runtime
def handler(event, context):
    return app(event, context)
                    
