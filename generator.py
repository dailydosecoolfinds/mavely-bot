import os
import time
import requests
import sys
from playwright.sync_api import sync_playwright

def generate_mavely_link(product_url, row_id):
    # --- CONFIGURACIÓN ---
    # PEGA AQUÍ TU URL DE WEBHOOK DE MAKE (ESCENARIO DE RETORNO)
    MAKE_WEBHOOK_URL = "https://hook.us1.make.com/tu_codigo_aqui"
    
    # Credenciales desde variables de entorno (GitHub Secrets)
    email = os.environ.get('MAVELY_EMAIL')
    password = os.environ.get('MAVELY_PASSWORD')

    if not email or not password:
        print("Error: No se encontraron las credenciales MAVELY_EMAIL o MAVELY_PASSWORD")
        return

    with sync_playwright() as p:
        # Lanzamos el navegador
        browser = p.chromium.launch(headless=True) # Cambia a False si quieres ver qué pasa (solo local)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            print(f"Iniciando proceso para la fila {row_id}...")
            
            # 1. Login
            page.goto("https://admin.joinmavely.com/login", wait_until="networkidle")
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            
            # Esperamos a que entre al dashboard (ajustado para ser flexible)
            page.wait_for_url("**/dashboard**", timeout=60000)
            print("Login exitoso.")

            # 2. Ir directo al generador de links
            page.goto("https://admin.joinmavely.com/links", wait_until="networkidle")
            
            # 3. Pegar la URL del producto
            # Buscamos el input del generador por el placeholder común
            input_selector = 'input[placeholder*="Paste"], input[placeholder*="URL"]'
            page.wait_for_selector(input_selector)
            page.fill(input_selector, product_url)
            
            # Presionamos Enter para generar
            page.keyboard.press("Enter")
            print(f"Generando link para: {product_url}")
            
            # Esperamos a que el link de mavely aparezca en pantalla
            # Mavely suele mostrar los resultados en un área de texto o input nuevo
            time.sleep(5) 
            
            # Intentamos localizar el link generado que siempre empieza con mavely.app.link
            # Usamos un selector de texto para encontrar el enlace corto
            generated_link_element = page.locator('text=mavely.app.link').first
            mavely_link = generated_link_element.inner_text()

            print(f"Link creado: {mavely_link}")

            # 4. ENVIAR RESULTADO A MAKE
            payload = {
                "status": "success",
                "mavely_link": mavely_link,
                "row_id": row_id,
                "original_url": product_url
            }
            response = requests.post(MAKE_WEBHOOK_URL, json=payload)
            print(f"Notificación enviada a Make. Status: {response.status_code}")

        except Exception as e:
            error_msg = str(e)
            print(f"Error durante el proceso: {error_msg}")
            # Avisamos a Make que hubo un error para que no se quede esperando
            requests.post(MAKE_WEBHOOK_URL, json={
                "status": "error", 
                "message": error_msg, 
                "row_id": row_id
            })
        
        finally:
            browser.close()

if __name__ == "__main__":
    # Verificamos que se pasen los argumentos necesarios
    if len(sys.argv) < 3:
        print("Uso: python generator.py <product_url> <row_id>")
    else:
        url_arg = sys.argv[1]
        row_id_arg = sys.argv[2]
        generate_mavely_link(url_arg, row_id_arg)
