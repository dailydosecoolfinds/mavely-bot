import os
import time
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url):
    with sync_playwright() as p:
        # Iniciamos el navegador
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        page.goto("https://admin.joinmavely.com/login")
        page.fill('input[type="email"]', os.environ['MAVELY_EMAIL'])
        page.fill('input[type="password"]', os.environ['MAVELY_PASSWORD'])
        page.click('button[type="submit"]')
        
        # Esperar a que cargue el dashboard
        page.wait_for_url("**/dashboard**")

        # 2. Ir al Creador de Links (SmartLink)
        # Mavely suele tener el input de creación en el dashboard o /links
        page.goto("https://admin.joinmavely.com/links")
        
        # 3. Pegar la URL de Gemini
        input_selector = 'input[placeholder*="Paste"]' # Selector genérico, ajustalo si cambia
        page.wait_for_selector(input_selector)
        page.fill(input_selector, product_url)
        
        # 4. Click en generar y copiar
        page.click('button:has-text("Create"), button:has-text("Generate")')
        time.sleep(3) # Esperar proceso
        
        # Extraer el link generado (mavely.app.link/...)
        result_link = page.inner_text('div.generated-link') # Ajustar según el selector real
        
        print(f"RESULT_LINK={result_link}")
        browser.close()

if __name__ == "__main__":
    import sys
    url = sys.argv[1]
    generate_mavely_link(url)
