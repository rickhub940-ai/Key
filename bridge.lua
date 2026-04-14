local k = _G.key
local h = game:GetService("RbxAnalyticsService"):GetClientId()

-- URL ของ Vercel (แยกส่วนไว้ให้ OBF ทำงานได้เนียนขึ้น)
local domain = "https://key-eta-one.vercel.app/"
local query = "?key=" .. tostring(k) .. "&hwid=" .. tostring(h)

local success, result = pcall(function()
    return game:HttpGet(domain .. query)
end)

if success then
    local run = loadstring(result)
    if run then run() end
end
