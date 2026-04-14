if not _G.Auth or type(_G.Auth) ~= "string" or #_G.Auth < 20 then
    game.Players.LocalPlayer:Kick("Rick Hub: Security Violation (No Token)")
    return
end
_G.Auth = nil -- ล้างทิ้งทันที

print("Rick Hub Started!")
