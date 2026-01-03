import os
import requests
import sys
import json

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    # IMPORTANTE: El valor de MAVELY_COOKIES debe ser solo el token 'eyJ...'
    session_token = os.environ.get('MAVELY_COOKIES')

    if not product_url:
        print("❌ Error: URL recibida vacía.")
        return

    print(f"--- Fila: {row_id} | Procesando: {product_url} ---")

    # API interna de Mavely (formato tRPC)
    api_url = "https://creators.mave.ly/api/trpc/links.create?batch=1"
    
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"__Secure-next-auth.session-token={session_token}",
        "x-trpc-source": "react",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://creators.mave.ly/tools/link-creator"
    }

    # Formato de datos exacto que usa la web de Mavely
    payload = {
        "0": {
            "json": {
                "url": product_url
            }
        }
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Extraer el link del formato tRPC
            try:
                mavely_link = data[0]['result']['data']['json']['link']
                print(f"🚀 ¡CONSEGUIDO!: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            except:
                raise Exception(f"Formato de respuesta desconocido: {data}")
        elif response.status_code == 401:
            raise Exception("Token de sesión expirado. Por favor, actualiza MAVELY_COOKIES en GitHub.")
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")
        requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})

if __name__ == "__main__":
    # Capturamos los argumentos de GitHub
    url_input = sys.argv[1] if len(sys.argv) > 1 else ""
    row_input = sys.argv[2] if len(sys.argv) > 2 else ""
    generate_mavely_link(url_input, row_input)
