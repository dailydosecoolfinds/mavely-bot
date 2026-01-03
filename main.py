import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Servidor Mavely en linea.", 200

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(force=True)
    product_url = data.get('url')
    row_id = data.get('row_id')
    
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    raw_token = os.environ.get('MAVELY_COOKIES', '')
    session_token = raw_token.strip().replace('"', '').replace("'", "")

    api_url = "https://creators.mave.ly/api/trpc/links.create?batch=1"
    
    headers = {
        "Host": "creators.mave.ly",
        "Connection": "keep-alive",
        "Content-Length": str(len(str({"0": {"json": {"url": product_url}}}))),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-trpc-source": "react",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://creators.mave.ly",
        "Referer": "https://creators.mave.ly/tools/link-creator",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Cookie": f"__Secure-next-auth.session-token={session_token}"
    }
    
    payload = {"0": {"json": {"url": product_url}}}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        
        # Log para debug en Render
        print(f"Status Mavely: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            res_json = response.json()
            mavely_link = res_json[0]['result']['data']['json']['link']
            requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            return jsonify({"status": "ok", "link": mavely_link})
        else:
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": f"Mavely Error {response.status_code}", "row_id": row_id})
            return jsonify({"error": "Mavely Error", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
