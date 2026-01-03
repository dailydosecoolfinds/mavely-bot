import os
import time
import requests
import sys
import json
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/f74d3eppf9xthkcz8pxumuss7tvcr8k9"
    cookies_json = os.environ.get('MAVELY_COOKIES')

    with sync_playwright() as p:
        # Lanzamos el navegador
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        # Cargar cookies si existen
        if cookies_json:
            try:
                context.add_cookies(json.loads(cookies_json))
            except Exception as e:
                print(f"Error al cargar JSON de cookies: {e}")
        
        page = context.new_page()

        try:
            print(f"--- Iniciando Proceso Fila {row_id} ---")
            print(f"Abriendo Link Creator para: {product_url}")
            
            # 1. Navegar a la herramienta
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            time.sleep(8) # Espera para carga de scripts internos

            # 2. VERIFICACIÓN DE SESIÓN
            # Buscamos elementos que solo aparecen si estás logueado (como el botón logout o el avatar)
            is_logged_in = page.locator('button:has-text("Logout"), a[href*="logout"], .user-profile').count()
            if is_logged_in > 0:
                print("✅ Sesión detectada correctamente.")
            else:
                print("⚠️ ADVERTENCIA: No se detecta sesión activa. Es muy probable que las cookies hayan expirado.")

            # 3. Localizar el cuadro de texto de forma flexible
            print("Buscando cuadro de texto...")
            # Probamos varios selectores comunes en Mavely
            input_selector = 'input[placeholder*="Paste"], input[type="text"], .MuiInputBase-input'
            input_box = page.locator(input_selector).first
            
            if input_box.is_visible():
                input_box.click()
                # Limpiar campo por si acaso
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                
                # Escribir URL simulando teclado humano para evitar bloqueos
                page.keyboard.type(product_url, delay=40)
                time.sleep(2)
                
                # Intentar clic en botón "Create"
                create_button = page.locator('button:has-text("Create"), button:has-text("Generate")').first
                if create_button.is_visible() and create_button.is_enabled():
                    print("Haciendo clic en el botón 'Create'...")
                    create_button.click()
                else:
                    print("Botón no clickable, intentando con tecla Enter...")
                    page.keyboard.press("Enter")
            else:
                raise Exception("No se encontró el campo de entrada. La página podría haber cambiado o no cargó el login.")

            # 4. Esperar y Capturar el Link
            print("Esperando generación del enlace (15s)...")
            time.sleep(15)

            # Intentar extraer el link mediante RegEx en todo el texto de la página
            mavely_link = page.evaluate("""() => {
                const text = document.body.innerText;
                const match = text.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                return match ? 'https://' + match[0] : null;
            }""")

            # Si falla el texto, intentar buscar un elemento <a> que lo contenga
            if not mavely_link:
                link_element = page.locator('a[href*="mavely.app.link"]').first
                if link_element.count() > 0:
                    mavely_link = link_element.get_attribute("href")

            if not mavely_link:
                # Si llegamos aquí, algo falló. Tomamos foto para el log de GitHub
                page.screenshot(path="debug_screen.png")
                raise Exception("Mavely no devolvió un link. Revisa si la URL original es válida o si las cookies expiraron.")
            
            print(f"🚀 ¡EXITO! Link generado: {mavely_link}")

            # 5. Enviar a Make
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": mavely_link,
                "row_id": row_id,
                "original_url": product_url
            })

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "error", 
                "message": error_msg, 
                "row_id": row_id
            })
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
