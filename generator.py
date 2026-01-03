import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9" 
    
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    with sync_playwright() as p:
        # Iniciamos con parámetros de navegador real
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Procesando fila {row_id}...")
            
            # 1. Navegación con espera extendida
            page.goto("https://creators.joinmavely.com/login", wait_until="networkidle", timeout=60000)
            
            # A veces hay una pantalla de carga, esperamos a que el input sea visible
            print("Esperando formulario de login...")
            page.wait_for_selector('input[name="email"], input[type="email"]', state="visible", timeout=45000)
            
            # 2. Login
            page.fill('input[name="email"], input[type="email"]', email)
            page.fill('input[name="password"], input[type="password"]', password)
            page.click('button[type="submit"]')
            
            # 3. Esperar al Dashboard
            print("Login enviado, esperando Dashboard...")
            page.wait_for_url("**/dashboard**", timeout=60000)
            
            # 4. Ir al Link Creator
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle")
            
            # 5. Pegar y Generar
            input_xpath = "//input[contains(@placeholder, 'Paste')] | //input[contains(@placeholder, 'URL')]"
            page.wait_for_selector(input_xpath, timeout=30000)
            page.fill(input_xpath, product_url)
            page.keyboard.press("Enter")
            
            # Esperar a que el link aparezca (suele tardar unos segundos en generarse)
            time.sleep(8)
            
            # 6. Extraer el link
            # Buscamos el texto que contiene el dominio de mavely
            mavely_link_locator = page.locator('text=mavely.app.link').first
            if mavely_link_locator.is_visible():
                mavely_link = mavely_link_locator.inner_text()
                status = "success"
                print(f"Link generado: {mavely_link}")
            else:
                # Intento alternativo por atributo de valor
                mavely_link = page.eval_on_selector('input[value*="mavely.app.link"]', 'el => el.value')
                status = "success"

            # Enviar a Make
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": status,
                "mavely_link": mavely_link,
                "row_id": row_id
            })

        except Exception as e:
            print(f"Error detectado: {e}")
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
