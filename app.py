from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import logging
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Airtable Config via environment variables
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'appqd5RgY61IFtaCW')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Water data')
AIRTABLE_PAT = os.getenv('AIRTABLE_PAT', 'your_fallback_token_here')
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return jsonify({'error': 'Failed to connect to Airtable', 'details': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
    return wrapper

@app.route('/')
def index():
    return jsonify({"message": "Water Quality Monitoring API"})

@app.route('/api/submit', methods=['POST'])
@handle_errors
def submit_data():
    data = request.json
    logger.info(f"Received data: {data}")

    timestamp = data.get('Timestamp')
    ph = data.get('pH')
    turbidity = data.get('Turbidity')
    flow = data.get('Flow')
    level = data.get('WaterLevel')

    airtable_record = {
        "fields": {
            "Timestamp": timestamp,
            "pH": float(ph),
            "Turbidity": float(turbidity),
            "Flow": float(flow),
            "Water Level": float(level)
        }
    }

    response = requests.post(AIRTABLE_URL, headers=HEADERS, json=airtable_record)
    response.raise_for_status()

    return jsonify({"success": True, "message": "Data sent to Airtable"})

@app.route('/data', methods=['GET'])
@handle_errors
def get_airtable_data():
    response = requests.get(AIRTABLE_URL, headers=HEADERS)
    response.raise_for_status()
    records = response.json().get('records', [])

    formatted = [record.get("fields", {}) for record in records]
    return jsonify(formatted)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
