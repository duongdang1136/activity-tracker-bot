import { Zalo, ThreadType } from "zca-js";

// Khởi tạo Zalo client
const zalo = new Zalo();

// Function để kiểm tra xem tin nhắn có phải là dãy 6 số không
function is6DigitOTP(message) {
    // Regex để kiểm tra dãy chính xác 6 chữ số
    const otpRegex = /^\d{6}$/;
    return otpRegex.test(message.trim());
}

// Function khởi tạo bot
async function initBot() {
    try {
        console.log("Đang đăng nhập bằng QR Code...");
        const api = await zalo.loginQR();
        
        console.log("Đăng nhập thành công! Bot đang lắng nghe tin nhắn...");
        
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
                        case ThreadType.Group: {
                            console.log("Gửi phản hồi đến nhóm...");
                            
                            try {
                                await api.sendMessage(
                                    "Cảm ơn bạn",
                                    message.threadId,
                                    ThreadType.Group
                                );
                                console.log("Đã gửi tin nhắn cảm ơn thành công!");
                            } catch (groupError) {
                                console.log("Lỗi gửi tin nhắn nhóm, thử với object:");
                                
                                await api.sendMessage(
                                    { msg: "Cảm ơn bạn" },
                                    message.threadId,
                                    ThreadType.Group
                                );
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
        
        // Lắng nghe các sự kiện khác (tùy chọn)
        api.listener.on("error", (error) => {
            console.error("Lỗi listener:", error);
        });
        
        api.listener.on("disconnect", () => {
            console.log("Mất kết nối! Đang thử kết nối lại...");
        });
        
        // Bắt đầu lắng nghe
        api.listener.start();
        
        console.log("=".repeat(50));
        console.log("🤖 BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG!");
        console.log("📱 Gửi dãy 6 số bất kỳ để test (VD: 123456)");
        console.log("🔔 Bot sẽ trả lời 'Cảm ơn bạn' khi nhận được OTP");
        console.log("=".repeat(50));
        
        return api;
        
    } catch (error) {
        console.error("Lỗi khởi tạo bot:", error);
        throw error;
    }
}

// Function để test các trường hợp khác nhau
function testOTPValidation() {
    console.log("=== TEST OTP VALIDATION ===");
    
    const testCases = [
        "123456",    // ✅ Hợp lệ
        "000000",    // ✅ Hợp lệ  
        "999999",    // ✅ Hợp lệ
        "12345",     // ❌ Chỉ 5 số
        "1234567",   // ❌ 7 số
        "12a456",    // ❌ Có chữ cái
        " 123456 ",  // ❌ Có khoảng trắng
        "abc123",    // ❌ Có chữ cái
        "",          // ❌ Rỗng
    ];
    
    testCases.forEach(testCase => {
        const mockMessage = { data: { content: testCase } };
        const isValid = is6DigitOTP(testCase);
        console.log(`"${testCase}" => ${isValid ? "✅ Hợp lệ" : "❌ Không hợp lệ"}`);
    });
    
    console.log("=".repeat(30));
}

// Chạy test validation trước
testOTPValidation();

// Khởi động bot
initBot().catch(error => {
    console.error("Không thể khởi động bot:", error);
    process.exit(1);
});

// Xử lý graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Đang tắt bot...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Đang tắt bot...');
    process.exit(0);
});