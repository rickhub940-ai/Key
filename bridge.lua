local k = _G.key
local h = game:GetService("RbxAnalyticsService"):GetClientId()

-- ส่งแบบเดิมที่คุณชอบ (แนบไปกับลิงก์เลย)
local success, result = pcall(function()
    return game:HttpGet("https://key-eta-one.vercel.app/?key="..tostring(k).."&hwid="..tostring(h))
end)

if success then
    local run = loadstring(result)
    if run then run() end
else
    warn("Rick Hub: Connection Error")
end
