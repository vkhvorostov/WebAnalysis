import psycopg2
from psycopg2 import sql


class PostgresDB:
    def __init__(self, db_name, user, password, host='localhost', port='5432'):
        self.connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor()

    def create(self, table_name, columns):
        """Создает таблицу с указанными столбцами."""
        columns_with_types = ', '.join([f"{col} TEXT" for col in columns])
        create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
            sql.Identifier(table_name),
            sql.SQL(columns_with_types)
        )
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def delete(self, table_name):
        """Удаляет указанную таблицу."""
        delete_table_query = sql.SQL("DROP TABLE IF EXISTS {};").format(
            sql.Identifier(table_name)
        )
        self.cursor.execute(delete_table_query)
        self.connection.commit()

    def get(self, table_name):
        """Получает все записи из указанной таблицы."""
        select_query = sql.SQL("SELECT * FROM {};").format(sql.Identifier(table_name))
        self.cursor.execute(select_query)
        return self.cursor.fetchall()

    def set(self, table_name, values):
        """Добавляет новую запись в указанную таблицу."""
        placeholders = ', '.join(['%s'] * len(values))
        fields = ('company_name', 'city', 'industry', 'cms', 'language', 'framework', 'external_js', 'social_links')
        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({});").format(
            sql.Identifier(table_name),
            sql.SQL(', '.join(fields)),
            sql.SQL(placeholders)
        )
        self.cursor.execute(insert_query, values)
        self.connection.commit()

    def close(self):
        """Закрывает соединение с базой данных."""
        self.cursor.close()
        self.connection.close()
