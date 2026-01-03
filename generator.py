import os
import requests
import sys

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9" 
    session_token = os.environ.get('MAVELY_COOKIES')

    print(f"--- Fila: {row_id} | Generando link para: {product_url} ---")

    # Nueva URL de la API basada en el protocolo tRPC que usa Mavely ahora
    api_url = "https://creators.mave.ly/api/trpc/links.create?batch=1"
    
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"__Secure-next-auth.session-token={session_token}",
        "x-trpc-source": "react", # Este encabezado es CRUCIAL ahora
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://creators.mave.ly/tools/link-creator"
    }

    # El cuerpo del mensaje (payload) ahora debe ir numerado por el formato tRPC
    payload = {
        "0": {
            "json": {
                "url": product_url
            }
        }
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            # Estructura de respuesta tRPC: [0].result.data.json.link
            try:
                mavely_link = data[0]['result']['data']['json']['link']
                print(f"🚀 ¡ÉXITO TOTAL!: {mavely_link}")
                
                requests.post(MAKE_WEBHOOK_URL, json={
                    "status": "success",
                    "mavely_link": mavely_link,
                    "row_id": row_id
                })
            except (KeyError, IndexError):
                raise Exception(f"La API respondió pero el formato cambió: {data}")
        
        elif response.status_code == 401:
            raise Exception("Token expirado. Por favor, obtén un nuevo session-token.")
        else:
            raise Exception(f"Error de API {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")
        requests.post(MAKE_WEBHOOK_URL, json={
            "status": "error",
            "message": str(e),
            "row_id": row_id
        })

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
