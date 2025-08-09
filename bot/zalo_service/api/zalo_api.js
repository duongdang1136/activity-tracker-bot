
import { Zalo, ThreadType } from 'zca-js';

class ZaloAPI {
    constructor(config, supabaseClient) {
        this.api = null; // API instance sau khi login
        this.isConnected = false;
        this.config = config;
        this.supabase = supabaseClient;
    }
    async connect() {
        console.log("⚠️ Note: connect() is deprecated. API instance should be injected from main file.");
        return this.api;
    }

    startListening() {
        console.log("⚠️ Note: Message listening is handled in main file.");
        return true;
    }

    stopListening() {
        if (this.api && this.api.listener) {
            this.api.listener.stop();
            console.log("🛑 Đã dừng lắng nghe tin nhắn Zalo.");
        }
    }

    // Setter để inject API instance từ main file
    setAPI(apiInstance) {
        this.api = apiInstance;
        this.isConnected = true;
        console.log("✅ API instance injected into ZaloAPI class.");
    }


    // Gửi tin nhắn
    async sendMessage(message, threadId, isGroup = false) {
         if (!this.api) {
            throw new Error("API instance chưa được inject. Hãy gọi setAPI() trước.");
        }
        try {
            // Xác định thread_type dựa trên tham số isGroup
            const threadType = isGroup ? ThreadType.GROUP : ThreadType.USER;

            // Gọi phương thức sendMessage với thread_type đúng
            await this.api.sendMessage(
                { msg: message },
                threadId,
                threadType
            );

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
            const { error } = await this.supabase.rpc(functionName, params);
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
        const isGroup = message.type === ThreadType.Group;
        if (!isGroup) return; // Chỉ theo dõi hoạt động trong nhóm

        const metadata = {
            display_name: message.sender.name,
            group_name: message.thread.name,
            content: message.data.content
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
    // Kiểm tra xem tin nhắn có phải mã liên kết không
    isLinkingToken(content) {
        if (!content || typeof content !== 'string') return false;

        const trimmedContent = content.trim();
        return this.config.LINKING_TOKEN_PATTERNS.some(pattern =>
            pattern.test(trimmedContent)
        );
    }

    // Hàm mới: Xử lý mã liên kết
    async handleLinkingToken(token, authorId) {
        console.log(`[Linking] Bắt đầu xác thực token '${token}' cho người dùng ${authorId}`);
        const platform_id_zalo = this.config.PLATFORM_ID;

        try {
            // 1. Tìm token
            const { data: tokenData, error: findError } = await this.supabase
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
                await this.supabase
                    .from('platform_linking_tokens')
                    .update({ is_used: true })
                    .eq('id', tokenData.id);
                return true; // Đã xử lý (dù là lỗi hết hạn)
            }

            // [Token hợp lệ] -> Tiếp tục luồng
            try {
                const super_user_id = tokenData.user_id;
                const zalo_platform_user_id = authorId.toString();

                // Lấy tên Zalo của người dùng
                let zalo_username = "Zalo User";
                try {
                    // Note: zca-js có thể không có getUserInfo, tùy vào version
                    const userInfo = await this.api.getUserInfo(zalo_platform_user_id);
                    zalo_username = userInfo ? userInfo.name : "Zalo User";
                } catch (error) {
                    console.log("⚠️ Không thể lấy thông tin người dùng:", error.message);
                }

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
                await this.supabase
                    .from('platform_linking_tokens')
                    .update({ is_used: true })
                    .eq('id', tokenData.id);
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

        } catch (error) {
            console.error("❌ Lỗi nghiêm trọng trong quá trình liên kết:", error);
            await this.sendMessage("Đã có lỗi hệ thống xảy ra. Vui lòng thử lại sau.", authorId, false);
            return true;
        }
    }
    // --- CÁC HÀM TIỆN ÍCH ---
    isCommand(message) {
        if (!message || typeof message !== 'string') return false;
        return message.trim().startsWith(this.config.COMMAND_PREFIX);
    }

    parseCommand(message) {
        if (!this.isCommand(message)) return null;

        const parts = message.trim().substring(this.config.COMMAND_PREFIX.length).split(' ');
        return {
            command: parts[0].toLowerCase(),
            args: parts.slice(1)
        };
    }
}

export default ZaloAPI;