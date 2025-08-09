import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// Đoạn code này để đọc file .env từ thư mục gốc của toàn bộ dự án
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Đọc file .env từ thư mục gốc của toàn bộ dự án
dotenv.config({ path: path.join(__dirname, '../.env') });

export const ZALO_CONFIG = {
    // Supabase credentials
    SUPABASE_URL: process.env.SUPABASE_URL,
    SUPABASE_KEY: process.env.SUPABASE_KEY,

    // Platform ID cho Zalo trong database
    PLATFORM_ID: parseInt(process.env.ZALO_PLATFORM_ID) || 1,

    // Bot behavior config
    COMMAND_PREFIX: process.env.ZALO_COMMAND_PREFIX || '/',
    AUTO_REPLY: process.env.ZALO_AUTO_REPLY === 'true',

    // OTP Detection
    LINKING_TOKEN_PATTERNS: [
        /^\d{6}$/,        // 6 digits (123456)
        /^\d{4}$/,        // 4 digits (1234)
        /^[A-Z0-9]{6}$/,  // 6 alphanumeric uppercase (ABC123)
        /^[A-Z0-9]{4}$/   // 4 alphanumeric uppercase (AB12)
    ],

    // Message handling config
    IGNORE_SELF_MESSAGES: true,
    TRACK_GROUP_ACTIVITY: true,
    TRACK_DIRECT_ACTIVITY: false,

    // Cấu hình logging
    LOG_LEVEL: process.env.ZALO_LOG_LEVEL || 'info',
    LOG_FILE: process.env.ZALO_LOG_FILE || './logs/zalo.log',

    // Validation function
    validate() {
        const required = ['SUPABASE_URL', 'SUPABASE_KEY'];
        const missing = required.filter(key => !this[key]);

        if (missing.length > 0) {
            throw new Error(`Missing required config: ${missing.join(', ')}`);
        }

        console.log("✅ Configuration validated successfully");
        console.log(`📊 Platform ID: ${this.PLATFORM_ID}`);
        console.log(`🔧 Command Prefix: ${this.COMMAND_PREFIX}`);
        console.log(`📝 Debug Mode: ${this.DEBUG_MODE ? 'ON' : 'OFF'}`);
        return true;
    }
}

// Validate configuration on import
try {
    ZALO_CONFIG.validate();
} catch (error) {
    console.error("❌ Configuration validation failed:", error.message);
    process.exit(1);
}


    // API endpoints để sync với Python backend
//    PYTHON_API_BASE: process.env.PYTHON_API_BASE || 'http://localhost:5000',
//    API_ENDPOINTS: {
//        LOG_ACTIVITY: '/api/activity/log',
//        UPDATE_USER: '/api/users/update',
//        GET_USER_INFO: '/api/users/info',
//        LOG_MESSAGE: '/api/messages/log'
//    },


