import time
import csv
import uuid
from urllib.parse import unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.headless = True
options.add_argument('--ignore-certificate-errors')
options.add_argument('--disable-web-security')

service = Service(ChromeDriverManager().install())

BASE_URL = "https://www.bonanza.com/booths/browse_categories"
CATEGORY_QUANTITY = 3
PRODUCT_QUANTITY = 5
category_links = []
items = []

# Відкриваємо драйвер для вилучення категорій
driver = webdriver.Chrome(service=service, options=options)
driver.get(BASE_URL)
time.sleep(1)

try:
    # Знаходження елементів із класом link_to_search всередині sub_category_list
    category_elements = driver.find_elements(By.CSS_SELECTOR, '.sub_category_list .link_to_search')

    # Вилучення перших кількох посилань
    links = [element.get_attribute('href') for element in category_elements[:CATEGORY_QUANTITY]]

    # Декодування URL
    decoded_links = [unquote(link) for link in links]
    category_links.extend(decoded_links)  # Використовуємо extend, щоб додати елементи без вкладення списку
    time.sleep(1)  # Очікування для завантаження сторінки

finally:
    driver.quit()

# Обробка кожного посилання по черзі
for link in category_links:
    # Оновлення драйвера для відкриття посилань
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(link)
    time.sleep(1)  # Очікування для завантаження сторінки

    try:
        # Проверка наличия элементов
        elements = driver.find_elements(By.CLASS_NAME, 'results_title')
        descriptions = driver.find_elements(By.CLASS_NAME, 'results_description_snippet')

        for element, description_element in zip(elements[:PRODUCT_QUANTITY], descriptions[:PRODUCT_QUANTITY]):
            link_element = element.find_element(By.TAG_NAME, 'a')
            product_link = link_element.get_attribute('href')
            name = link_element.text
            description = description_element.text
            items.append((product_link, name, description))
        print(f"Opened: {name}")

    finally:
        driver.quit()

# Второй этап: получение подробной информации о каждом продукте
detailed_items = []
for product_link, name, description in items:
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(product_link)
    time.sleep(1)

    try:
        price_element = driver.find_element(By.CSS_SELECTOR, '.item_price')
        price = price_element.text
        # Найти все элементы с селектором p.extended_info_value_content
        item_number_elements = driver.find_elements(By.CSS_SELECTOR, 'p.extended_info_value_content')
        item_number = item_number_elements[-1].text.strip()  # Последний элемент
        quantity_available = item_number_elements[1].text.strip()  # Второй элемент
        condition = item_number_elements[2].text.strip()  # Третий элемент

        # Найти элемент с изображением и извлечь URL
        image_element = driver.find_element(By.CSS_SELECTOR, 'img[onerror^="BONZ.handleBrokenImage"]')
        image_url = image_element.get_attribute('src')

    except Exception as e:
        price = "N/A"
        item_number = "N/A"
        quantity_available = "N/A"
        condition = "N/A"
        image_url = "N/A"
        print(f"Failed to extract product item for {product_link}: {e}")

    unique_key = str(uuid.uuid4())
    detailed_items.append(
        (name, description, price, image_url, product_link, unique_key, item_number, quantity_available, condition))
    driver.close()

# Сохранение данных в CSV
csv_file = "out.csv"
try:
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Product Name", "Product Description", "Price", "Image URL", "Product Link", "Unique Key", "Item Number",
             "Quantity Available", "Condition"])
        for product_data in detailed_items:
            writer.writerow(product_data)
    print(f"Product data have been written to {csv_file}")
except Exception as e:
    print(f"Failed to write to CSV file: {e}")
