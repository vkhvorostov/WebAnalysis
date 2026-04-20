import os
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import Main
from SqlORM import Company, PostgresDB

app = FastAPI(
    title="WebAnalysis API",
    description="API for web analysis and company data management",
    version="1.0.0"
)

# Database connection using environment variables
db = PostgresDB(
    db_name=os.getenv('POSTGRES_DB', 'webanalysis'),
    user=os.getenv('POSTGRES_USER', 'exampleuser'),
    password=os.getenv('POSTGRES_PASSWORD', 'examplepwd'),
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5432')
)


class CompanyRequest(BaseModel):
    city: str
    industry: str
    company_name: str
    url: str


class CompanyResponse(BaseModel):
    company_name: str
    city: str
    industry: str
    cms: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    external_js: Optional[str] = None
    social_links: Optional[str] = None


class AnalyzeBatchRequest(BaseModel):
    ids: Optional[List[int]] = Field(default=None, description="Restrict to these company IDs")
    cities: Optional[List[str]] = Field(default=None, description="Restrict to these cities")
    industries: Optional[List[str]] = Field(
        default=None, description="Restrict to these industries"
    )
    date: Optional[date] = Field(
        default=None,
        description="If set, read HTML from ParsedData for this calendar date (dd.mm.yyyy folder); if null, fetch from the internet",
    )


class AnalyzeResultItem(BaseModel):
    id: int
    company_name: str
    city: str
    industry: str
    status: str
    detail: Optional[str] = None


class AnalyzeBatchResponse(BaseModel):
    results: List[AnalyzeResultItem]


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "WebAnalysis API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/companies/analyze", response_model=AnalyzeBatchResponse)
def companies_analyze(body: AnalyzeBatchRequest):
    """
    Run analysis for companies selected by optional filters. Filters are combined with AND.
    If `date` is set, HTML is loaded from ParsedData for that date (no internet fetch).
    If `date` is null, data is collected from the internet (today's parse folder).
    """
    try:
        q = db.session.query(Company)
        if body.ids:
            q = q.filter(Company.id.in_(body.ids))
        if body.cities:
            q = q.filter(Company.city.in_(body.cities))
        if body.industries:
            q = q.filter(Company.industry.in_(body.industries))
        rows = q.order_by(Company.id).all()

        results: List[AnalyzeResultItem] = []
        for c in rows:
            ok, err = Main.process(
                db,
                c.city,
                c.industry,
                c.company_name,
                c.url,
                parse_date=body.date,
            )
            results.append(
                AnalyzeResultItem(
                    id=c.id,
                    company_name=c.company_name,
                    city=c.city,
                    industry=c.industry,
                    status="ok" if ok else "error",
                    detail=err,
                )
            )
        return AnalyzeBatchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/companies", response_model=CompanyResponse, status_code=201)
async def create_company(company: CompanyRequest):
    """
    Insert a new company row (identity and URL only; analysis fields are unset until analyzed).
    """
    name = company.company_name.replace("/", "-")
    try:
        if db.get_company(company.city, company.industry, name):
            raise HTTPException(
                status_code=400,
                detail=f"Company {name} already exists in database",
            )
        row = Company(
            company_name=name,
            city=company.city,
            industry=company.industry,
            url=company.url,
        )
        db.session.add(row)
        db.session.commit()
        db.session.refresh(row)
        return CompanyResponse(
            company_name=row.company_name,
            city=row.city,
            industry=row.industry,
            cms=None,
            language=None,
            framework=None,
            external_js=None,
            social_links=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies", response_model=List[CompanyResponse])
async def get_companies():
    """
    Get all companies from the database
    """
    try:
        companies = db.get("companies")
        return [
            CompanyResponse(
                company_name=company[0],
                city=company[1],
                industry=company[2],
                cms=company[3],
                language=company[4],
                framework=company[5],
                external_js=company[6],
                social_links=company[7]
            )
            for company in companies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies/{city}/{industry}/{company_name}", response_model=CompanyResponse)
async def get_company(city: str, industry: str, company_name: str):
    """
    Get a specific company by city, industry, and company name
    """
    try:
        company = db.get_company(city, industry, company_name)
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_name} not found"
            )
        return CompanyResponse(
            company_name=company[1],  # Index 1 because ID is at index 0
            city=company[2],
            industry=company[3],
            cms=company[4],
            language=company[5],
            framework=company[6],
            external_js=company[7],
            social_links=company[8]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db.close()

