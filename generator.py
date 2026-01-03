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
            print(f"Abriendo Mavely para Fila {row_id}...")
            page.goto("https://creators.joinmavely.com/tools/link-creator", wait_until="networkidle", timeout=60000)
            time.sleep(10)

            # INYECCIÓN JAVASCRIPT: Forzamos el pegado de la URL
            print("Inyectando URL en el sistema...")
            page.evaluate(f"""(url) => {{
                const input = document.querySelector('input[placeholder*="Paste"], input[type="url"], input[type="text"]');
                if (input) {{
                    input.value = url;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }}""", product_url)
            
            time.sleep(2)
            page.keyboard.press("Enter")
            print("Enter presionado. Esperando generación...")

            # Espera agresiva: Mavely tarda unos segundos en mostrar el resultado
            time.sleep(10)

            # Extraemos el link buscando patrones en el texto de toda la página
            mavely_link = page.evaluate("""() => {
                const text = document.body.innerText;
                const match = text.match(/mavely\.app\.link\/[a-zA-Z0-9]+/);
                return match ? 'https://' + match[0] : null;
            }""")

            if not mavely_link:
                # Intento final: buscar el primer enlace que empiece por mavely
                mavely_link = page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('a'));
                    const found = links.find(a => a.href.includes('mavely.app.link'));
                    return found ? found.href : null;
                }""")

            if not mavely_link:
                raise Exception("Mavely no generó el enlace a tiempo.")
            
            print(f"¡Link capturado!: {mavely_link}")

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
