import csv
import time
import uuid
from urllib.parse import unquote
from loguru import logger


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

logger.add("logs_info.log", level="INFO", format="{time} - {level} - {message}")


def initialize_driver():
    """
    Initialize a headless Chrome WebDriver with specified options.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.
    """
    options = Options()
    options.headless = True
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-web-security')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def get_category_links(driver, base_url, category_quantity):
    """
    Retrieve category links from the base URL.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        base_url (str): The URL to retrieve category links from.
        category_quantity (int): The number of category links to retrieve.

    Returns:
        list: A list of decoded category URLs.
    """
    driver.get(base_url)
    time.sleep(1)
    category_elements = driver.find_elements(By.CSS_SELECTOR, '.sub_category_list .link_to_search')
    links = [element.get_attribute('href') for element in category_elements[:category_quantity]]
    decoded_links = [unquote(link) for link in links]
    return decoded_links


def get_product_links(driver, category_links, product_quantity):
    """
    Retrieve product links from each category link.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        category_links (list): A list of category URLs.
        product_quantity (int): The number of product links to retrieve per category.

    Returns:
        list: A list of tuples containing product link, name, and description.
    """
    items = []
    for link in category_links:
        driver.get(link)
        time.sleep(1)
        elements = driver.find_elements(By.CLASS_NAME, 'results_title')
        descriptions = driver.find_elements(By.CLASS_NAME, 'results_description_snippet')
        for element, description_element in zip(elements[:product_quantity], descriptions[:product_quantity]):
            link_element = element.find_element(By.TAG_NAME, 'a')
            product_link = link_element.get_attribute('href')
            name = link_element.text
            description = description_element.text
            items.append((product_link, name, description))
        logger.info(f"Opened: {name}")
    return items


def get_product_details(driver, items):
    """
    Retrieve detailed information for each product.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        items (list): A list of tuples containing product link, name, and description.

    Returns:
        list: A list of tuples containing detailed product information.
    """
    detailed_items = []
    for product_link, name, description in items:
        driver.get(product_link)
        time.sleep(1)
        try:
            price_element = driver.find_element(By.CSS_SELECTOR, '.item_price')
            price = price_element.text
            item_number_elements = driver.find_elements(By.CSS_SELECTOR, 'p.extended_info_value_content')
            item_number = item_number_elements[-1].text.strip()
            quantity_available = item_number_elements[1].text.strip()
            condition = item_number_elements[2].text.strip()
            image_element = driver.find_element(By.CSS_SELECTOR, 'img[onerror^="BONZ.handleBrokenImage"]')
            image_url = image_element.get_attribute('src')
        except Exception as e:
            price, item_number, quantity_available, condition, image_url = "N/A", "N/A", "N/A", "N/A", "N/A"
            logger.info(f"Failed to extract product item for {product_link}: {e}")

        unique_key = str(uuid.uuid4())
        detailed_items.append(
            (name, description, price, image_url, product_link, unique_key, item_number, quantity_available, condition)
        )
    return detailed_items


def save_to_csv(detailed_items, csv_file):
    """
    Save detailed product information to a CSV file.

    Args:
        detailed_items (list): A list of tuples containing detailed product information.
        csv_file (str): The name of the CSV file to save the data to.
    """
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                ["Product Name", "Product Description", "Price", "Image URL", "Product Link", "Unique Key",
                 "Item Number",
                 "Quantity Available", "Condition"])
            for product_data in detailed_items:
                writer.writerow(product_data)
        logger.info(f"Product data have been written to {csv_file}")
    except Exception as e:
        logger.info(f"Failed to write to CSV file: {e}")


def main():
    """
    Main function to execute the web scraping workflow.
    """
    BASE_URL = "https://www.bonanza.com/booths/browse_categories"
    CATEGORY_QUANTITY = 2
    PRODUCT_QUANTITY = 2
    CSV_FILE = "out.csv"

    driver = initialize_driver()

    try:
        category_links = get_category_links(driver, BASE_URL, CATEGORY_QUANTITY)
    finally:
        driver.quit()

    driver = initialize_driver()
    try:
        items = get_product_links(driver, category_links, PRODUCT_QUANTITY)
    finally:
        driver.quit()

    driver = initialize_driver()
    try:
        detailed_items = get_product_details(driver, items)
    finally:
        driver.quit()

    save_to_csv(detailed_items, CSV_FILE)


if __name__ == "__main__":
    main()
