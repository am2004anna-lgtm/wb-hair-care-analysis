import random
import time
import re

import requests

nm_id = 77408601  # артикул товара

url = "https://search.wb.ru/exactmatch/ru/common/v13/search"
params = {
    "appType": 1,
    "curr": "rub",
    "dest": -1257786,
    "query": str(nm_id),
    "resultset": "catalog",
    "sort": "popular",
    "spp": 30,
    "suppressSpellcheck": "false",
}

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.wildberries.ru/",
}

response = None
for attempt in range(1, 6):
    response = requests.get(url, params=params, headers=headers, timeout=20)
    print(f"Попытка {attempt}: статус {response.status_code}")

    if response.status_code != 429:
        break

    # При 429 делаем паузу перед следующим запросом.
    wait_seconds = random.uniform(2.0, 5.0)
    print(f"WB вернул 429, ждем {wait_seconds:.1f} сек...")
    time.sleep(wait_seconds)

print(f"Статус ответа: {response.status_code}")

def print_product(name, brand, price, rating, reviews):
    print("=" * 50)
    print(f"Товар: {name}")
    print(f"Бренд: {brand}")
    print(f"Цена: {price} руб.")
    print(f"Рейтинг: {rating}")
    print(f"Отзывов: {reviews}")
    print("=" * 50)


def parse_product_from_html(text):
    # На странице WB часто есть JSON с данными товара.
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', text)
    brand_match = re.search(r'"brand"\s*:\s*"([^"]+)"', text)
    price_match = re.search(r'"price"\s*:\s*"?(\d+)"?', text)
    rating_match = re.search(r'"rating"\s*:\s*([0-9.]+)', text)
    reviews_match = re.search(r'"feedbacks"\s*:\s*(\d+)', text)

    name = name_match.group(1) if name_match else "Нет названия"
    brand = brand_match.group(1) if brand_match else "Нет бренда"
    price = int(price_match.group(1)) if price_match else 0
    rating = float(rating_match.group(1)) if rating_match else 0
    reviews = int(reviews_match.group(1)) if reviews_match else 0
    return name, brand, price, rating, reviews


if response.status_code == 200:
    data = response.json()
    products = data.get("data", {}).get("products", [])

    if products:
        product = products[0]
        name = product.get("name", "Нет названия")
        brand = product.get("brand", "Нет бренда")
        price = product.get("salePriceU", 0) / 100
        rating = product.get("rating", 0)
        reviews = product.get("feedbacks", 0)
        print_product(name, brand, price, rating, reviews)
    else:
        print("API не вернул товар. Пробуем получить данные со страницы WB...")
        detail_url = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"
        html_resp = requests.get(detail_url, headers=headers, timeout=20)

        if html_resp.status_code == 200:
            name, brand, price, rating, reviews = parse_product_from_html(html_resp.text)
            print_product(name, brand, price, rating, reviews)
        else:
            print(f"Не удалось открыть страницу товара. Код: {html_resp.status_code}")
else:
    print(f"Ошибка: {response.status_code}")
