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
        browser = p.chromium.launch(headless=True)
        # Usamos un User Agent de una persona real para evitar bloqueos
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. Ir directamente a la herramienta
            print("Navegando directamente a la herramienta de links...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="load", timeout=60000)
            time.sleep(10)

            # 2. Manejo de Login si es necesario
            if page.locator('input[name="email"]').is_visible():
                print("Formulario de Login detectado. Entrando...")
                page.locator('input[name="email"]').fill(email)
                page.locator('input[name="password"]').fill(password)
                page.click('button[type="submit"]')
                # Esperar a que cargue la herramienta tras loguearse
                page.wait_for_url("**/tools/link-creator", timeout=60000)
                time.sleep(10)

            # 3. Cerrar posibles Pop-ups (Anuncios de Mavely)
            print("Limpiando posibles obstáculos visuales...")
            try:
                # Intenta presionar Escape para cerrar diálogos o busca botones de "Close" / "X"
                page.keyboard.press("Escape")
                if page.locator('button[aria-label="Close"], .close-button').is_visible():
                    page.locator('button[aria-label="Close"], .close-button').click()
            except:
                pass

            # 4. Localizar Input de forma agresiva
            print("Localizando cuadro de texto...")
            # Intentamos con varios selectores posibles que usa Mavely
            input_selector = 'input[placeholder*="Paste"], .MuiInputBase-input, input[type="text"]'
            input_box = page.locator(input_selector).first
            
            # Esperar a que sea editable
            input_box.wait_for(state="visible", timeout=30000)
            
            print("Pegando URL y generando...")
            input_box.click()
            page.keyboard.type(product_url, delay=50)
            time.sleep(2)
            page.keyboard.press("Enter")
            
            # 5. Esperar y Capturar el resultado
            print("Esperando el enlace de Mavely...")
            time.sleep(15)

            mavely_link = page.evaluate("""() => {
                const match = document.body.innerText.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                return match ? 'https://' + match[0] : null;
            }""")

            if mavely_link:
                print(f"🚀 ENLACE CREADO: {mavely_link}")
                requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": mavely_link, "row_id": row_id})
            else:
                # Si no lo encuentra por texto, buscamos el botón "Copy"
                if page.get_by_text("Copy").is_visible():
                    print("Enlace generado detectado (botón Copy listo).")
                    # Intentamos extraerlo del atributo si es posible o enviamos confirmación
                    requests.post(MAKE_WEBHOOK_URL, json={"status": "success", "mavely_link": "Generado (Ver en Mavely)", "row_id": row_id})
                else:
                    raise Exception("No se pudo extraer el link final. ¿URL inválida?")

        except Exception as e:
            print(f"❌ Error detallado: {e}")
            page.screenshot(path="debug.png") # Esto ayuda a ver qué veía el bot
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    generate_mavely_link(sys.argv[1], sys.argv[2])
