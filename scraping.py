#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapea todos los eventos publicados en https://www.diadelospatrimonios.cl/
y genera un CSV (dia_patrimonios_events.csv) con columnas:

    titulo | url | pagina

Requisitos:
    pip install selenium pandas

Descarga ChromeDriver compatible con tu versión de Chrome
y ponlo en el PATH o en la misma carpeta del script.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time


def crear_driver() -> webdriver.Chrome:
    chrome_opts = Options()
    chrome_opts.add_argument("--start-maximized")
    chrome_opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    # chrome_opts.add_argument("--headless=new")   #  ⬅️  descomenta si quieres modo headless
    return webdriver.Chrome(options=chrome_opts)


def esperar_resultados(driver: webdriver.Chrome) -> None:
    """Espera a que aparezca al menos un artículo en el contenedor de resultados."""
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#resultados-actividades article.node--type-actividad")
        )
    )


def scrapear_pagina(driver: webdriver.Chrome, pagina: int) -> list[dict]:
    """Devuelve una lista de dicts con título y URL de la página actual."""
    eventos = []

    # obtener todas las tarjetas
    tarjetas = driver.find_elements(
        By.CSS_SELECTOR, "#resultados-actividades article.node--type-actividad"
    )

    for card in tarjetas:
        enlace = card.find_element(By.CSS_SELECTOR, "h2.title a")
        eventos.append(
            {   "pagina": pagina,
                "titulo": enlace.text.strip(),
                "url": enlace.get_attribute("href"),
            }
        )

    print(f"Página {pagina:>3}: capturados {len(tarjetas)} eventos")
    return eventos


def ir_a_siguiente_pagina(driver: webdriver.Chrome) -> bool:
    """
    Hace clic en el número de página siguiente.
    Devuelve True si había siguiente; False si ya estamos en la última.
    """
    try:
        next_link = driver.find_element(
            By.CSS_SELECTOR, ".paginationjs-page.active + .paginationjs-page a"
        )
    except NoSuchElementException:
        return False  # fin del paginado

    # Por si el paginador quedó fuera de la vista
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'})", next_link
    )

    # Elemento de referencia para detectar que el DOM cambió
    primer_articulo = driver.find_element(
        By.CSS_SELECTOR, "#resultados-actividades article.node--type-actividad"
    )

    next_link.click()

    # Esperar a que el artículo viejo desaparezca
    WebDriverWait(driver, 10).until(EC.staleness_of(primer_articulo))
    return True


def main():
    driver = crear_driver()
    eventos = []

    try:
        driver.get("https://www.diadelospatrimonios.cl/")

        # Hacer clic en “Buscar” para cargar el listado
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit-search-form"))
        ).click()

        esperar_resultados(driver)

        pagina = 1
        while True:
            eventos.extend(scrapear_pagina(driver, pagina))
            if not ir_a_siguiente_pagina(driver):
                break
            pagina += 1
            # Pequeña pausa opcional para no saturar el servidor
            time.sleep(0.5)

    except TimeoutException:
        print("⏰ Timeout esperando contenido.")
    finally:
        driver.quit()

    # Guardar CSV
    pd.DataFrame(eventos).to_csv(
        "dia_patrimonios_events.csv", index=False, encoding="utf-8-sig"
    )
    print(f"\n🎉 Listo: {len(eventos)} eventos guardados en dia_patrimonios_events.csv")


if __name__ == "__main__":
    main()
