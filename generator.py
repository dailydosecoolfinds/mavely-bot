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
        # Cargamos un perfil con las cookies
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        if cookies_json:
            context.add_cookies(json.loads(cookies_json))
        
        page = context.new_page()

        try:
            print(f"Entrando directamente al generador para fila {row_id}...")
            
            # Vamos directo a la herramienta de links
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            
            # Verificamos si estamos dentro o si nos echó al login
            if "login" in page.url:
                print("Error: Las cookies han expirado o son inválidas.")
                raise Exception("Auth Required")

            # Pegar y Generar
            input_xpath = "//input[contains(@placeholder, 'Paste')] | //input[contains(@placeholder, 'URL')]"
            page.wait_for_selector(input_xpath, timeout=30000)
            page.fill(input_xpath, product_url)
            page.keyboard.press("Enter")
            
            print("Esperando generación de link...")
            time.sleep(10) # Damos tiempo extra
            
            # Extraer link
            mavely_link = page.locator('text=mavely.app.link').first.inner_text()
            print(f"Éxito: {mavely_link}")

            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": mavely_link,
                "row_id": row_id
            })

        except Exception as e:
            print(f"Error: {e}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
