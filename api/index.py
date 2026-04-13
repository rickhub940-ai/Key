import os, requests, base64, json, random, string 
from datetime import datetime, timedelta
from flask import Flask, request, Response
app = Flask(__name__)

def generate_random_token(length=20):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))
@app.route('/')
def handle_request():
    u_key = request.headers.get('X-Key')
    u_hwid = request.headers.get('X-Hwid')
    if not u_key:
        code, _ = get_github_file("bridge.lua")
        return Response(code if code else "print('Error')", mimetype='text/plain')
    data, sha = get_github_file("whitelist.json")
    if not data or u_key not in data.get("keys", {}):
        return Response("game.Players.LocalPlayer:Kick('Invalid Key')", mimetype='text/plain')
    info = data["keys"][u_key]
    if info["hwid"] is None:
        info["hwid"] = u_hwid
        update_github("whitelist.json", data, sha)
    elif info["hwid"] != u_hwid:
        return Response("game.Players.LocalPlayer:Kick('HWID Mismatch')", mimetype='text/plain')
    main, _ = get_github_file("main_script.lua")
    if main:
        dynamic_token = generate_random_token(24)
        protected_code = f"_G.Auth = '{dynamic_token}';\n" + main
        return Response(protected_code, mimetype='text/plain')
    return Response("print('Main Script Error')", mimetype='text/plain')
        
