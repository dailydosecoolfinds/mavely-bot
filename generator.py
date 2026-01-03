import os
import requests
import sys

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9" 
    session_token = os.environ.get('MAVELY_COOKIES')

    print(f"--- Fila: {row_id} | Generando link para: {product_url} ---")

    # URL de la API interna de Mavely
    api_url = "https://creators.mave.ly/api/links/create"
    
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"__Secure-next-auth.session-token={session_token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://creators.mave.ly/tools/link-creator"
    }

    payload = {"url": product_url}

    try:
        # Petición directa a la API
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        
        if response.status_code in [200, 201]:
            data = response.json()
            # Extraemos el link de la respuesta
            mavely_link = data.get('link') or data.get('data', {}).get('link')
            
            if mavely_link:
                print(f"🚀 ¡ÉXITO!: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={
                    "status": "success",
                    "mavely_link": mavely_link,
                    "row_id": row_id
                })
            else:
                raise Exception(f"Respuesta de API sin link: {data}")
        
        elif response.status_code == 401:
            raise Exception("Token expirado. Copia el valor de la cookie nuevamente.")
        else:
            raise Exception(f"Error Mavely API: {response.status_code} - {response.text}")

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
