import os
import time
import requests
import sys
import json
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    cookies_json = os.environ.get('MAVELY_COOKIES')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Forzamos una resolución de escritorio clara
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        if cookies_json:
            context.add_cookies(json.loads(cookies_json))
        
        page = context.new_page()

        try:
            print(f"Abriendo Link Creator para fila {row_id}...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            
            # 1. Buscar el input de forma más agresiva (por tipo o por clase si el placeholder falla)
            # Intentamos primero el selector anterior y luego uno genérico de tipo 'url' o 'text'
            input_selector = 'input[placeholder*="Paste"], input[type="url"], .MuiInputBase-input'
            
            print("Buscando campo de entrada...")
            page.wait_for_selector(input_selector, timeout=30000)
            
            # 2. Limpiar (por si acaso) y pegar la URL
            page.fill(input_selector, "")
            page.fill(input_selector, product_url)
            print(f"URL pegada: {product_url}")
            
            # 3. Presionar el botón de Crear (buscando por texto "Create" o Enter)
            page.keyboard.press("Enter")
            
            print("Esperando a que el sistema genere el link...")
            # Mavely suele mostrar un link que contiene 'mavely.app.link'
            # Esperamos a que aparezca ese texto en la página
            page.wait_for_selector('text=mavely.app.link', timeout=30000)
            
            # 4. Extraer el link
            mavely_link = page.locator('text=mavely.app.link').first.inner_text()
            print(f"¡Éxito! Link obtenido: {mavely_link}")

            # 5. Notificar a Make
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": mavely_link,
                "row_id": row_id
            })

        except Exception as e:
            print(f"Error en el proceso: {e}")
            # Si falla, intentamos tomar una captura de pantalla (opcional para debug)
            # page.screenshot(path="error.png") 
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "error",
                "message": str(e),
                "row_id": row_id
            })
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
