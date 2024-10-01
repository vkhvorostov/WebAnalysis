import requests
import HtmlParser
import DeepCodeAnalyser
import JSAnalyser
import ScreenshotMaker
import SimpleSaver

def main():
    city = input("Введите город: ")
    company_name = input("Введите название компании: ")
    url = input("Введите URL сайта компании: ")

    # Папка для сохранения ресурсов и HTML
    save_dir = f"ParsedData/{city}/{company_name}"

    # Получаем HTML код страницы и связанные ресурсы
    html = HtmlParser.get_html_and_resources(url, save_dir)
    if not html:
        print(f"Не удалось получить HTML для {company_name}.")
        return

    # Делаем скриншот главной страницы
    screenshot_save_path = f"{company_name}_screenshot.png"
    ScreenshotMaker.take_screenshot(url, screenshot_save_path)

    # Анализируем страницу
    cms = DeepCodeAnalyser.detect_cms(html)
    language = DeepCodeAnalyser.detect_language(requests.get(url).headers)
    framework = DeepCodeAnalyser.detect_framework(requests.get(url).headers)
    external_js = JSAnalyser.find_external_js(html)
    social_links = JSAnalyser.find_social_links(html)

    # Сохраняем данные через модуль SimpleSaver
    SimpleSaver.save_parsing_results(
        city=city,
        company_name=company_name,
        html=html,
        screenshot_data=screenshot_save_path,
        cms=cms,
        language=language,
        framework=framework,
        external_js=external_js,
        social_links=social_links
    )

if __name__ == "__main__":
    main()