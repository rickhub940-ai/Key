import os
import requests
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, request, Response

app = Flask(__name__)

# ดึงค่าจาก Environment Variables ใน Vercel Settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "ชื่อUserGitHubของคุณ"
REPO_NAME = "ชื่อโปรเจกต์ของคุณ"
WHITELIST_FILE = "whitelist.json"
MAIN_SCRIPT_FILE = "main_script.lua"

def get_github_file(path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        return json.loads(base64.b64decode(data['content']).decode('utf-8')) if path.endswith('.json') else base64.b64decode(data['content']).decode('utf-8'), data['sha']
    return None, None

def update_github(path, content, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content_encoded = base64.b64encode(json.dumps(content, indent=4).encode('utf-8')).decode('utf-8')
    payload = {"message": "Auto Update", "content": content_encoded, "sha": sha}
    requests.put(url, headers=headers, json=payload)

@app.route('/')
def verify():
    # รับคีย์จาก _G.Key ที่ส่งผ่านมากับ URL (หรือ Headers)
    user_key = request.args.get('key')
    user_hwid = request.args.get('hwid')
    
    if not user_key or not user_hwid:
        return Response("print('Error: Missing Key/HWID')", mimetype='text/plain')

    data, sha = get_github_file(WHITELIST_FILE)
    if not data: return Response("print('Error: Database Connection')", mimetype='text/plain')

    keys = data.get("keys", {})
    if user_key not in keys:
        return Response("game.Players.LocalPlayer:Kick('Invalid Key!')", mimetype='text/plain')

    info = keys[user_key]
    now = datetime.now()

    # 1. เช็ควันหมดอายุ และ ลบคีย์ทิ้ง
    if info["expiration"] != "permanent" and info["expiration"] not in ["1", "7"]:
        expire_date = datetime.strptime(info["expiration"], "%Y-%m-%d")
        if now > expire_date:
            del data["keys"][user_key]
            update_github(WHITELIST_FILE, data, sha)
            return Response("game.Players.LocalPlayer:Kick('Key Expired and Deleted!')", mimetype='text/plain')

    # 2. ผูก HWID ครั้งแรก และ คำนวณเวลา (1 หรือ 7 วัน)
    if info["hwid"] is None:
        info["hwid"] = user_hwid
        if info["expiration"] in ["1", "7"]:
            days = int(info["expiration"])
            info["expiration"] = (now + timedelta(days=days)).strftime("%Y-%m-%d")
        update_github(WHITELIST_FILE, data, sha)
        # ดึงสคริปต์หลักมาให้รันต่อทันทีหลังจากผูกเสร็จ
        main_code, _ = get_github_file(MAIN_SCRIPT_FILE)
        return Response(main_code, mimetype='text/plain')

    # 3. ตรวจสอบ HWID ว่าตรงกันไหม
    if info["hwid"] == user_hwid:
        main_code, _ = get_github_file(MAIN_SCRIPT_FILE)
        return Response(main_code, mimetype='text/plain')
    else:
        return Response("game.Players.LocalPlayer:Kick('HWID Mismatch!')", mimetype='text/plain')
  
