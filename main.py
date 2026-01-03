import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    product_url = data.get('url')
    row_id = data.get('row_id')
    
    # URL de tu Webhook de Make
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    
    # Limpieza del Token de los Secretos de Render
    raw_token = os.environ.get('MAVELY_COOKIES', '')
    session_token = raw_token.strip().replace('"', '').replace("'", "")

    if not product_url or not session_token:
        return jsonify({"error": "Faltan datos"}), 400

    # API de Mavely
    api_url = "https://creators.mave.ly/api/trpc/links.create?batch=1"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"__Secure-next-auth.session-token={session_token}",
        "x-trpc-source": "react",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://creators.mave.ly/tools/link-creator"
    }
    payload = {"0": {"json": {"url": product_url}}}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            mavely_link = res_json[0]['result']['data']['json']['link']
            # Avisar a Make del éxito
            requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            return jsonify({"status": "ok", "link": mavely_link})
        else:
            # Reintentar con otro User-Agent o reportar error
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": f"Error {response.status_code}", "row_id": row_id})
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
