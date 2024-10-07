import os
import json
from pathlib import Path
from difflib import SequenceMatcher


diffNumbers = []

def get_directory_paths(city, company_name):
    base_path = Path("ParsedData") / city / company_name
    if not base_path.exists():
        print(f"Папка для компании '{company_name}' в городе '{city}' не найдена.")
        return None
    return list(base_path.glob("*/"))  # Возвращает все папки с датами


def compare_files(file1, file2):
    if not file1.exists() or not file2.exists():
        return None, None  # Один из файлов отсутствует

    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        content1 = f1.read()
        content2 = f2.read()

    similarity = SequenceMatcher(None, content1, content2).ratio() * 100
    return content1, similarity


def compare_json(json_file1, json_file2):
    if not json_file1.exists() or not json_file2.exists():
        return None, None  # Один из JSON-файлов отсутствует

    with open(json_file1, 'r', encoding='utf-8') as f1, open(json_file2, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    differences = {}
    for key in data1.keys() | data2.keys():
        if data1.get(key) != data2.get(key):
            differences[key] = (data1.get(key), data2.get(key))

    total_keys = len(data1.keys()) + len(data2.keys())
    # Если оба файла пустые, различий нет
    if total_keys == 0:
        return {}, 0.0

    # Если нет различий, возвращаем 0%
    if not differences:
        return {}, 0.0

    difference_percentage = (len(differences) / total_keys) * 100
    return differences, difference_percentage


def colorize(text, color):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "reset": "\033[0m"
    }
    return f"{colors[color]}{text}{colors['reset']}"


def main():
    while True:
        city = input("Введите город: ")
        company_name = input("Введите название компании: ")

        date_folders = get_directory_paths(city, company_name)
        if date_folders is None:
            continue  # Возвращаемся к началу, если папка не найдена

        print("Выберите папку для сравнения:")
        for idx, folder in enumerate(date_folders):
            print(f"{idx + 1}. {folder.name}")

        choice1 = int(input("Выберите номер первой папки: ")) - 1
        choice2 = int(input("Выберите номер второй папки: ")) - 1

        folder1 = date_folders[choice1]
        folder2 = date_folders[choice2]

        # Путь к папке code
        code_folder1 = folder1 / "code"
        code_folder2 = folder2 / "code"

        # Сравнение HTML файлов
        html_file1 = code_folder1 / f"{company_name}.html"
        html_file2 = code_folder2 / f"{company_name}.html"
        html_content, html_similarity = compare_files(html_file1, html_file2)

        # Сравнение JSON файлов
        json_file1 = folder1 / f"{company_name}.json"
        json_file2 = folder2 / f"{company_name}.json"
        json_diff, json_difference_percentage = compare_files(json_file1, json_file2)

        # Сравнение JS и CSS файлов
        js_files1 = list(code_folder1.glob("js/*.js"))
        js_files2 = list(code_folder2.glob("js/*.js"))
        css_files1 = list(code_folder1.glob("css/*.css"))
        css_files2 = list(code_folder2.glob("css/*.css"))

        # Вывод результатов сравнения
        print("\nСравнение файлов:")

        # HTML
        if html_content is None:
            print(colorize(f"HTML файл отсутствует в одной из папок.", "red"))
            html_similarity = 0  # Присваиваем 0, чтобы избежать ошибок при расчете общего процента
        else:
            if html_similarity == 100:
                print(colorize(f"HTML файл {company_name}.html присутствует в обеих папках и полностью идентичен.",
                               "green"))
            else:
                print(
                    f"HTML файл {company_name}.html присутствует в обеих папках и отличается на {100-html_similarity:.2f}%.")

        diffNumbers.append(100 - html_similarity)

        # JSON
        if json_diff is None:
            print(colorize(f"JSON файл отсутствует в одной из папок.", "red"))
            json_difference_percentage = 0
        else:
            if json_difference_percentage == 100:
                print(colorize(f"JSON файл присутствует в обеих папках и полностью идентичен.", "green"))
            else:
                print(f"Процент различия в JSON файлах: {100 - json_difference_percentage:.2f}%.")

        diffNumbers.append(100 - json_difference_percentage)

        # Сравнение JS файлов
        for js_file in js_files1:
            js_file2 = code_folder2 / "js" / js_file.name
            js_content, js_similarity = compare_files(js_file, js_file2)
            if js_content is None:
                print(colorize(f"JS файл {js_file.name} отсутствует в одной из папок.", "red"))

                diffNumbers.append(100)
            else:
                if js_similarity == 100:
                    print(
                        colorize(f"JS файл {js_file.name} присутствует в обеих папках и полностью идентичен.", "green"))
                else:
                    print(f"JS файл {js_file.name} присутствует в обеих папках и отличается на {100-js_similarity:.2f}%.")

                diffNumbers.append(100 - js_similarity)

        # Сравнение CSS файлов
        for css_file in css_files1:
            css_file2 = code_folder2 / "css" / css_file.name
            css_content, css_similarity = compare_files(css_file, css_file2)
            if css_content is None:
                print(colorize(f"CSS файл {css_file.name} отсутствует в одной из папок.", "red"))

                diffNumbers.append(100)
            else:
                if css_similarity == 100:
                    print(colorize(f"CSS файл {css_file.name} присутствует в обеих папках и полностью идентичен.",
                                   "green"))
                else:
                    print(
                        f"CSS файл {css_file.name} присутствует в обеих папках и отличается на {100-css_similarity:.2f}%.")

                diffNumbers.append(100 - css_similarity)

        # Итоговый вывод
        total_difference = sum(diffNumbers) / len(diffNumbers)
        print(f"Общий процент различия файлов в папках: {total_difference:.2f}%.")


if __name__ == "__main__":
    main()