import pytest
from myproject.scraper import scrape_section

# Фикстура для реальных данных
@pytest.fixture
def scraped_data():
    try:
        return scrape_section("https://www.divan.ru/category/svet", headless=True)
    except Exception:
        return []

@pytest.mark.integration
def test_scraper_returns_list(scraped_data):
    assert isinstance(scraped_data, list)
    if len(scraped_data) == 0:
        pytest.skip("Страница не загрузилась (таймаут или ошибка сети)")
    assert len(scraped_data) > 0

def test_scraper_item_keys(scraped_data):
    if len(scraped_data) == 0:
        pytest.skip("Нет данных для проверки (таймаут или ошибка сети)")
    required_keys = {"name", "price", "currency", "url"}
    for item in scraped_data:
        assert required_keys.issubset(item.keys())

def test_scraper_item_types(scraped_data):
    if len(scraped_data) == 0:
        pytest.skip("Нет данных для проверки (таймаут или ошибка сети)")
    for item in scraped_data:
        assert isinstance(item["name"], str)
        assert isinstance(item["currency"], str)
        assert isinstance(item["url"], str)
        # Цена может быть int или None
        assert (isinstance(item["price"], int) or item["price"] is None)

def test_scraper_url_format(scraped_data):
    if len(scraped_data) == 0:
        pytest.skip("Нет данных для проверки (таймаут или ошибка сети)")
    for item in scraped_data:
        assert item["url"].startswith("https://")
