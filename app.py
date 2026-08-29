import os
import json
import base64
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)
CORS(app)

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lace_catalog_db.json')
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')

GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "1PtDSCGspIEa1GO_n6NEpNujjN5tCGTTH")

def get_drive_credentials():
    # 1. Check if credentials exist in Environment Variables (Render / Cloud)
    env_creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if env_creds_json:
        try:
            creds_info = json.loads(env_creds_json)
            return service_account.Credentials.from_service_account_info(
                creds_info, scopes=['https://www.googleapis.com/auth/drive']
            )
        except Exception as e:
            print("Env Creds Parse Error:", e)

    # 2. Fallback to local file (Local PC)
    if os.path.exists(CREDENTIALS_FILE):
        try:
            return service_account.Credentials.from_service_account_file(
                CREDENTIALS_FILE, scopes=['https://www.googleapis.com/auth/drive']
            )
        except Exception as e:
            print("Local Creds File Error:", e)

    return None

def upload_base64_to_drive(base64_str, filename):
    if "data:image" not in str(base64_str):
        return base64_str

    try:
        creds = get_drive_credentials()
        if not creds:
            print("Drive Upload Error: No valid Google Credentials found!")
            return base64_str

        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
            
        img_bytes = base64.b64decode(base64_str)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': f"{filename}.jpg",
            'parents': [GDRIVE_FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(img_bytes), mimetype='image/jpeg', resumable=True)
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        file_id = uploaded_file.get('id')
        
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()

        return f"https://lh3.googleusercontent.com/d/{file_id}"
    except Exception as e:
        print("Drive Upload Error:", e)
        return base64_str

def load_data():
    if not os.path.exists(DB_FILE):
        save_data([])
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/api/designs', methods=['GET'])
def get_designs():
    return jsonify(load_data()), 200

@app.route('/api/designs', methods=['POST'])
def add_or_update_design():
    new_item = request.get_json(force=True)
    if not new_item:
        return jsonify({"error": "No JSON payload provided"}), 400

    img_data = new_item.get('img', '')
    if "data:image" in str(img_data):
        drive_url = upload_base64_to_drive(img_data, f"Laxmi_{new_item.get('name', 'lace')}_{new_item.get('id', 'item')}")
        new_item['img'] = drive_url

    current_data = load_data()
    item_id = str(new_item.get('id'))
    new_name_clean = str(new_item.get('name', '')).strip().lower()

    existing_index = -1
    for idx, item in enumerate(current_data):
        if str(item.get('id')) == item_id:
            existing_index = idx
            break

    # Duplicate Design Name check
    for idx, item in enumerate(current_data):
        if str(item.get('name', '')).strip().lower() == new_name_clean:
            if existing_index == -1 or existing_index != idx:
                return jsonify({"error": "DUPLICATE_NAME", "message": f"Design '{new_item.get('name')}' pehle se uploaded hai! Duplicate allowed nahi hai."}), 400

    if existing_index > -1:
        current_data[existing_index] = new_item
    else:
        current_data.insert(0, new_item)
        
    save_data(current_data)
    return jsonify({"message": "Saved successfully", "design": new_item}), 201

@app.route('/api/designs/<design_id>', methods=['DELETE'])
def delete_design(design_id):
    current_data = load_data()
    updated_data = [item for item in current_data if str(item.get('id')) != str(design_id)]
    save_data(updated_data)
    return jsonify({"message": "Design deleted successfully"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
