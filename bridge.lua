local k = _G.key -- ดึงจาก Loader
local h = game:GetService("RbxAnalyticsService"):GetClientId()

-- ถ้า _G.key ดึงไม่ได้ ให้ลองใช้ค่าสำรองเพื่อเช็ค
if not k or k == "" then
    k = "NO_KEY_DETECTED" 
end

local url = "https://key-eta-one.vercel.app/?key="..tostring(k).."&hwid="..tostring(h)

local s, r = pcall(function()
    return game:HttpGet(url)
end)

if s then
    local f = loadstring(r)
    if f then f() end
end
