import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import Main
from SqlORM import PostgresDB

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
                company_name=saved_company[0],
                city=saved_company[1],
                industry=saved_company[2],
                cms=saved_company[3],
                language=saved_company[4],
                framework=saved_company[5],
                external_js=saved_company[6],
                social_links=saved_company[7]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save company data")
    
    except Exception as e:
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
            company_name=company[0],
            city=company[1],
            industry=company[2],
            cms=company[3],
            language=company[4],
            framework=company[5],
            external_js=company[6],
            social_links=company[7]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db.close()

