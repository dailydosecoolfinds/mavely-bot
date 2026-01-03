import os
import requests
import sys
import json

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    
    # 1. Obtener el token y LIMPIARLO de espacios, saltos de línea o comillas accidentales
    raw_token = os.environ.get('MAVELY_COOKIES', '')
    session_token = raw_token.strip().replace('"', '').replace("'", "")

    if not product_url:
        print("❌ Error: URL recibida vacía desde Make/GitHub.")
        return

    if not session_token:
        print("❌ Error: No se encontró el token MAVELY_COOKIES en los Secretos.")
        return

    print(f"--- Fila: {row_id} | Procesando URL: {product_url} ---")

    # API interna de Mavely (formato tRPC)
    api_url = "https://creators.mave.ly/api/trpc/links.create?batch=1"
    
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"__Secure-next-auth.session-token={session_token}",
        "x-trpc-source": "react",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://creators.mave.ly/tools/link-creator"
    }

    # Estructura exacta requerida por el servidor de Mavely
    payload = {
        "0": {
            "json": {
                "url": product_url
            }
        }
    }

    try:
        # Petición directa al servidor (sin abrir navegador)
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Navegar por el JSON de tRPC para encontrar el link
            try:
                mavely_link = data[0]['result']['data']['json']['link']
                print(f"🚀 ¡CONSEGUIDO!: {mavely_link}")
                
                # Enviar éxito a Make
                requests.post(MAKE_WEBHOOK_URL, json={
                    "status": "success", 
                    "mavely_link": mavely_link, 
                    "row_id": row_id
                })
            except (KeyError, IndexError, TypeError) as e:
                print(f"❌ Error al leer la respuesta: {e}")
                raise Exception(f"Formato de respuesta desconocido: {data}")
        
        elif response.status_code == 401:
            raise Exception("Token expirado. Copia el nuevo valor de '__Secure-next-auth.session-token' en GitHub.")
        else:
            raise Exception(f"Error {response.status_code} en servidor Mavely: {response.text}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        # Enviar error a Make para que sepas qué pasó
        requests.post(MAKE_WEBHOOK_URL, json={
            "status": "error", 
            "message": str(e), 
            "row_id": row_id
        })

if __name__ == "__main__":
    # Captura de argumentos pasados por GitHub Actions
    # sys.argv[1] es la URL, sys.argv[2] es el ID de la fila
    url_input = sys.argv[1] if len(sys.argv) > 1 else ""
    row_input = sys.argv[2] if len(sys.argv) > 2 else ""
    
    generate_mavely_link(url_input, row_input)
