import os
import time
import requests
import sys
import re
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    print(f"--- Iniciando | Fila: {row_id} ---")

    with sync_playwright() as p:
        # Argumentos para desactivar la detección de automatización
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ])
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Inyectar un script para ocultar el objeto 'navigator.webdriver'
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        try:
            print("Paso 1: Login...")
            page.goto("https://creators.joinmavely.com/login", wait_until="networkidle")
            
            # Esperar a que el formulario sea real
            page.wait_for_selector('input[name="email"]', timeout=30000)
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            
            # Esperar a que el dashboard cargue de verdad
            print("Esperando Dashboard...")
            page.wait_for_url("**/home", timeout=60000)
            time.sleep(5)

            print("Paso 2: Herramienta de Links...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle")
            
            # ESPERA CRÍTICA: En lugar de buscar un input genérico, buscamos la estructura de Mavely
            print("Buscando interfaz de creación...")
            # Mavely usa un input dentro de un div con una clase específica o placeholder
            selector_final = 'input[placeholder*="Paste"], input[type="text"]'
            page.wait_for_selector(selector_final, state="visible", timeout=45000)
            
            input_box = page.locator(selector_final).first
            input_box.click()
            page.keyboard.type(product_url, delay=100) # Más lento para parecer humano
            time.sleep(1)
            page.keyboard.press("Enter")
            
            print("Paso 3: Extracción...")
            # Mavely a veces tarda, esperamos a que el link aparezca en el DOM
            time.sleep(15)

            # Buscamos cualquier texto que parezca un link de mavely
            content = page.content()
            match = re.search(r'mavely\.app\.link\/[a-zA-Z0-9]+', content)
            
            if match:
                mavely_link = "https://" + match.group(0)
                print(f"🚀 LOGRADO: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            else:
                # Si falló, tomamos una captura para ver qué hay en pantalla
                page.screenshot(path="debug_final.png")
                raise Exception("Link no encontrado tras login exitoso.")

        except Exception as e:
            print(f"❌ Error detallado: {e}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    generate_mavely_link(sys.argv[1], sys.argv[2])
