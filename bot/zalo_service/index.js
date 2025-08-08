process.stdout.setEncoding('utf8');
process.stderr.setEncoding('utf8');
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
    console.log("🤖 Zalo Bot Service (QR Flow) is starting...");
    try {
        const zalo = new Zalo();

        console.log("📱 Starting QR code login process...");
        console.log("Please scan the QR code that will appear in your terminal or browser.");
        
        // Function để kiểm tra xem tin nhắn có phải là dãy 6 số không
        function is6DigitOTP(message) {
            // Regex để kiểm tra dãy chính xác 6 chữ số
            const otpRegex = /^\d{6}$/;
            return otpRegex.test(message.trim());
        }

        // 1. Đăng nhập và lấy đối tượng `api`
        const api = await zalo.loginQR();
                
        console.log("✅ Successfully logged in via QR code!");
        

        // 2. CHỈ SAU KHI CÓ `api`, MỚI BẮT ĐẦU ĐĂNG KÝ LISTENER
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
        // Lắng nghe sự kiện tin nhắn
        api.listener.on("message", async (message) => {
            try {
                // Kiểm tra xem tin nhắn có phải là plain text không
                const isPlainText = typeof message.data.content === "string";
                
                // Bỏ qua tin nhắn của chính mình
                if (message.isSelf || !isPlainText) {
                    return;
                }
                
                const messageContent = message.data.content;
                console.log(`Nhận tin nhắn: "${messageContent}" từ ${message.threadId}`);
                
                // Kiểm tra xem tin nhắn có phải là dãy 6 số không
                if (is6DigitOTP(messageContent)) {
                    console.log(`Phát hiện OTP 6 số: ${messageContent}`);
                    
                    // Xử lý theo loại thread (cá nhân hoặc nhóm)
                    switch (message.type) {
                        case ThreadType.User: {
                            console.log("Gửi phản hồi đến tin nhắn cá nhân...");
                            
                            // Thử gửi tin nhắn đơn giản trước
                            try {
                                await api.sendMessage(
                                    "Cảm ơn bạn",
                                    message.threadId,
                                    ThreadType.User
                                );
                                console.log("Đã gửi tin nhắn cảm ơn thành công!");
                            } catch (simpleError) {
                                console.log("Lỗi gửi tin nhắn đơn giản, thử với object:");
                                
                                // Thử với format object khác
                                try {
                                    await api.sendMessage(
                                        { msg: "Cảm ơn bạn" },
                                        message.threadId,
                                        ThreadType.User
                                    );
                                    console.log("Đã gửi tin nhắn với object thành công!");
                                } catch (objectError) {
                                    console.error("Lỗi gửi tin nhắn với object:", objectError);
                                    
                                    // Thử method khác nếu có
                                    console.log("Thử gửi tin nhắn không quote...");
                                    await api.sendMessage(
                                        { 
                                            msg: "Cảm ơn bạn",
                                            // Bỏ quote để tránh lỗi
                                        },
                                        message.threadId,
                                        ThreadType.User
                                    );
                                }
                            }
                            break;
                        }
                        default:
                            console.log("Loại thread không xác định");
                    }
                } else {
                    console.log(`Tin nhắn "${messageContent}" không phải là OTP 6 số`);
                }
                
            } catch (error) {
                console.error("Lỗi khi xử lý tin nhắn:", error);
            }
        });
        // Xử lý các event khác nếu cần
        api.listener.on("error", (error) => {
            console.error("❌ Listener Error:", error);
        });
        
        // 3. Bắt đầu lắng nghe
        api.listener.start();
        console.log("✅ Zalo Bot is connected and listening for messages...");
        console.log("⚠️  Note: Only one web listener can run per account at a time.");
        console.log("   If you open Zalo in browser, the listener will stop automatically.");

    } catch (error) {
        console.error("❌ Fatal error during Zalo bot initialization:", error);
        process.exit(1); // Thoát nếu có lỗi nghiêm trọng
    }
}

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
// Bắt đầu chạy chương trình
main();