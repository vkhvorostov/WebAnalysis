import requests
import HtmlParser
import DeepCodeAnalyser
import JSAnalyser
import ScreenshotMaker
import SimpleSaver
from SqlORM import PostgresDB


def main():
    db = PostgresDB(db_name='webanalysis', user='exampleuser', password='examplepwd')

    city = 'Новосибирск'  # input("Введите город: ")
    industry = 'Медицинский центр'
    company_name = input("Введите название компании: ")
    url = input("Введите URL сайта компании: ")

    # Создаём иерархию папок для сохранения ресурсов и HTML
    save_dir = SimpleSaver.create_save_directory(city, company_name)
    screenshot_save_path = save_dir / f"{company_name}_screenshot.png"

    html = SimpleSaver.get_html(company_name, save_dir)
    if not html:
        # Получаем HTML код страницы и связанные ресурсы
        html = HtmlParser.get_html_and_resources(url, save_dir / "code")
        if not html:
            print(f"Не удалось получить HTML для {company_name}.")
            return
        # Делаем скриншот главной страницы
        ScreenshotMaker.take_screenshot(url, screenshot_save_path)

    # Анализируем страницу
    cms = DeepCodeAnalyser.detect_cms(html)
    language = DeepCodeAnalyser.detect_language(requests.get(url).headers)
    framework = DeepCodeAnalyser.detect_framework(requests.get(url).headers)
    external_js = JSAnalyser.find_external_js(html)
    social_links = JSAnalyser.find_social_links(html)

    # Сохраняем данные через модуль SimpleSaver
    SimpleSaver.save_parsing_results(
        save_dir=save_dir,
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

    db.set("companies", (company_name, city, industry, cms, language, framework, external_js, social_links))


if __name__ == "__main__":
    main()
