import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// Đoạn code này để đọc file .env từ thư mục gốc của toàn bộ dự án
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Đọc file .env từ thư mục gốc của toàn bộ dự án
dotenv.config({ path: path.join(__dirname, '../.env') });

export const ZALO_CONFIG = {
    // Cấu hình logging
    LOG_LEVEL: process.env.ZALO_LOG_LEVEL || 'info',
    LOG_FILE: process.env.ZALO_LOG_FILE || './logs/zalo.log',

    // Supabase credentials
    SUPABASE_URL: process.env.SUPABASE_URL,
    SUPABASE_KEY: process.env.SUPABASE_KEY,
    PLATFORM_ID: 1,

    // Cấu hình retry
    MAX_RETRY: parseInt(process.env.ZALO_MAX_RETRY) || 3,
    RETRY_DELAY: parseInt(process.env.ZALO_RETRY_DELAY) || 1000,


    // Bot behavior config
    COMMAND_PREFIX: process.env.ZALO_COMMAND_PREFIX || '/',


    // API endpoints để sync với Python backend
//    PYTHON_API_BASE: process.env.PYTHON_API_BASE || 'http://localhost:5000',
//    API_ENDPOINTS: {
//        LOG_ACTIVITY: '/api/activity/log',
//        UPDATE_USER: '/api/users/update',
//        GET_USER_INFO: '/api/users/info',
//        LOG_MESSAGE: '/api/messages/log'
//    },

    // Zalo specific config
    AUTO_REPLY: process.env.ZALO_AUTO_REPLY === 'true',
    COMMAND_PREFIX: process.env.ZALO_COMMAND_PREFIX || '!',

    // OTP Detection
    LINKING_TOKEN_PATTERNS: [
        /^\d{6}$/,        // 6 digits
        /^\d{4}$/,        // 4 digits
        /^[A-Z0-9]{6}$/   // 6 alphanumeric
    ]
};