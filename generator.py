import os
import time
import requests
import sys
import json
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    print(f"--- Iniciando Script | Fila: {row_id} ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("Accediendo a Mavely...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle")
            time.sleep(5)

            # Si nos pide login
            if page.locator('input[type="email"]').is_visible():
                print("Sesión no detectada. Iniciando sesión manualmente...")
                page.locator('input[type="email"]').fill(email)
                page.locator('input[type="password"]').fill(password)
                page.get_by_role("button", name="Sign In").click()
                print("Esperando a que cargue el dashboard...")
                page.wait_for_url("**/tools/link-creator", timeout=30000)
                time.sleep(5)

            # Proceso de pegado de link
            input_box = page.locator('input[placeholder*="Paste"], .MuiInputBase-input').first
            if input_box.is_visible():
                print(f"Generando link para: {product_url}")
                input_box.click()
                page.keyboard.type(product_url, delay=30)
                time.sleep(2)
                page.keyboard.press("Enter")
                
                print("Esperando resultado...")
                time.sleep(15)

                mavely_link = page.evaluate("""() => {
                    const match = document.body.innerText.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                    return match ? 'https://' + match[0] : null;
                }""")

                if mavely_link:
                    print(f"🚀 ÉXITO: {mavely_link}")
                    requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
                else:
                    raise Exception("No se visualiza el link generado.")
            else:
                raise Exception("No se pudo acceder al generador de links.")

        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="error.png")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    generate_mavely_link(sys.argv[1], sys.argv[2])
