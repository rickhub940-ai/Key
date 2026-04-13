import os
import requests
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, request, Response

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
WHITELIST_FILE = "whitelist.json"
MAIN_SCRIPT_FILE = "main_script.lua"

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
    payload = {"message": "Auto Update", "content": content_encoded, "sha": sha}
    requests.put(url, headers=headers, json=payload)

@app.route('/')
def handle_request():
    user_key = request.args.get('key')
    user_hwid = request.args.get('hwid')

    # --- จังหวะที่ 1: ถ้ายังไม่มี key/hwid ส่งมา (คนเพิ่งกดรันครั้งแรก) ---
    if not user_key or not user_hwid:
        # ส่ง "Bridge Script" กลับไปดึงค่าแบบเงียบๆ
        bridge_code = """
        local k = _G.Key
        local h = game:GetService("RbxAnalyticsService"):GetClientId()
        local u = "https://your-project.vercel.app/?key="..k.."&hwid="..h
        local s, r = pcall(function() return game:HttpGet(u) end)
        if s then loadstring(r)() end
        """
        return Response(bridge_code, mimetype='text/plain')

    # --- จังหวะที่ 2: เมื่อ Bridge Script ส่งค่ากลับมาเช็คที่เดิม ---
    data, sha = get_github_file(WHITELIST_FILE)
    if not data: return Response("print('Database Error')", mimetype='text/plain')

    keys = data.get("keys", {})
    if user_key not in keys:
        return Response("game.Players.LocalPlayer:Kick('Invalid Key')", mimetype='text/plain')

    info = keys[user_key]
    now = datetime.now()

    # เช็คหมดอายุและลบ
    if info["expiration"] not in ["permanent", "1", "7"]:
        expire_date = datetime.strptime(info["expiration"], "%Y-%m-%d")
        if now > expire_date:
            del data["keys"][user_key]
            update_github(WHITELIST_FILE, data, sha)
            return Response("game.Players.LocalPlayer:Kick('Expired')", mimetype='text/plain')

    # ผูก HWID & คำนวณเวลา
    if info["hwid"] is None:
        info["hwid"] = user_hwid
        if info["expiration"] in ["1", "7"]:
            days = int(info["expiration"])
            info["expiration"] = (now + timedelta(days=days)).strftime("%Y-%m-%d")
        update_github(WHITELIST_FILE, data, sha)
    
    # ตรวจสอบ HWID และส่งสคริปต์หลัก
    if info["hwid"] == user_hwid:
        main_code, _ = get_github_file(MAIN_SCRIPT_FILE)
        return Response(main_code, mimetype='text/plain')
    
    return Response("game.Players.LocalPlayer:Kick('HWID Mismatch')", mimetype='text/plain')
        
