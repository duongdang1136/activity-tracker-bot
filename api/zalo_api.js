import { Zalo, ThreadType, MessageType } from 'zca-js';
import axios from 'axios';
import { ZALO_CONFIG } from '../config/zalo_config.js';

class ZaloAPI {
    constructor() {
        this.zalo = new Zalo();
        this.api = null;
        this.isConnected = false;
    }

    // Kết nối với Zalo
    async connect() {
        try {
            console.log("🔄 Đang kết nối Zalo...");
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
    async sendMessage(message, threadId, threadType = ThreadType.User) {
        if (!this.isConnected || !this.api) {
            throw new Error("Zalo chưa được kết nối");
        }

        try {
            // Thử nhiều format để tránh lỗi
            try {
                await this.api.sendMessage(message, threadId, threadType);
            } catch (error) {
                // Thử với object format
                await this.api.sendMessage({ msg: message }, threadId, threadType);
            }
            
            console.log(`📤 Đã gửi tin nhắn: "${message}" tới ${threadId}`);
            return true;
        } catch (error) {
            console.error("❌ Lỗi gửi tin nhắn:", error);
            return false;
        }
    }

    // Sync dữ liệu với Python backend
    async syncWithPython(endpoint, data) {
        try {
            const response = await axios.post(
                `${ZALO_CONFIG.PYTHON_API_BASE}${endpoint}`,
                data,
                {
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    timeout: 5000
                }
            );
            return response.data;
        } catch (error) {
            console.error(`❌ Lỗi sync với Python API [${endpoint}]:`, error.message);
            return null;
        }
    }

    // Log hoạt động user
    async logUserActivity(userId, activity, metadata = {}) {
        const data = {
            platform: 'zalo',
            user_id: userId,
            activity_type: activity,
            metadata: metadata,
            timestamp: new Date().toISOString()
        };

        return await this.syncWithPython(ZALO_CONFIG.API_ENDPOINTS.LOG_ACTIVITY, data);
    }

    // Log tin nhắn
    async logMessage(messageData) {
        const data = {
            platform: 'zalo',
            thread_id: messageData.threadId,
            user_id: messageData.senderId || 'unknown',
            message: messageData.content,
            message_type: messageData.type,
            timestamp: new Date().toISOString(),
            metadata: {
                thread_type: messageData.threadType,
                is_self: messageData.isSelf
            }
        };

        return await this.syncWithPython(ZALO_CONFIG.API_ENDPOINTS.LOG_MESSAGE, data);
    }

    // Kiểm tra OTP
    isOTP(message) {
        return ZALO_CONFIG.OTP_PATTERNS.some(pattern => pattern.test(message.trim()));
    }

    // Kiểm tra command
    isCommand(message) {
        return message.startsWith(ZALO_CONFIG.COMMAND_PREFIX);
    }

    // Parse command
    parseCommand(message) {
        const parts = message.slice(1).split(' ');
        return {
            command: parts[0].toLowerCase(),
            args: parts.slice(1)
        };
    }
}

export default ZaloAPI;