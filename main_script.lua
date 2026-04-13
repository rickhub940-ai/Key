
if not _G.Auth or type(_G.Auth) ~= "string" or #_G.Auth < 20 then
    game.Players.LocalPlayer:Kick("\n[Rick Hub Security]\nAccess Denied: Please run through the official loader.")
    return
end
_G.Auth = nil 


print("Rick Hub: Authorized Successfully!")

while task.wait(1) do
    print("Auto Farming...")
end



print("ok")
