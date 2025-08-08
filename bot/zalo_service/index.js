process.stdout.setEncoding('utf8');
process.stderr.setEncoding('utf8');
import { Zalo } from 'zca-js';
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


async function messageDispatcher(message) {
    try {
        const messageText = message.content || ''; // Lấy nội dung tin nhắn
        // Kiểm tra xem tin nhắn có phải là plain text không
        const isPlainText = typeof message.data.content === "string";

        // Bỏ qua tin nhắn của chính mình
        if (message.isSelf || !isPlainText) {
            return;
        }

        const messageContent = message.data.content;
        console.log(`Nhận tin nhắn: "${messageContent}" từ ${message.threadId}`);


        // Nếu có vẻ là token, hãy thử xử lý nó.
        const isToken = ZALO_CONFIG.LINKING_TOKEN_PATTERNS.some(p => p.test(messageText.trim()));
        if (isToken) {
            const isHandled = await zaloApi.handleLinkingToken(messageText, message.from);
            if (isHandled) return;
        }

        // Nếu không phải là một token đã được xử lý,
        // thì coi nó là một hoạt động bình thường và ghi điểm.
        await zaloApi.trackActivity(message);

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
        const api = await zalo.loginQR();

        console.log("✅ Successfully logged in via QR code!");


        // 2. CHỈ SAU KHI CÓ `api`, MỚI BẮT ĐẦU ĐĂNG KÝ LISTENER
        console.log("Registering event listeners...");

        api.listener.on("message", async (message) => {
            console.log(`\n--- Nhận được tin nhắn từ Zalo user---`);
            console.log(`From: ${message.from}`);
            console.log(`Thread: ${message.threadId}`);
            console.log(`Type: ${message.type === ThreadType.Group ? 'Group' : 'Direct'}`);
            console.log(`Content: ${typeof message.data.content === "string" ? message.data.content : '[Non-text content]'}`);
            console.log(JSON.stringify(message, null, 2));

            messageDispatcher(message);
            try {
                await handleActivityMessage(message);
            } catch (error) {
                console.error("❌ Error handling message:", error);
            }
        });

        api.on("disconnect", () => console.log("Mất kết nối!"));
        // Xử lý các event khác nếu cần
        api.listener.on("error", (error) => {
            console.error("❌ Listener Error:", error);
        });

        // 3. Bắt đầu lắng nghe
        await api.listen();
        console.log("✅ Zalo Bot is connected and listening.");

    } catch (error) {
        console.error("❌ Lỗi nghiêm trọng khi khởi tạo bot.", error);
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