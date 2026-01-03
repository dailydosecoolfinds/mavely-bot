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
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        if cookies_json:
            context.add_cookies(json.loads(cookies_json))
        
        page = context.new_page()

        try:
            print(f"Abriendo Link Creator (Fila {row_id})...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            
            # Espera a que la app de Mavely se monte por completo
            time.sleep(12)

            # ESTRATEGIA: Navegación por Teclado (Focus)
            # Presionamos Tab un par de veces para entrar al área de contenido y el campo de URL
            print("Navegando hacia el campo de entrada...")
            page.keyboard.press("Tab")
            time.sleep(1)
            page.keyboard.press("Tab")
            time.sleep(1)
            
            # Escribimos la URL directamente (esto funciona incluso si el selector falla)
            print(f"Escribiendo URL: {product_url}")
            page.keyboard.type(product_url, delay=100) # delay simula escritura humana
            time.sleep(2)
            page.keyboard.press("Enter")
            
            print("URL enviada. Esperando resultado...")
            
            # Intentamos detectar el link generado por su prefijo
            # Si el selector falla, esperamos un tiempo razonable
            try:
                page.wait_for_selector('text=mavely.app.link', timeout=20000)
                link_element = page.locator('text=mavely.app.link').first
                mavely_link = link_element.inner_text()
            except:
                # Si no aparece el texto, buscamos cualquier elemento que parezca un link generado
                print("Selector de texto falló, buscando link por atributo...")
                mavely_link = page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll('a, p, span'));
                    const found = links.find(el => el.innerText.includes('mavely.app.link'));
                    return found ? found.innerText : null;
                }''')

            if not mavely_link:
                raise Exception("El enlace no apareció en pantalla tras enviar la URL.")
            
            print(f"¡Éxito!: {mavely_link}")

            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": mavely_link.strip(),
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
