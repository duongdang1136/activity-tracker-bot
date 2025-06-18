from flask import Flask, jsonify
from flask_cors import CORS
from services.web_service import WebService

app = Flask(__name__)
CORS(app)

web_service = WebService()

@app.route('/api/leaderboard/<platform_name>/<group_name>', methods=['GET'])
def get_leaderboard(platform_name, group_name):
    data = web_service.get_leaderboard_for_group(group_name, platform_name)
    if data is None:
        return jsonify({"error": "Could not fetch leaderboard data."}), 500
    return jsonify(data)

def run_web_app():
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    run_web_app()
