from sqlalchemy import create_engine, Column, String, Integer, Text, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Optional, List, Tuple

Base = declarative_base()


class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    url = Column(String, nullable=False)

    def __repr__(self):
        return f"<Company(name='{self.company_name}', city='{self.city}', industry='{self.industry}')>"


class CompanyData(Base):
    __tablename__ = 'companies_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date_parse = Column(Date, nullable=False)
    cms = Column(String, nullable=True)
    language = Column(String, nullable=True)
    framework = Column(String, nullable=True)
    external_js = Column(Text, nullable=True)
    social_links = Column(Text, nullable=True)

    def __repr__(self):
        return f"<CompanyData(name='{self.date_parse}')>"
    

class PostgresDB:
    def __init__(self, db_name='webanalysis', user='exampleuser', password='examplepwd', 
                 host='localhost', port='5432'):
        """Initialize database connection using SQLAlchemy"""
        # Create connection string
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        
        # Create engine
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Note: Tables are created via Alembic migrations, not here
        # Run 'alembic upgrade head' to apply migrations
        
        # Create a session for backward compatibility
        self.session = self.SessionLocal()
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create(self, table_name: str, columns: List[str]):
        """Создает таблицу с указанными столбцами."""
        # With SQLAlchemy, tables are defined by models
        # This method is kept for backward compatibility but doesn't do much
        # Tables should be created via Alembic migrations
        # Run 'alembic upgrade head' to apply migrations
        pass
    
    def delete(self, table_name: str):
        """Удаляет указанную таблицу."""
        if table_name == 'companies':
            Company.__table__.drop(bind=self.engine, checkfirst=True)
    
    def get(self, table_name: str) -> List[Tuple]:
        """Получает все записи из указанной таблицы."""
        if table_name == 'companies':
            companies = self.session.query(Company).all()
            return [
                (
                    c.company_name,
                    c.city,
                    c.industry,
                    c.cms,
                    c.language,
                    c.framework,
                    c.external_js,
                    c.social_links
                )
                for c in companies
            ]
        return []
    
    def get_company(self, city: str, industry: str, company_name: str) -> Optional[Tuple]:
        """Получает запись о компании из таблицы companies"""
        company = self.session.query(Company).filter(
            Company.city == city,
            Company.industry == industry,
            Company.company_name == company_name
        ).first()
        
        if company:
            # Return tuple with ID first for backward compatibility
            return (
                company.id,
                company.company_name,
                company.city,
                company.industry,
                company.cms,
                company.language,
                company.framework,
                company.external_js,
                company.social_links
            )
        return None
    
    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """Получает компанию по ID (для внутреннего использования)"""
        return self.session.query(Company).filter(Company.id == company_id).first()
    
    def set(self, table_name: str, values: Tuple):
        """Добавляет новую запись в указанную таблицу."""
        if table_name == 'companies':
            company = Company(
                company_name=values[0],
                city=values[1],
                industry=values[2],
                cms=values[3] if len(values) > 3 else None,
                language=values[4] if len(values) > 4 else None,
                framework=values[5] if len(values) > 5 else None,
                external_js=values[6] if len(values) > 6 else None,
                social_links=values[7] if len(values) > 7 else None
            )
            self.session.add(company)
            self.session.commit()
    
    def set_field(self, table_name: str, id: int, name: str, value: str):
        """Обновляет в указанной таблице указанное поле у нужной записи."""
        if table_name == 'companies':
            company = self.session.query(Company).filter(Company.id == id).first()
            if company:
                setattr(company, name, value)
                self.session.commit()
    
    def close(self):
        """Закрывает соединение с базой данных."""
        self.session.close()
        self.engine.dispose()
