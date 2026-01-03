import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9" # ASEGÚRATE DE QUE ESTÉ BIEN PUESTA
    
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    with sync_playwright() as p:
        # Usamos un User Agent de una persona real para evitar bloqueos
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"Iniciando proceso para la fila {row_id}...")
            
            # URL CORREGIDA: creators.joinmavely.com
            page.goto("https://creators.joinmavely.com/login", wait_until="domcontentloaded")
            
            # Login
            page.wait_for_selector('input[type="email"]')
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            
            # Esperar a entrar
            page.wait_for_url("**/dashboard**", timeout=60000)
            print("Login exitoso.")

            # Ir a la página de herramientas/links
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle")
            
            # Pegar URL y Generar
            input_selector = 'input[placeholder*="Paste"]'
            page.wait_for_selector(input_selector)
            page.fill(input_selector, product_url)
            page.keyboard.press("Enter")
            
            # Esperar el resultado
            time.sleep(7) 
            
            # Buscar el link de mavely en el texto de la página
            content = page.content()
            if "mavely.app.link" in content:
                # Extraemos el link usando una técnica más flexible
                mavely_link = page.locator('text=mavely.app.link').first.inner_text()
                status = "success"
                print(f"Link creado: {mavely_link}")
            else:
                mavely_link = "No se pudo extraer el link"
                status = "error"

            # 4. ENVIAR A MAKE
            payload = {
                "status": status,
                "mavely_link": mavely_link,
                "row_id": row_id,
                "original_url": product_url
            }
            requests.post(MAKE_WEBHOOK_URL, json=payload)

        except Exception as e:
            print(f"Error: {e}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
