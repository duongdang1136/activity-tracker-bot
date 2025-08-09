process.stdout.setEncoding('utf8');
process.stderr.setEncoding('utf8');

import { Zalo,ThreadType } from 'zca-js';
import { createClient } from '@supabase/supabase-js';
import { ZALO_CONFIG } from './config/zalo_config.js';
import ZaloAPI from './api/zalo_api.js';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Đoạn code này để đọc file .env từ thư mục gốc của toàn bộ dự án
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Đọc file .env từ thư mục gốc của toàn bộ dự án
dotenv.config({ path: path.join(__dirname, '../.env') });

// ==============================================================================
// CẤU HÌNH
// ==============================================================================

// --- KHỞI TẠO CÁC DỊCH VỤ ---
const supabase = createClient(ZALO_CONFIG.SUPABASE_URL, ZALO_CONFIG.SUPABASE_KEY);
const zaloApi = new ZaloAPI(ZALO_CONFIG, supabase);
const PLATFORM_NAME = 'zalo';

// Global variables để quản lý API instance
let globalApi = null;

// ==============================================================================
// CÁC HÀM XỬ LÝ
// ==============================================================================

async function handleActivityMessage(message) {
    // Chỉ xử lý tin nhắn trong nhóm
    if (message.type !== ThreadType.Group) return;

    // Bỏ qua tin nhắn từ chính bot
    if (message.isSelf) return;

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


async function messageDispatcher(message) {
    try {
        // Lấy nội dung tin nhắn
        //const messageText = message.content || '';

        // Kiểm tra xem tin nhắn có phải là plain text không
        const isPlainText = typeof message.data.content === "string";

        // Bỏ qua tin nhắn của chính mình hoặc non-text content
        if (message.isSelf || !isPlainText) {
            return;
        }

        const messageContent = message.data.content;
        console.log(`Nhận tin nhắn: "${messageContent}" từ ${message.threadId}`);


        // Kiểm tra xem có phải token linking không
        const isToken = ZALO_CONFIG.LINKING_TOKEN_PATTERNS.some(p => p.test(messageContent.trim()));
        if (isToken) {
            console.log(`[Token Detection] Detected potential linking token: ${messageContent}`);
            const isHandled = await zaloApi.handleLinkingToken(messageContent, message.from);
            if (isHandled) return;
        }

        // Nếu không phải token, thì ghi nhận activity
        await handleActivityMessage(message);

    } catch (error) {
        console.error("Lỗi khi xử lý tin nhắn:", error);
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

        // 1. Đăng nhập và lấy đối tượng `api`
        globalApi = await zalo.loginQR();
        console.log("✅ Successfully logged in via QR code!");

        // 2. Cập nhật API instance trong ZaloAPI class
        zaloApi.setAPI(globalApi);
        //zaloApi.isConnected = true;

        // 3. Đăng ký event listeners
        console.log("Registering event listeners...");

        globalApi.listener.on("message", async (message) => {
            console.log(`\n--- Nhận được tin nhắn từ Zalo user---`);
            console.log(`From: ${message.from}`);
            console.log(`Thread: ${message.threadId}`);
            console.log(`Type: ${message.type === ThreadType.Group ? 'Group' : 'Direct'}`);
            console.log(`Is Self: ${message.isSelf}`);


            if (typeof message.data.content === "string") {
                console.log(`Content: ${message.data.content}`);
            } else {
                console.log(`Content: [Non-text content]`);
            }

            // Debug: In ra toàn bộ message object (có thể comment lại sau)
            // console.log("Full message object:", JSON.stringify(message, null, 2));

            await messageDispatcher(message);
        });


        // Xử lý lỗi listener
        globalApi.listener.on("error", (error) => {
            console.error("❌ Listener Error:", error);
        });

        // 4. Bắt đầu lắng nghe
        globalApi.listener.start();
        console.log("✅ Zalo Bot is connected and listening for messages...");
        console.log("⚠️  Note: Only one web listener can run per account at a time.");
        console.log("   If you open Zalo in browser, the listener will stop automatically.");

        // Setup graceful shutdown
        setupGracefulShutdown();

    } catch (error) {
        console.error("❌ Lỗi nghiêm trọng khi khởi tạo bot.", error);
        process.exit(1); // Thoát nếu có lỗi nghiêm trọng
    }
}

// ==============================================================================
// GRACEFUL SHUTDOWN
// ==============================================================================
function setupGracefulShutdown() {
    const shutdown = (signal) => {
        console.log(`\n🛑 Received ${signal}. Shutting down Zalo bot...`);

        if (globalApi && globalApi.listener) {
            try {
                globalApi.listener.stop();
                console.log("✅ Listener stopped successfully.");
            } catch (error) {
                console.error("❌ Error stopping listener:", error);
            }
        }

        console.log("👋 Bot shutdown complete. Goodbye!");
        process.exit(0);
    };
    // Xử lý tín hiệu thoát
    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

    // Xử lý uncaught exceptions
    process.on('uncaughtException', (error) => {
        console.error('❌ Uncaught Exception:', error);
        console.error('Stack trace:', error.stack);

        if (globalApi && globalApi.listener) {
            try {
                globalApi.listener.stop();
            } catch (e) {
                console.error("❌ Error stopping listener during crash:", e);
            }
        }

        process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
        console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);

        if (globalApi && globalApi.listener) {
            try {
                globalApi.listener.stop();
            } catch (e) {
                console.error("❌ Error stopping listener during crash:", e);
            }
        }

        process.exit(1);
    });
}


// ==============================================================================
// KHỞI CHẠY
// ==============================================================================
console.log("🚀 Starting Zalo Bot Application...");
main().catch(error => {
    console.error("❌ Failed to start main application:", error);
    process.exit(1);
});