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
            
            # Espera para que cargue el contenido dinámico
            time.sleep(7)

            # --- ESCANEO INTELIGENTE ---
            # Buscamos todos los inputs y filtramos el que parece ser el generador
            found_input = False
            inputs = page.query_selector_all("input")
            
            print(f"Se encontraron {len(inputs)} campos de entrada.")
            
            for i, el in enumerate(inputs):
                placeholder = el.get_attribute("placeholder") or ""
                if "http" in placeholder.lower() or "paste" in placeholder.lower() or "url" in placeholder.lower():
                    print(f"Campo detectado por placeholder: '{placeholder}'")
                    el.click()
                    el.fill("")
                    el.fill(product_url)
                    found_input = True
                    break
            
            # Si no se encontró por placeholder, intentamos el primer input visible
            if not found_input:
                for el in inputs:
                    if el.is_visible():
                        print("Usando primer campo visible disponible.")
                        el.click()
                        el.fill(product_url)
                        found_input = True
                        break

            if not found_input:
                raise Exception("No se pudo localizar el cuadro de texto de la URL.")

            # Presionar Enter para generar
            page.keyboard.press("Enter")
            print("Esperando generación del enlace...")
            
            # Esperamos específicamente a que aparezca un elemento que contenga "mavely.app.link"
            # O un botón que permita copiar el link
            page.wait_for_selector('text=mavely.app.link', timeout=30000)
            
            # Extraer el texto del link
            # Intentamos obtener el texto que contiene el dominio del link de afiliado
            link_element = page.locator('text=mavely.app.link').first
            mavely_link = link_element.inner_text()
            
            print(f"¡Link generado con éxito!: {mavely_link}")

            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": mavely_link,
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
