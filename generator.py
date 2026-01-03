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
        # Necesitamos permisos de portapapeles para extraer el link copiado
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            permissions=['clipboard-read', 'clipboard-write']
        )
        
        if cookies_json:
            context.add_cookies(json.loads(cookies_json))
        
        page = context.new_page()

        try:
            print(f"Iniciando generador para Fila {row_id}...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            
            # Espera a que la interfaz cargue
            time.sleep(10)

            # ESTRATEGIA: Tabulación y Escritura
            page.keyboard.press("Tab")
            time.sleep(0.5)
            page.keyboard.press("Tab")
            time.sleep(0.5)
            
            print(f"Pegando URL: {product_url}")
            page.keyboard.type(product_url, delay=50)
            page.keyboard.press("Enter")
            
            # Esperamos a que se procese el link
            print("Esperando a que aparezca el botón Copy...")
            time.sleep(8)
            
            # Buscamos el botón de copiar (suele decir 'Copy' o tener un icono de portapapeles)
            # Intentamos hacer clic en el botón que contiene el texto "Copy"
            copy_button = page.get_by_role("button", name="Copy").first
            
            if copy_button.is_visible():
                copy_button.click()
                print("Botón Copy presionado.")
                # Extraemos el contenido del portapapeles usando JS
                mavely_link = page.evaluate("navigator.clipboard.readText()")
            else:
                # Fallback: Intentar buscar cualquier texto que parezca un link
                print("Botón Copy no visible, intentando extracción directa...")
                mavely_link = page.evaluate('''() => {
                    const bodyText = document.body.innerText;
                    const match = bodyText.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                    return match ? match[0] : null;
                }''')

            if not mavely_link or "mavely" not in str(mavely_link):
                raise Exception("No se pudo recuperar el enlace de afiliado.")
            
            # Limpiar el link (por si trae espacios)
            final_link = "https://" + str(mavely_link).split("https://")[-1].strip()
            print(f"¡Éxito total!: {final_link}")

            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": final_link,
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
