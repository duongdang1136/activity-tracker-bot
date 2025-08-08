// Giả định file này nằm ở `bot/zalo_service/api/zalo_api.js`
import { Zalo, ThreadType } from 'zca-js';
//import axios from 'axios';

// Cấu hình sẽ được truyền vào constructor thay vì import
//import { ZALO_CONFIG } from '../config/zalo_config.js';

class ZaloAPI {
    // Sửa lại constructor để nhận cấu hình từ bên ngoài
    constructor(config, supabaseClient) {
        this.zalo = new Zalo();
        this.api = null;
        this.isConnected = false;
        this.config = config; // Lưu lại config
        this.supabase = supabaseClient; // Lưu lại supabase client
    }

    // Kết nối với Zalo
    async connect() {
        if (this.isConnected) {
            console.log("Zalo is already connected.");
            return this.api;
        }
        try {
            console.log("🔄 Đang kết nối Zalo bằng QR Code...");
            this.api = await this.zalo.loginQR();
            this.isConnected = true;
            console.log("✅ Kết nối Zalo thành công!");
            return this.api;
        } catch (error) {
            console.error("❌ Lỗi kết nối Zalo:", error);
            throw error;
        }
    }

    // Gửi tin nhắn
    async sendMessage(message, threadId, isGroup = false) {
        if (!this.isConnected) throw new Error("Zalo chưa được kết nối");
        try {
            // Xác định thread_type dựa trên tham số isGroup
            const threadType = isGroup ? ThreadType.GROUP : ThreadType.USER;

            // Gọi phương thức sendMessage với thread_type đúng
            await this.api.sendMessage(message, threadId, threadType);

            //try {
            //    await this.api.sendMessage(message, threadId, threadType);
            //} catch (error) {
                // Thử với object format
            //    await this.api.sendMessage({ msg: message }, threadId, threadType);
            //}
            console.log(`📤 Đã gửi tin nhắn tới ${isGroup ? 'nhóm' : 'người dùng'} ${threadId}`);
            return true;
        } catch (error) {
            console.error(`❌ Lỗi gửi tin nhắn tới ${threadId}:`, error);
        }
    }

    // --- CÁC HÀM GIAO TIẾP VỚI SUPABASE ---

    // Hàm chung để gọi RPC của Supabase
    async callRpc(functionName, params) {
        try {
            const { error } = await this.config.supabaseClient.rpc(functionName, params);
            if (error) {
                console.error(`❌ Lỗi khi gọi RPC '${functionName}':`, error.message);
                return null;
            }
            return true; // Trả về true nếu gọi thành công
        } catch (error) {
            console.error(`❌ Lỗi nghiêm trọng khi gọi RPC '${functionName}':`, error.message);
            return null;
        }
    }

    // Ghi nhận hoạt động qua Supabase RPC
    async trackActivity(message) {
        const isGroup = message.thread.type === ThreadType.Group;
        if (!isGroup) return; // Chỉ theo dõi hoạt động trong nhóm

        const metadata = {
            display_name: message.sender.name,
            group_name: message.thread.name,
        };

        console.log(`[Activity] Tracking 'message' from ${metadata.display_name} in group ${metadata.group_name}`);

        return await this.callRpc('update_activity_with_group', {
            p_user_platform_id: message.sender.id.toString(),
            p_platform_name: 'zalo',
            p_group_platform_id: message.thread.id.toString(),
            p_activity_type: 'message', // Có thể mở rộng cho các loại khác
            p_metadata: metadata,
        });
    }

    // Hàm mới: Xử lý mã liên kết
    async handleLinkingToken(token, authorId) {
        console.log(`[Linking] Bắt đầu xác thực token '${token}' cho người dùng ${authorId}`);
        const platform_id_zalo = this.config.PLATFORM_ID; // Giả sử ID của Zalo là 1

        // 1. Tìm token
        const { data: tokenData, error: findError } = await this.config.supabaseClient
            .from('platform_linking_tokens')
            .select('*')
            .eq('token', token.toUpperCase())
            .eq('platform_id', platform_id_zalo)
            .eq('is_used', false)
            .single(); // Lấy một bản ghi duy nhất

        // [Token không hợp lệ]
        if (findError || !tokenData) {
            console.log(`[Linking] Token '${token}' không hợp lệ hoặc đã được sử dụng.`);
            // Theo biểu đồ, có thể không cần gửi tin nhắn lỗi để tránh spam.
            // Nếu muốn gửi, thêm dòng: await this.sendMessage("Mã liên kết không hợp lệ.", authorId);
            return false; // Không phải mã, để cho hàm khác xử lý
        }
        // Bước 8: Đã có dữ liệu token
         console.log("[Linking] Tìm thấy token hợp lệ.");

        // 2. Kiểm tra hết hạn
        const expires_at = new Date(tokenData.expires_at);
        if (new Date() > expires_at) {
            await this.sendMessage("Mã liên kết của bạn đã hết hạn. Vui lòng tạo mã mới trên website.", authorId);
            // Đánh dấu mã này đã sử dụng để không kiểm tra lại
            await this.config.supabaseClient.from('platform_linking_tokens').update({ is_used: true }).eq('id', tokenData.id);
            return true; // Đã xử lý (dù là lỗi hết hạn)
        }

        // [Token hợp lệ] -> Tiếp tục luồng
        try {
            const super_user_id = tokenData.user_id;
            const zalo_platform_user_id = authorId.toString();

            // Lấy tên Zalo của người dùng
            const userInfo = await this.api.getUserInfo(zalo_platform_user_id);
            const zalo_username = userInfo ? userInfo.name : "Zalo User";

            // Bước 9: INSERT INTO user_platform_profiles
            const { error: insertError } = await this.supabase
                .from('user_platform_profiles')
                .insert({
                    user_id: super_user_id,
                    platform_id: platform_id_zalo,
                    platform_user_id: zalo_platform_user_id,
                    platform_username: zalo_username,
                });

            // Bước 10: Xử lý lỗi (nếu có)
            if (insertError) {
                // Lỗi này thường là do tài khoản Zalo đã được liên kết (unique constraint violation)
                console.error("❌ Lỗi khi tạo liên kết:", insertError.message);
                await this.sendMessage("Không thể liên kết. Tài khoản Zalo này có thể đã được sử dụng bởi một người dùng khác.", authorId);
                return true;
            }
            console.log(`[Linking] Đã tạo liên kết cho user ${super_user_id}`);

            // Bước 11: UPDATE platform_linking_tokens SET is_used = true
            await this.supabase.from('platform_linking_tokens').update({ is_used: true }).eq('id', tokenData.id);

            // Bước 12: Xác nhận cập nhật (đã xong)
            console.log(`[Linking] Đã cập nhật token ${token} thành đã sử dụng.`);

            // Bước 13: Gửi tin nhắn "Liên kết thành công!"
            await this.sendMessage("Chúc mừng! Tài khoản Zalo của bạn đã được liên kết thành công.", authorId);
            return true; // Báo hiệu đã xử lý thành công

        } catch (e) {
            console.error("❌ Lỗi nghiêm trọng trong quá trình liên kết:", e);
            await this.sendMessage("Đã có lỗi hệ thống xảy ra. Vui lòng thử lại sau.", authorId);
            return true; // Vẫn trả về true vì đã cố gắng xử lý
        }

    }


    // --- CÁC HÀM TIỆN ÍCH (giữ lại từ file của bạn) ---
    isCommand(message) {
        // ... (code không đổi)
    }
    parseCommand(message) {
        // ... (code không đổi)
    }
}

export default ZaloAPI; // Sử dụng ES Module export
