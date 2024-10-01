from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def take_screenshot(url, save_path):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')  # Для работы без открытия окна браузера
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.set_window_size(1280, 800)
    driver.get(url)
    driver.save_screenshot(str(save_path))  # Преобразуем в строку путь для сохранения
    driver.quit()