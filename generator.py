import os
import time
import requests
import sys
import json
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    cookies_raw = os.environ.get('MAVELY_COOKIES', '[]')

    print(f"--- Iniciando Script | Fila: {row_id} ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        # Carga de cookies con validación de seguridad
        try:
            cookies = json.loads(cookies_raw)
            # Limpiamos campos que dan problemas en Playwright
            for c in cookies:
                c.pop('hostOnly', None)
                c.pop('storeId', None)
                c.pop('sameSite', None) # A veces causa conflicto
            context.add_cookies(cookies)
            print("✅ Cookies cargadas y procesadas.")
        except Exception as e:
            print(f"❌ Error crítico en el formato de MAVELY_COOKIES: {e}")
            return

        page = context.new_page()

        try:
            print(f"Navegando a Mavely...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            time.sleep(10)

            # Verificar Login
            if "login" in page.url or not page.locator('input[placeholder*="Paste"]').first.is_visible():
                print("⚠️ Sesión no activa. Intentando recarga...")
                page.reload()
                time.sleep(5)

            input_box = page.locator('input[placeholder*="Paste"], .MuiInputBase-input').first
            
            if input_box.is_visible():
                print(f"Pegando URL: {product_url}")
                input_box.click()
                page.keyboard.type(product_url, delay=30)
                time.sleep(2)
                page.keyboard.press("Enter")
                
                print("Esperando generación...")
                time.sleep(15)

                # Buscar el link en la página
                mavely_link = page.evaluate("""() => {
                    const match = document.body.innerText.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                    return match ? 'https://' + match[0] : null;
                }""")

                if mavely_link:
                    print(f"🚀 ¡Link Creado!: {mavely_link}")
                    requests.post(MAKE_WEBHOOK_URL, json={
                        "status": "success",
                        "mavely_link": mavely_link,
                        "row_id": row_id
                    })
                else:
                    raise Exception("No se encontró el link generado en la pantalla.")
            else:
                print("❌ No se encontró el cuadro de texto. ¿Expiraron las cookies?")
                page.screenshot(path="error.png")

        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Faltan argumentos: url y row_id")
    else:
        generate_mavely_link(sys.argv[1], sys.argv[2])
