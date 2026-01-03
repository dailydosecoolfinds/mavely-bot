import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Status: Online", 200

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(force=True)
    product_url = data.get('url')
    row_id = data.get('row_id')
    
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    # Limpieza extrema del token
    session_token = os.environ.get('MAVELY_COOKIES', '').strip().replace('"', '').replace("'", "")

    if not product_url or not session_token:
        return jsonify({"error": "Missing URL or Token"}), 400

    api_url = "https://creators.mave.ly/api/trpc/links.create?batch=1"
    
    # Payload exacto en formato string para calcular Content-Length si fuera necesario
    json_payload = {"0": {"json": {"url": product_url}}}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "x-trpc-source": "react",
        "Origin": "https://creators.mave.ly",
        "Referer": "https://creators.mave.ly/tools/link-creator",
        "Cookie": f"__Secure-next-auth.session-token={session_token}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    try:
        # Usamos un timeout más largo por si Mavely tarda en responder
        response = requests.post(api_url, headers=headers, json=json_payload, timeout=30)
        
        print(f"Log Fila {row_id} - Status: {response.status_code}")

        if response.status_code == 200:
            res_data = response.json()
            mavely_link = res_data[0]['result']['data']['json']['link']
            requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            return jsonify({"status": "success", "link": mavely_link})
        else:
            # Reportamos el status exacto a Make para saber si es 401 (token) o 403 (bloqueo)
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": f"Mavely Status {response.status_code}", "row_id": row_id})
            return jsonify({"error": "Mavely Error", "status_code": response.status_code}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500
