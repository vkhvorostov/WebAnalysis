import csv
from SqlORM import PostgresDB


def main():
    input_file = 'companies.csv'
    db = PostgresDB(db_name='webanalysis', user='exampleuser', password='examplepwd')
    with open(input_file, 'r', newline='') as in_file:
        csv_reader = csv.DictReader(in_file, delimiter=';')
        for row in csv_reader:
            city = row['city'].strip()
            industry = row['industry'].strip()
            company_name = row['company_name'].strip().replace('/', '-')
            already_saved = db.get_company(city, industry, company_name)
            if already_saved:
                db.set_field("companies", already_saved[0], 'url', row['url'].strip())
    db.close()


if __name__ == "__main__":
    main()
