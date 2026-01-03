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
        # Usamos un perfil más robusto
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        if cookies_json:
            try:
                # Limpieza de cookies: Playwright a veces falla si el dominio tiene 'hostOnly'
                raw_cookies = json.loads(cookies_json)
                for cookie in raw_cookies:
                    if 'hostOnly' in cookie: del cookie['hostOnly']
                    if 'storeId' in cookie: del cookie['storeId']
                context.add_cookies(raw_cookies)
            except Exception as e:
                print(f"Error cargando cookies: {e}")
        
        page = context.new_page()

        try:
            print(f"--- Fila {row_id} | URL: {product_url} ---")
            
            # Navegar a la home primero para asentar las cookies
            page.goto("https://creators.joinmavely.com/", wait_until="networkidle")
            time.sleep(5)
            
            # Ahora ir a la herramienta de links
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle")
            time.sleep(10)

            # Verificación visual mejorada
            if page.get_by_text("Logout").is_visible() or page.locator(".MuiAvatar-root").is_visible():
                print("✅ Sesión detectada correctamente.")
            else:
                print("⚠️ Intento de re-carga de sesión...")
                page.reload()
                time.sleep(5)

            # Localizar el input
            input_selector = 'input[placeholder*="Paste"], .MuiInputBase-input'
            input_box = page.locator(input_selector).first
            
            if not input_box.is_visible():
                # Si sigue sin verse, es que Mavely nos sacó. Tomamos debug y lanzamos error.
                page.screenshot(path="debug_error.png")
                raise Exception("Sesión no activa tras reintentos. Revisa las cookies en GitHub.")

            print("Insertando URL...")
            input_box.click()
            page.keyboard.type(product_url, delay=50)
            time.sleep(2)
            
            # Click en el botón de crear
            create_btn = page.locator('button:has-text("Create"), button:has-text("Generate")').first
            create_btn.click()
            
            print("Generando link...")
            time.sleep(15)

            # Extraer link
            mavely_link = page.evaluate("""() => {
                const text = document.body.innerText;
                const match = text.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                return match ? 'https://' + match[0] : null;
            }""")

            if not mavely_link:
                # Último intento buscando el botón de "Copy"
                copy_btn = page.locator('button:has-text("Copy")').first
                if copy_btn.is_visible():
                    # Si hay botón de copy, el link existe pero no se ve en texto plano
                    print("Link generado (detectado por botón Copy).")
                    mavely_link = "Revisa tu panel de Mavely (Link detectado pero no extraído)"

            if not mavely_link:
                raise Exception("Link no encontrado en la página final.")

            print(f"🚀 Link: {mavely_link}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})

        except Exception as e:
            print(f"❌ Error: {e}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()
