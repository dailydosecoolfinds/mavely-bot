import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    print(f"--- Iniciando Fila: {row_id} ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("Accediendo a Mavely...")
            page.goto("https://creators.mave.ly/login", wait_until="networkidle")
            
            # 1. Login Manual (Más robusto)
            if page.locator('input[type="email"]').is_visible():
                print("Introduciendo credenciales...")
                page.fill('input[type="email"]', email)
                page.fill('input[type="password"]', password)
                page.click('button[type="submit"]')
                page.wait_for_load_state("networkidle")
                time.sleep(5)

            # 2. Ir a la herramienta
            print("Navegando al Link Creator...")
            page.goto("https://creators.mave.ly/tools/link-creator", wait_until="networkidle")
            time.sleep(8)

            # 3. Quitar basura (Modales, anuncios, capas)
            page.evaluate("() => { document.querySelectorAll('[class*=\"backdrop\"], [class*=\"modal\"], [class*=\"Dialog\"]').forEach(el => el.remove()); }")

            # 4. Buscar el input por su función, no por su nombre
            print("Buscando campo de texto...")
            # Buscamos cualquier input que sea para escribir (textbox)
            input_field = page.get_by_role("textbox").first
            
            if not input_field.is_visible():
                # Si no lo ve, intenta buscar por el placeholder que usa Mavely
                input_field = page.locator('input[placeholder*="http"], input[placeholder*="Paste"]').first

            input_field.click()
            input_field.fill(product_url)
            print("URL pegada. Generando...")
            page.keyboard.press("Enter")
            
            # 5. Capturar el link generado
            time.sleep(12)
            
            # Buscamos el link en el texto de la página
            page_content = page.content()
            import re
            links = re.findall(r'https://mavely\.app\.link/\w+', page_content)
            
            if links:
                final_link = links[0]
                print(f"🚀 ENLACE: {final_link}")
                requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": final_link, "row_id": row_id})
            else:
                # Si no lo encuentra, buscamos un botón que diga "Copy"
                copy_btn = page.get_by_text("Copy Link").first
                if copy_btn.is_visible():
                    print("Link detectado mediante botón Copy.")
                    requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": "Generado (Ver en Mavely)", "row_id": row_id})
                else:
                    raise Exception("No se pudo extraer el link.")

        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="error_debug.png")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    generate_mavely_link(sys.argv[1], sys.argv[2])
