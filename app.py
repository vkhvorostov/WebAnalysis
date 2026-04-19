import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import Main
from SqlORM import PostgresDB, Company

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "WebAnalysis API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/analyze", response_model=CompanyResponse)
async def analyze_company(company: CompanyRequest):
    """
    Analyze a company website and store the results
    """
    try:
        # Check if company already exists
        already_saved = db.get_company(company.city, company.industry, company.company_name)
        if already_saved:
            raise HTTPException(
                status_code=400,
                detail=f"Company {company.company_name} already exists in database"
            )
        
        # Process the company
        Main.process(
            db=db,
            city=company.city,
            industry=company.industry,
            company_name=company.company_name.replace('/', '-'),
            url=company.url
        )
        
        # Get the saved company data
        saved_company = db.get_company(company.city, company.industry, company.company_name.replace('/', '-'))
        if saved_company:
            return CompanyResponse(
                company_name=saved_company[1],  # Index 1 because ID is at index 0
                city=saved_company[2],
                industry=saved_company[3],
                cms=saved_company[4],
                language=saved_company[5],
                framework=saved_company[6],
                external_js=saved_company[7],
                social_links=saved_company[8]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save company data")
    
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

