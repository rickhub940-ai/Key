local k = _G.key
local h = game:GetService("RbxAnalyticsService"):GetClientId()
local d = "https://key-eta-one.vercel.app/"
local q = "?key=" .. tostring(k) .. "&hwid=" .. tostring(h)

local s, r = pcall(function()
    return game:HttpGet(d .. q)
end)

if s then
    local f = loadstring(r)
    if f then f() end
end
