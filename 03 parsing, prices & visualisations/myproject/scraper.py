# scraper.py
import time
import re

# Пробуем импортировать undetected-chromedriver
UC_AVAILABLE = False
uc = None
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except (ImportError, ModuleNotFoundError, Exception) as e:
    UC_AVAILABLE = False
    print(f"[debug] undetected-chromedriver недоступен: {e}")

# Всегда импортируем selenium для fallback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException


def scrape():
    """Парсит одну страницу раздела lamp (для теста)."""
    url = "https://www.divan.ru/category/lamp"
    return scrape_section(url, headless=False, timeout=60)


def scrape_all_pages(base_url="https://www.divan.ru/category/svet?sort=0",
                     headless=True, max_pages=5, delay_between_pages=2, scroll_steps=8):
    """Обходит пагинацию, собирает уникальные товары по URL."""
    all_results, seen = [], set()
    
    # Создаем один драйвер для всех страниц (переиспользуем сессию)
    driver = None
    try:
        driver = _init_driver(headless=headless, timeout=60)
        
        # Один раз заходим на главную для установки сессии
        print("[debug] Инициализация сессии на главной странице...")
        try:
            driver.get("https://www.divan.ru/")
            time.sleep(3)
            # Имитируем просмотр
            driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception as e:
            print(f"[warning] Ошибка при инициализации сессии: {e}")
        
        for page in range(max_pages):  # divan.ru: page начинается с 0
            sep = "&" if "?" in base_url else "?"
            url = f"{base_url}{sep}page={page}"
            print(f"[page {page}] {url}")
            
            try:
                # Используем существующий драйвер вместо создания нового
                items = scrape_section_with_driver(driver, url, scroll_steps=scroll_steps)
            except Exception as e:
                print(f"[page {page}] error: {type(e).__name__}: {e}")
                items = []
            
            if not items:
                print(f"[page {page}] пусто — стоп.")
                break
            
            new_items = [it for it in items if it.get("url") and it["url"] not in seen]
            for it in new_items:
                seen.add(it["url"])
            
            print(f"[page {page}] новых: {len(new_items)} (всего: {len(all_results) + len(new_items)})")
            
            if len(new_items) == 0 and page > 0:
                # Если нет новых товаров, возможно пагинация не работает или достигнут конец
                print(f"[page {page}] Нет новых товаров — возможно, пагинация не работает или достигнут конец каталога")
                print(f"[page {page}] Останавливаем парсинг. Собрано уникальных товаров: {len(all_results)}")
                break
            
            all_results.extend(new_items)
            
            # Промежуточное сохранение после каждой страницы (на случай прерывания)
            if all_results:
                try:
                    from myproject import saver
                    saver.save_xlsx(all_results, filename="results_partial.xlsx")
                except Exception as e:
                    print(f"[warning] Не удалось сохранить промежуточные данные: {e}")
            
            if page < max_pages - 1:
                time.sleep(delay_between_pages)
        
    finally:
        # Закрываем драйвер в конце
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    print(f"Итого уникальных: {len(all_results)}")
    return all_results


def _init_driver(headless: bool, timeout: int):
    """Инициализирует драйвер с использованием undetected-chromedriver если доступен."""
    
    # Проверяем доступность undetected-chromedriver
    use_uc = False
    if UC_AVAILABLE:
        try:
            # Пробуем создать объект ChromeOptions для проверки
            test_options = uc.ChromeOptions()
            use_uc = True
        except Exception as e:
            print(f"[debug] undetected-chromedriver недоступен при проверке: {e}")
            use_uc = False
    
    if use_uc:
        # Используем undetected-chromedriver для лучшего обхода защиты
        print("[debug] Используем undetected-chromedriver для обхода защиты")
        try:
            options = uc.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            
            # ВАЖНО: headless режим часто легче обнаруживается защитой
            # Попробуем без headless или с минимальными настройками
            if headless:
                # Используем headless только если явно запрошен, но с дополнительными настройками
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
            else:
                # В видимом режиме добавляем настройки для обхода защиты
                options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Дополнительные настройки для обхода защиты
            options.add_argument("--lang=ru-RU,ru")
            options.add_argument("--disable-infobars")
            
            # Используем временный профиль для сохранения cookies между сессиями
            import tempfile
            import os
            temp_profile = os.path.join(tempfile.gettempdir(), "uc_profile_divan")
            os.makedirs(temp_profile, exist_ok=True)
            options.add_argument(f"--user-data-dir={temp_profile}")
            
            # Создаем драйвер через undetected-chromedriver
            # Используем use_subprocess=True для лучшей работы
            driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
            driver.set_page_load_timeout(timeout)
            return driver
        except Exception as e:
            print(f"[warning] Ошибка при создании undetected-chromedriver: {e}")
            print("[warning] Переключаемся на обычный Selenium")
            import traceback
            print(f"[debug] Traceback: {traceback.format_exc()}")
    # Fallback на обычный Selenium (если UC недоступен)
    if not UC_AVAILABLE or uc is None:
        print("[warning] undetected-chromedriver недоступен, используем обычный Selenium")
        print("[warning] ВНИМАНИЕ: Обычный Selenium может не обойти защиту сайта!")
    
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.page_load_strategy = "normal"
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    
    if ChromeDriverManager:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        # Если webdriver-manager недоступен, используем системный chromedriver
        driver = webdriver.Chrome(options=options)
    
    driver.set_page_load_timeout(timeout)
    return driver


def scrape_section_with_driver(driver, url, timeout=40, scroll_steps=8):
    """Парсит одну страницу используя переданный драйвер (для переиспользования сессии)."""
    return _scrape_section_impl(driver, url, timeout, scroll_steps, close_driver=False)


def scrape_section(url, headless=False, timeout=40, scroll_steps=8):
    """Парсит одну страницу раздела divan.ru и возвращает список товаров."""
    driver = _init_driver(headless=headless, timeout=timeout)
    return _scrape_section_impl(driver, url, timeout, scroll_steps, close_driver=True)


def _scrape_section_impl(driver, url, timeout=40, scroll_steps=8, close_driver=True):
    """Внутренняя реализация парсинга страницы."""
    try:
        # Стратегия обхода: сначала главная страница для установки cookies и сессии
        try:
            # Шаг 1: Заходим на главную страницу и ждем полной загрузки
            print("[debug] Шаг 1: Заходим на главную страницу для установки сессии...")
            try:
                # Используем более длинный таймаут для главной страницы
                driver.set_page_load_timeout(30)
                driver.get("https://www.divan.ru/")
                
                # Ждем загрузки и имитируем человеческое поведение
                time.sleep(5)  # Увеличена задержка
                
                # Ждем полной загрузки страницы
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except:
                    pass
                
                # Имитируем человеческое поведение: прокрутка, паузы
                import random
                scroll_positions = [100, 300, 500, 200, 0]
                for pos in scroll_positions:
                    driver.execute_script(f"window.scrollTo(0, {pos});")
                    time.sleep(random.uniform(0.5, 1.5))  # Случайные задержки
                
                # Возвращаемся наверх
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                
                # Проверяем, что мы не на странице ошибки
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if "err_too_many_redirects" in page_text or "переадресация" in page_text:
                    print("[warning] Обнаружена проблема с редиректами на главной странице")
                    # Пробуем очистить cookies и перезагрузить
                    driver.delete_all_cookies()
                    time.sleep(2)
                    driver.get("https://www.divan.ru/")
                    time.sleep(5)
                
                print("[debug] Главная страница обработана")
                    
            except Exception as e:
                print(f"[warning] Ошибка при загрузке главной страницы: {e}")
                # Продолжаем попытку загрузки целевой страницы
            
            # Шаг 2: Переходим на целевую страницу через клик по ссылке (более естественно)
            print(f"[debug] Шаг 2: Переходим на целевую страницу: {url}")
            time.sleep(3)  # Увеличена пауза между переходами
            
            # Пробуем найти ссылку на категорию и кликнуть по ней (более естественно)
            try:
                # Ищем ссылку на категорию "Свет"
                category_link = driver.find_element(By.XPATH, "//a[contains(@href, '/category/svet')]")
                if category_link:
                    print("[debug] Найдена ссылка на категорию, кликаем...")
                    category_link.click()
                    time.sleep(5)
                else:
                    # Если не нашли ссылку, переходим напрямую
                    driver.get(url)
                    time.sleep(5)
            except:
                # Если не удалось найти ссылку, переходим напрямую
                try:
                    driver.get(url)
                except Exception as e:
                    # Таймаут не критичен, если страница начала загружаться
                    if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                        print(f"[debug] Таймаут при загрузке, но страница может быть загружена, продолжаем...")
                    else:
                        print(f"[warning] Ошибка при загрузке страницы: {e}")
            
            time.sleep(5)  # Увеличено время ожидания
            
        except Exception as e:
            print(f"[warning] Ошибка в процессе загрузки: {e}")
            # Пробуем еще раз после задержки
            time.sleep(3)
            try:
                driver.get(url)
                time.sleep(3)
            except Exception as e2:
                # Даже при ошибке продолжаем - возможно страница загрузилась
                if "timeout" not in str(e2).lower():
                    print(f"[error] Не удалось загрузить страницу: {e2}")
                    return []
        
        # Ждем загрузки body
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            print("[warning] Таймаут при ожидании body, продолжаем...")
        
        # Проверяем, не попали ли мы на страницу ошибки
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            current_url = driver.current_url
            
            if "err_too_many_redirects" in page_text or "переадресация" in page_text or "redirect" in page_text:
                print("[warning] Обнаружена проблема с редиректами")
                # Пробуем использовать JavaScript для навигации
                try:
                    driver.execute_script(f"window.location.href = '{url}';")
                    time.sleep(3)
                except:
                    pass
        except:
            pass
        
        # Дополнительное ожидание для загрузки контента
        time.sleep(3)
        
        # Ждём появления контента (пробуем разные индикаторы загрузки)
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            pass

        # Ленивая загрузка: прокрутка вниз с большими задержками
        last_h = driver.execute_script("return document.body.scrollHeight")
        stable = 0
        for i in range(scroll_steps):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)  # Увеличена задержка
            h = driver.execute_script("return document.body.scrollHeight")
            if h == last_h:
                stable += 1
                if stable >= 3:  # Увеличено количество стабильных проверок
                    break
            else:
                stable = 0
                last_h = h
            # Прокрутка по частям для лучшей загрузки
            driver.execute_script("window.scrollTo(0, arguments[0]);", h // 2)
            time.sleep(0.5)

        # Прокрутка обратно наверх
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # Ждём появления карточек - пробуем разные селекторы с увеличенным временем ожидания
        cards = []
        selectors = [
            'a[href^="/product/"]',  # Основной селектор - работает!
            'a[href*="/product/"]',
            'a[href*="product"]',
            '[data-product-id]',
            '.product-card a',
            'article a[href*="/product/"]',
        ]
        
        # Также пробуем XPath селекторы
        xpath_selectors = [
            '//a[contains(@href, "/product/")]',
            '//a[starts-with(@href, "/product/")]',
        ]
        
        for selector in selectors:
            try:
                found_cards = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                # Фильтруем только ссылки на товары
                found_cards = [c for c in found_cards if c.get_attribute("href") and "/product/" in c.get_attribute("href")]
                if found_cards:
                    cards = found_cards
                    print(f"[cards] найдено {len(cards)} через селектор: {selector}")
                    break
            except TimeoutException:
                continue
            except Exception as e:
                continue
        
        # Если не нашли через CSS, пробуем XPath
        if not cards:
            for xpath in xpath_selectors:
                try:
                    found_cards = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.XPATH, xpath))
                    )
                    # Фильтруем только ссылки на товары
                    found_cards = [c for c in found_cards if c.get_attribute("href") and "/product/" in c.get_attribute("href")]
                    if found_cards:
                        cards = found_cards
                        print(f"[cards] найдено {len(cards)} через XPath селектор")
                        break
                except TimeoutException:
                    continue
                except Exception:
                    continue
        
        # Если не нашли через селекторы, пробуем найти все ссылки и отфильтровать
        if not cards:
            try:
                all_links = driver.find_elements(By.TAG_NAME, "a")
                cards = [link for link in all_links 
                        if link.get_attribute("href") and "/product/" in link.get_attribute("href")]
                if cards:
                    print(f"[cards] найдено {len(cards)} через поиск всех ссылок")
            except Exception:
                pass
        
        if not cards:
            print("[cards] карточки не найдены ни одним селектором")
            # Детальная отладка
            try:
                print(f"[debug] URL страницы: {driver.current_url}")
                print(f"[debug] Заголовок страницы: {driver.title}")
                
                # Проверяем, есть ли вообще контент на странице
                body_text = driver.find_element(By.TAG_NAME, "body").text[:500]
                print(f"[debug] Первые 500 символов текста страницы: {body_text}")
                
                # Проверяем все ссылки на странице
                all_links = driver.find_elements(By.TAG_NAME, "a")
                print(f"[debug] Всего ссылок на странице: {len(all_links)}")
                
                # Показываем примеры ссылок
                sample_hrefs = []
                for link in all_links[:20]:
                    href = link.get_attribute("href")
                    if href:
                        sample_hrefs.append(href)
                print(f"[debug] Примеры ссылок (первые 20): {sample_hrefs[:10]}")
                
                # Проверяем, есть ли элементы с классами, содержащими "product"
                try:
                    product_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'product') or contains(@class, 'Product')]")
                    print(f"[debug] Элементов с классом 'product': {len(product_elements)}")
                    if product_elements:
                        for i, elem in enumerate(product_elements[:3]):
                            print(f"[debug] Элемент {i}: tag={elem.tag_name}, class={elem.get_attribute('class')}")
                except:
                    pass
                
                # Проверяем структуру страницы
                try:
                    main_content = driver.find_elements(By.XPATH, "//main | //div[@role='main'] | //div[contains(@class, 'content')] | //div[contains(@class, 'catalog')]")
                    print(f"[debug] Найдено основных контейнеров: {len(main_content)}")
                except:
                    pass
                    
            except Exception as e:
                print(f"[debug] Ошибка при отладке: {e}")
                import traceback
                print(traceback.format_exc())
            return []

        results = []
        seen_urls = set()
        for c in cards:
            try:
                # URL
                product_url = c.get_attribute("href")
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://www.divan.ru{product_url}"
                if not product_url or product_url in seen_urls:
                    continue
                seen_urls.add(product_url)

                # Определяем контейнер для поиска данных (сама карточка или родитель)
                search_container = c
                containers_to_search = [c]  # Список контейнеров для поиска
                
                try:
                    # Если карточка - это ссылка, пробуем найти родительские контейнеры
                    if c.tag_name == 'a':
                        # Пробуем найти родительские элементы (до 3 уровней вверх)
                        current = c
                        for _ in range(3):
                            try:
                                parent = current.find_element(By.XPATH, './..')
                                if parent:
                                    containers_to_search.append(parent)
                                    current = parent
                            except:
                                break
                except Exception:
                    pass

                # Название (fallback с несколькими вариантами)
                name = ""
                name_selectors = [
                    'div[itemprop="name"]',
                    'div.ProductName',
                    '[class*="ProductName"]',
                    '[class*="product-name"]',
                    '.product-name',
                    '[data-testid="product-name"]',
                    'h2',
                    'h3',
                    'h4',
                    '.name',
                    'span[itemprop="name"]',
                    '[class*="Name"]',
                    '[class*="title"]',
                    '[class*="Title"]',
                ]
                
                # Ищем название во всех контейнерах
                for container in containers_to_search:
                    if name:
                        break
                    # Пробуем селекторы
                    for selector in name_selectors:
                        try:
                            name_elem = container.find_element(By.CSS_SELECTOR, selector)
                            name = name_elem.text.strip()
                            if name and len(name) > 3:  # Минимальная длина названия
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Если не нашли через селекторы, пробуем получить текст из самого контейнера
                    if not name:
                        try:
                            container_text = container.text.strip()
                            # Берем первую строку текста, если она не слишком длинная
                            if container_text and len(container_text) < 200:
                                lines = container_text.split('\n')
                                if lines:
                                    potential_name = lines[0].strip()
                                    if potential_name and len(potential_name) > 3:
                                        name = potential_name
                                        break
                        except:
                            pass
                
                # Если название не найдено, пробуем получить из title, alt или aria-label
                if not name:
                    try:
                        name = (c.get_attribute("title") or 
                               c.get_attribute("alt") or 
                               c.get_attribute("aria-label") or "")
                        if not name:
                            for container in containers_to_search:
                                name = (container.get_attribute("title") or 
                                       container.get_attribute("alt") or 
                                       container.get_attribute("aria-label") or "")
                                if name:
                                    break
                    except:
                        pass

                # Цена (fallback с несколькими вариантами)
                raw_price = None
                price_selectors = [
                    'span[data-testid="price"]',
                    '[data-testid="price"]',
                    'span.FullPrice_actual__Mio07',
                    '[class*="FullPrice"]',
                    '[class*="Price_actual"]',
                    '.price',
                    '.product-price',
                    'span[itemprop="price"]',
                    '[itemprop="price"]',
                    '.actual-price',
                    '[class*="Price"]',
                    '[class*="price"]',
                    '[class*="cost"]',
                    '[class*="Cost"]',
                    'span[class*="rub"]',
                    '[class*="rub"]',
                ]
                
                # Ищем цену во всех контейнерах
                for container in containers_to_search:
                    if raw_price:
                        break
                    # Пробуем селекторы
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            raw_price = price_elem.text.strip()
                            if raw_price and any(char.isdigit() for char in raw_price):
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Если не нашли через селекторы, ищем числа в тексте контейнера
                    if not raw_price:
                        try:
                            container_text = container.text
                            # Ищем паттерны цен (числа с пробелами или без)
                            price_patterns = re.findall(r'[\d\s]+[₽руб]|[\d\s]+руб|[\d\s]+₽|\d{1,3}(?:\s?\d{3})*(?:\s?[₽руб])?', container_text)
                            if price_patterns:
                                raw_price = price_patterns[0].strip()
                        except:
                            pass
                
                # Пробуем получить цену из data-атрибутов
                if not raw_price:
                    try:
                        for container in containers_to_search:
                            raw_price = (container.get_attribute("data-price") or 
                                        container.get_attribute("data-cost") or None)
                            if raw_price:
                                break
                    except:
                        pass
                
                price = _parse_price(raw_price) if raw_price else None

                results.append({
                    "name": name,
                    "price": price,
                    "currency": "RUB",
                    "url": product_url
                })
            except Exception as e:
                print(f"[error] Ошибка при парсинге товара: {type(e).__name__}: {e}")
                import traceback
                print(f"[error] Traceback: {traceback.format_exc()}")

        print(f"[items] спарсено: {len(results)}")
        return results

    except TimeoutException as e:
        print(f"[timeout] {e}")
        return []
    except WebDriverException as e:
        print(f"[webdriver] {e}")
        return []
    finally:
        try:
            driver.quit()
        except (WebDriverException, OSError, Exception):
            # Игнорируем ошибки при закрытии (известная проблема с undetected-chromedriver)
            try:
                driver.close()
            except:
                pass


def _parse_price(text: str):
    """Возвращает числовую цену в рублях из текста; иначе None."""
    if not text or text == "нет данных":
        return None
    digits = re.findall(r"\d+", text.replace("\xa0", " "))
    if not digits:
        return None
    try:
        return int("".join(digits))
    except ValueError:
        return None
