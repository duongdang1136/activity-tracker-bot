// Import thư viện
const { Zalo, ThreadType } = require('zca-js');
const { createClient } = require('@supabase/supabase-js');
const path = require('path');

require('dotenv').config({ path: path.join(__dirname, '../../.env') });

// ==============================================================================
// CẤU HÌNH
// ==============================================================================

// Supabase
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;
const ZALO_SESSION_DATA = process.env.ZALO_SESSION_DATA;


if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error("❌ Missing required environment variables. Check your .env file.");
    process.exit(1);
}


// Khởi tạo Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
const PLATFORM_NAME = 'zalo';


// ==============================================================================
// CÁC HÀM XỬ LÝ
// ==============================================================================

async function handleActivityMessage(message) {
    // Chỉ xử lý tin nhắn trong nhóm
    if (message.type !== ThreadType.Group) return;
    // Kiểm tra nếu tin nhắn là plain text
    const isPlainText = typeof message.data.content === "string";
    if (!isPlainText) return;

    const metadata = {
        display_name: message.data.displayName || 'Unknown User',
        group_name: message.data.threadName || 'Unknown Group',
        content: message.data.content
    };

    console.log(`[Activity] Tracking 'message' from ${metadata.display_name} in group ${metadata.group_name}`);
    
    // Gọi RPC function trên Supabase
    const { error } = await supabase.rpc('update_activity_with_group', {
        p_user_platform_id: message.from,
        p_platform_name: PLATFORM_NAME,
        p_group_platform_id: message.threadId,
        p_activity_type: 'message',
        p_metadata: metadata,
    });

    if (error) {
        console.error("❌ Error calling RPC for activity:", error.message);
    } else {
        console.log("✅ Activity recorded via RPC.");
    }
}


// ==============================================================================
// HÀM CHÍNH
// ==============================================================================
async function main() {
    console.log("🤖 Zalo Bot Service (zca-js with QR Flow) is starting...");
    const zalo = new Zalo();
    let api; // Biến để lưu đối tượng API sau khi đăng nhập
    // ---- Bước 1: Cố gắng đăng nhập bằng Session đã lưu ----
    if (ZALO_SESSION_DATA) {
        console.log("🔑 Found session data in .env. Attempting to login using session...");
        try {
            const sessionData = JSON.parse(ZALO_SESSION_DATA);
            // Giả định thư viện có phương thức login bằng session
            api = await zalo.loginWithSession(sessionData); 
            console.log("✅ Successfully logged in using saved session!");
        } catch (error) {
            console.warn("⚠️ Failed to login with session, it might be expired. Falling back to QR code.", error.message);
            api = null; // Đặt lại api để đảm bảo chạy luồng QR
        }
    }

    // ---- Bước 2: Nếu không có session hoặc session lỗi, dùng QR Code ----
    if (!api) {
        try {
            console.log("📱 Starting QR code login process...");
            console.log("Please scan the QR code that will appear in your terminal or browser");
            
            // Đăng nhập bằng QR code
            api = await zalo.loginQR();
            
            console.log("✅ Successfully logged in via QR code!");
            
            // ---- Bước 3: Lấy và in ra session mới ----
            // Giả định thư viện có phương thức để lấy session
            const newSessionData = await api.getSession(); 
            
            console.log("\n\n========================= IMPORTANT =========================");
            console.log("COPY AND PASTE THE FOLLOWING LINE INTO YOUR .env FILE");
            console.log("TO AVOID SCANNING QR CODE NEXT TIME:");
            console.log("---------------------------------------------------------");
            console.log(`ZALO_SESSION_DATA='${JSON.stringify(newSessionData)}'`); // In ra định dạng dễ copy
            console.log("=========================================================\n\n");
        } catch (error) {
            console.error("❌ Fatal error during QR login process:", error);
            process.exit(1);
        }
    }
        // ---- Đăng ký Listener ----
        console.log("Registering event listeners...");

        api.listener.on("message", async (message) => {
            console.log(`\n--- Received Zalo message ---`);
            console.log(`From: ${message.from}`);
            console.log(`Thread: ${message.threadId}`);
            console.log(`Type: ${message.type === ThreadType.Group ? 'Group' : 'Direct'}`);
            console.log(`Content: ${typeof message.data.content === "string" ? message.data.content : '[Non-text content]'}`);
            console.log(JSON.stringify(message, null, 2)); 
            try {
                await handleActivityMessage(message);
            } catch (error) {
                console.error("❌ Error handling message:", error);
            }
        });

        // Xử lý các event khác nếu cần
        api.listener.on("error", (error) => {
            console.error("❌ Listener Error:", error);
        });

        // Bắt đầu lắng nghe
        api.listener.start();
        console.log("✅ Zalo Bot is connected and listening for messages...");
        console.log("⚠️  Note: Only one web listener can run per account at a time.");
        console.log("   If you open Zalo in browser, the listener will stop automatically.");

        // Xử lý tín hiệu thoát
        process.on('SIGINT', () => {
            console.log('\n🛑 Shutting down Zalo bot...');
            api.listener.stop();
            process.exit(0);
        });

        process.on('SIGTERM', () => {
            console.log('\n🛑 Shutting down Zalo bot...');
            api.listener.stop();
            process.exit(0);
        });

// Xử lý uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});
}

