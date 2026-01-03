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
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        if cookies_json:
            context.add_cookies(json.loads(cookies_json))
        
        page = context.new_page()

        try:
            print(f"Abriendo Link Creator para fila {row_id}...")
            # Cargamos la página y esperamos a que no haya más actividad de red
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=90000)
            
            # Pausa táctica para que los scripts internos de Mavely se ejecuten
            time.sleep(10)
            
            print("Buscando campo de entrada por múltiples métodos...")
            
            # Intentamos encontrar el input de forma jerárquica
            # 1. Por placeholder común
            # 2. Por ser el único input de tipo texto en la zona central
            # 3. Por clase de Material UI
            input_found = False
            selectors = [
                'input[placeholder*="Paste"]', 
                'input[type="text"]', 
                'input[type="url"]',
                '.MuiInputBase-input',
                'div[role="main"] input'
            ]
            
            target_input = None
            for selector in selectors:
                try:
                    locator = page.locator(selector).first
                    if locator.is_visible():
                        target_input = locator
                        print(f"Campo encontrado usando: {selector}")
                        input_found = True
                        break
                except:
                    continue
            
            if not input_found:
                # Si fallan los selectores, intentamos hacer click en el centro de la pantalla
                # y escribir, a veces el input está pero oculto para el bot
                print("Intentando enfoque directo por coordenadas...")
                page.mouse.click(600, 400) # Click estimado en la zona del input
                target_input = page.keyboard

            # Pegar la URL
            if input_found:
                target_input.fill("")
                target_input.fill(product_url)
            else:
                page.keyboard.type(product_url)
            
            page.keyboard.press("Enter")
            print(f"URL enviada: {product_url}")
            
            # Esperar el link generado
            print("Esperando link final...")
            # Mavely suele mostrar el link en un elemento que dice "mavely.app.link"
            page.wait_for_selector('text=mavely.app.link', timeout=45000)
            
            mavely_link = page.locator('text=mavely.app.link').first.inner_text()
            print(f"¡Éxito! Link: {mavely_link}")

            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "success",
                "mavely_link": mavely_link,
                "row_id": row_id
            })

        except Exception as e:
            print(f"Error: {e}")
            # Guardamos lo que el bot veía para diagnosticar (esto lo verás en los logs de GH)
            print("HTML de la página en el momento del error:")
            # print(page.content()[:1000]) # Solo los primeros 1000 caracteres para no saturar
            requests.post(MAKE_WEBHOOK_URL, json={"status": "error", "message": str(e), "row_id": row_id})
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        generate_mavely_link(sys.argv[1], sys.argv[2])
