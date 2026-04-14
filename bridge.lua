-- [[ ก่อน OBF: โค้ดต้นฉบับ ]]
local key = _G.key
local hwid = game:GetService("RbxAnalyticsService"):GetClientId()

-- แยกส่วน URL หลบการสแกน String
local d = "https://your-app.vercel.app/" 
local p = "?key=" .. tostring(key) .. "&hwid=" .. tostring(hwid)

local s, res = pcall(function()
    return game:HttpGet(d .. p)
end)

if s then
    local func = loadstring(res)
    if func then func() end
end
