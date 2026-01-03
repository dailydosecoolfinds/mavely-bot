import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    print(f"--- Iniciando Fila: {row_id} | URL: {product_url} ---")

    with sync_playwright() as p:
        # Modo headless=True (obligatorio en GitHub)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("Paso 1: Login...")
            page.goto("https://creators.mave.ly/login", wait_until="networkidle", timeout=60000)
            
            # Llenar login
            page.wait_for_selector('input[type="email"]', timeout=20000)
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            
            # Esperar a entrar
            print("Esperando Dashboard...")
            time.sleep(10) 

            # Ir a la herramienta
            print("Paso 2: Herramienta de Links...")
            page.goto("https://creators.mave.ly/tools/link-creator", wait_until="networkidle")
            time.sleep(10)

            # Intentar localizar el cuadro de texto de varias formas
            print("Paso 3: Localizando campo de pegado...")
            # Intentamos cerrar cualquier pop-up primero
            page.keyboard.press("Escape")
            
            # Buscamos el input
            input_selector = 'input[placeholder*="http"], input[placeholder*="Paste"], .MuiInputBase-input'
            page.wait_for_selector(input_selector, timeout=30000)
            
            input_field = page.locator(input_selector).first
            input_field.click()
            input_field.fill(product_url)
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("Paso 4: Esperando Link...")
            time.sleep(15)

            # Extraer link por texto
            content = page.content()
            import re
            links = re.findall(r'https://mavely\.app\.link/\w+', content)
            
            if links:
                mavely_link = links[0]
                print(f"🚀 ENLACE CREADO: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            else:
                raise Exception("No se encontró el enlace generado en la página.")

        except Exception as e:
            print(f"❌ Error: {e}")
            # Si falla, guardamos captura para ver el error real
            page.screenshot(path="debug_error.png")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
    else:
        print("Error: Faltan argumentos (url o row_id)")
