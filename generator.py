import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    print(f"--- Fila: {row_id} | URL: {product_url} ---")

    with sync_playwright() as p:
        # Iniciamos sin cookies previas para evitar conflictos de sesión expirada
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            # 1. IR AL LOGIN PRIMERO (Para asegurar que estamos dentro)
            print("Paso 1: Asegurando sesión...")
            page.goto("https://creators.joinmavely.com/login", wait_until="networkidle")
            
            if page.locator('input[name="email"]').is_visible():
                print("Iniciando sesión desde cero...")
                page.locator('input[name="email"]').fill(email)
                page.locator('input[name="password"]').fill(password)
                page.click('button[type="submit"]')
                page.wait_for_url("**/home", timeout=60000)
                print("✅ Login completado.")
            
            # 2. IR A LA HERRAMIENTA
            print("Paso 2: Entrando al creador de links...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle")
            time.sleep(8)

            # 3. ELIMINAR CUALQUIER CAPA QUE BLOQUEE (Pop-ups)
            # Este código borra cualquier cosa que esté por encima del cuadro de texto
            page.evaluate("""() => {
                const selectors = ['.MuiDialog-root', '.MuiBackdrop-root', '[role="presentation"]'];
                selectors.forEach(s => {
                    const elements = document.querySelectorAll(s);
                    elements.forEach(el => el.remove());
                });
            }""")
            print("Limpieza de pop-ups ejecutada.")

            # 4. BUSCAR EL CUADRO DE TEXTO (Selector simplificado)
            print("Paso 3: Localizando entrada de texto...")
            # Usamos el selector más básico posible que tiene Mavely para ese campo
            input_box = page.locator('input').first 
            
            input_box.wait_for(state="visible", timeout=20000)
            input_box.click()
            
            # Escribir con un delay mayor para asegurar que el sistema lo procesa
            print("Escribiendo URL...")
            page.keyboard.type(product_url, delay=60)
            time.sleep(2)
            page.keyboard.press("Enter")
            
            # 5. CAPTURAR EL LINK
            print("Paso 4: Extrayendo resultado...")
            time.sleep(15)

            # Buscamos el link en los elementos <a> o en el texto
            mavely_link = page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a'));
                const found = links.find(a => a.href.includes('mavely.app.link'));
                return found ? found.href : null;
            }""")

            if not mavely_link:
                # Intento final por texto plano
                text = page.content()
                import re
                match = re.search(r'mavely\.app\.link\/[a-zA-Z0-9]+', text)
                if match:
                    mavely_link = "https://" + match.group(0)

            if mavely_link:
                print(f"🚀 ¡CONSEGUIDO!: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            else:
                # Si falló la extracción pero el bot llegó aquí, tomamos foto
                page.screenshot(path="debug_final.png")
                raise Exception("El link no apareció en la página. Mavely podría estar lento.")

        except Exception as e:
            print(f"❌ Error final: {e}")
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    generate_mavely_link(sys.argv[1], sys.argv[2])
