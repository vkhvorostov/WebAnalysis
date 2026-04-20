import os
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
import Main
from SqlORM import Company, CompanyData, PostgresDB

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
    domain_created: Optional[date] = None


class AnalyzeBatchRequest(BaseModel):
    """`parse_date` is accepted in JSON as `date` (alias)."""

    model_config = ConfigDict(populate_by_name=True)

    ids: Optional[List[int]] = Field(default=None, description="Restrict to these company IDs")
    cities: Optional[List[str]] = Field(default=None, description="Restrict to these cities")
    industries: Optional[List[str]] = Field(
        default=None, description="Restrict to these industries"
    )
    parse_date: Optional[date] = Field(
        default=None,
        alias="date",
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
                c,
                parse_date=body.parse_date,
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
            domain_created=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies", response_model=List[CompanyResponse])
async def get_companies():
    """
    Get all companies with fields from latest companies_data by date_parse.
    """
    try:
        companies = db.session.query(Company).order_by(Company.id).all()
        response: List[CompanyResponse] = []
        for company in companies:
            latest_data = (
                db.session.query(CompanyData)
                .filter(CompanyData.company_id == company.id)
                .order_by(CompanyData.date_parse.desc(), CompanyData.id.desc())
                .first()
            )
            response.append(
                CompanyResponse(
                    company_name=company.company_name,
                    city=company.city,
                    industry=company.industry,
                    cms=latest_data.cms if latest_data else None,
                    language=latest_data.language if latest_data else None,
                    framework=latest_data.framework if latest_data else None,
                    external_js=latest_data.external_js if latest_data else None,
                    social_links=latest_data.social_links if latest_data else None,
                    domain_created=latest_data.domain_created
                    if latest_data
                    else None,
                )
            )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/companies/{city}/{industry}/{company_name}", response_model=CompanyResponse)
async def get_company(city: str, industry: str, company_name: str):
    """
    Get a specific company by city, industry, and company name
    """
    try:
        company = (
            db.session.query(Company)
            .filter(
                Company.city == city,
                Company.industry == industry,
                Company.company_name == company_name,
            )
            .first()
        )
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_name} not found"
            )
        latest_data = (
            db.session.query(CompanyData)
            .filter(CompanyData.company_id == company.id)
            .order_by(CompanyData.date_parse.desc(), CompanyData.id.desc())
            .first()
        )
        return CompanyResponse(
            company_name=company.company_name,
            city=company.city,
            industry=company.industry,
            cms=latest_data.cms if latest_data else None,
            language=latest_data.language if latest_data else None,
            framework=latest_data.framework if latest_data else None,
            external_js=latest_data.external_js if latest_data else None,
            social_links=latest_data.social_links if latest_data else None,
            domain_created=latest_data.domain_created if latest_data else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db.close()

