# check_config.py
try:
    print("--- Bắt đầu kiểm tra cấu hình ---")
    from config import settings

    print("\n✅ Import 'settings' thành công!")

    print("\nĐang kiểm tra Supabase Config...")
    print(f"  URL: {settings.supabase.url}")
    print(f"  Key: ...{settings.supabase.key[-5:]}") # In 5 ký tự cuối của key
    print("✅ Supabase Config đã được đọc thành công!")



    print("\nĐang kiểm tra Zalo Config...")
    print(f"  phone: {settings.zalo.phone[-5:]}")
    print(f"  password: ...{settings.zalo.password[-5:]}")
    print(f"  imei: ...{settings.zalo.imei[-5:]}")
    #print(f"  cookies: ...{settings.zalo.cookies[-5:]}")# In 5 ký tự cuối của key
    print("✅ Zalo Config đã được đọc thành công!")




    print("\nĐang kiểm tra Discord Config...")
    print(f"  token: {settings.discord.token[-5:]}")
    print("✅ Discord Config đã được đọc thành công!")



    print("\nĐang kiểm tra Telegram Config...")
    print(f"  token: {settings.telegram.token[-5:]}")
    print("✅ Telegram Config đã được đọc thành công!")

except Exception as e:
    print("\n❌ Đã xảy ra lỗi trong quá trình kiểm tra:")
    print(e)