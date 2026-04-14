-- [[ ส่วนเช็ค Token - สำคัญมาก ]]
if not _G.Auth or type(_G.Auth) ~= "string" or #_G.Auth < 20 then
    -- ถ้าไม่มี Token ที่ถูกต้องมาจากการรันผ่าน Server ให้หยุดทำงาน
    return 
end

-- ล้างค่า Token ทันทีเพื่อความปลอดภัย
_G.Auth = nil 

-- [[ เริ่มโค้ดฟาร์มหรือฟังก์ชันหลักของคุณด้านล่างนี้ ]]
print("Rick Hub: Authenticated Successfully!")

-- ตัวอย่าง:
-- while task.wait(1) do ... end
