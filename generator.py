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

    print(f"--- Iniciando Proceso | Fila: {row_id} ---")

    with sync_playwright() as p:
        # Lanzamos con slow_mo para que Mavely no detecte movimientos demasiado rápidos
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Accediendo a Mavely...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            time.sleep(5)

            # --- LÓGICA DE LOGIN ---
            if page.locator('input[name="email"], input[type="email"]').is_visible():
                print("Sesión no activa. Iniciando sesión...")
                page.locator('input[name="email"], input[type="email"]').fill(email)
                time.sleep(1)
                page.locator('input[name="password"], input[type="password"]').fill(password)
                time.sleep(1)
                
                # Clic en el botón de entrar (buscamos por texto para más precisión)
                login_btn = page.locator('button:has-text("Sign In"), button[type="submit"]').first
                login_btn.click()
                
                print("Esperando redirección al Link Creator...")
                # Esperamos a que el cuadro de texto de links aparezca tras el login
                page.wait_for_selector('input[placeholder*="Paste"]', timeout=40000)
                print("✅ Login exitoso.")
            else:
                print("✅ Sesión ya estaba activa.")

            # --- PROCESO DE GENERACIÓN ---
            print(f"Generando link para: {product_url}")
            input_box = page.locator('input[placeholder*="Paste"]').first
            input_box.click()
            page.keyboard.type(product_url, delay=40)
            time.sleep(2)
            page.keyboard.press("Enter")
            
            # Esperar a que el link aparezca en pantalla
            print("Procesando enlace (15s)...")
            time.sleep(15)

            # Extraer link usando Regex en el texto de la página
            mavely_link = page.evaluate("""() => {
                const match = document.body.innerText.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                return match ? 'https://' + match[0] : null;
            }""")

            if not mavely_link:
                # Intento extra: buscar botón de copiar
                if page.locator('button:has-text("Copy")').is_visible():
                    print("Link generado detectado visualmente.")
                    mavely_link = "Enlace generado correctamente (ver panel)"

            if mavely_link:
                print(f"🚀 ÉXITO: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={
                    "status": "success", 
                    "mavely_link": mavely_link, 
                    "row_id": row_id
                })
            else:
                raise Exception("Mavely no mostró el link generado a tiempo.")

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            # Si falla, mandamos el error a Make para no quedarnos a ciegas
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "error", 
                "message": error_msg, 
                "row_id": row_id
            })
            page.screenshot(path="error_debug.png")
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
