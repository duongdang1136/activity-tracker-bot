from flask import Blueprint, request, jsonify, render_template
from services.auth_service import telegram_auth_service
import logging

logger = logging.getLogger(__name__)

telegram_auth_bp = Blueprint('telegram_auth', __name__, url_prefix='/auth/telegram')

@telegram_auth_bp.route('/widget')
def telegram_widget():
    """Hiển thị trang có Telegram Login Widget"""
    return render_template('telegram_widget.html')

@telegram_auth_bp.route('/callback', methods=['POST'])
def telegram_callback():
    """Xử lý callback từ Telegram Login Widget"""
    try:
        # Lấy dữ liệu auth từ request
        auth_data = request.get_json()
        
        if not auth_data:
            return jsonify({'error': 'No auth data provided'}), 400
        
        hub_user_id = auth_data.pop('hub_user_id', None)
        if not hub_user_id:
            return jsonify({'error': 'Hub user ID required'}), 400
        
        # Liên kết tài khoản
        success, message = telegram_auth_service.link_telegram_account(
            hub_user_id=hub_user_id,
            telegram_auth_data=auth_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'telegram_user': {
                    'id': auth_data.get('id'),
                    'first_name': auth_data.get('first_name'),
                    'username': auth_data.get('username')
                }
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Telegram callback error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@telegram_auth_bp.route('/unlink', methods=['POST'])
def unlink_telegram():
    """Hủy liên kết tài khoản Telegram"""
    try:
        data = request.get_json()
        hub_user_id = data.get('hub_user_id')
        
        if not hub_user_id:
            return jsonify({'error': 'Hub user ID required'}), 400
        
        success, message = telegram_auth_service.unlink_telegram_account(hub_user_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Telegram unlink error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
