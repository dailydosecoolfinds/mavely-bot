import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url):
    # URL del Webhook de Make que acabas de crear
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9" 
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Login
            page.goto("https://admin.joinmavely.com/login")
            page.fill('input[type="email"]', os.environ['MAVELY_EMAIL'])
            page.fill('input[type="password"]', os.environ['MAVELY_PASSWORD'])
            page.click('button[type="submit"]')
            page.wait_for_url("**/dashboard**", timeout=60000)

            # 2. Ir a la sección de Links
            page.goto("https://admin.joinmavely.com/links")
            
            # 3. Generar el Link
            input_selector = 'input[placeholder*="Paste"]'
            page.wait_for_selector(input_selector)
            page.fill(input_selector, product_url)
            page.keyboard.press("Enter") # A veces es más seguro que el click
            
            time.sleep(5) # Esperar a que el sistema procese

            # 4. Extraer el link (Ajusta el selector según la interfaz actual)
            # Normalmente Mavely muestra el link en un campo que dice 'mavely.app.link'
            generated_link = page.locator('text=mavely.app.link').first.inner_text()

            # 5. ENVIAR DE VUELTA A MAKE
            payload = {
                "mavely_link": generated_link,
                "status": "success",
                "original_url": product_url
            }
            requests.post(MAKE_WEBHOOK_URL, json=payload)
            print(f"Success: {generated_link}")

        except Exception as e:
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e)})
            print(f"Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    url_to_process = sys.argv[1]
    generate_mavely_link(url_to_process)
