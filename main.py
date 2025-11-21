# main.py - FastAPI application with all endpoints

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from database import get_db, SessionLocal, User, Document, Analysis
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    DocumentCreate, DocumentResponse,
    AnalysisCreate, AnalysisResponse
)
from auth import (
    hash_password, verify_password,
    create_token_response, get_current_user
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Document Analyzer API",
    description="Backend API for document analysis with AI",
    version="1.0.0"
)

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API is running"""
    return {
        "message": "AI Document Analyzer API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/auth/signup", response_model=Token, tags=["Authentication"])
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account
    
    - **username**: unique username (3-50 chars)
    - **email**: valid email address
    - **password**: min 8 characters
    """
    logger.info(f"Signup attempt for user: {user.username}")
    
    # Check if user exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        logger.warning(f"Signup failed: username {user.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        logger.warning(f"Signup failed: email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User {user.username} created successfully")
    
    # Return token
    return create_token_response(user.username)


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Login with username and password
    
    Returns JWT token
    """
    logger.info(f"Login attempt for user: {user.username}")
    
    # Find user
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        logger.warning(f"Login failed: user {user.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(user.password, db_user.hashed_password):
        logger.warning(f"Login failed: invalid password for {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    logger.info(f"User {user.username} logged in successfully")
    
    # Return token
    return create_token_response(user.username)


# ============================================
# DOCUMENT ENDPOINTS
# ============================================

@app.post("/documents/upload", response_model=DocumentResponse, tags=["Documents"])
async def upload_document(
    document: DocumentCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new document
    
    - **filename**: name of document
    - **file_type**: pdf, txt, docx, etc
    - **content**: document text content
    """
    logger.info(f"Document upload by {current_user['username']}: {document.filename}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create document
    db_document = Document(
        user_id=user.id,
        filename=document.filename,
        file_type=document.file_type,
        content=document.content,
        file_size=len(document.content),
        status="uploaded"
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    logger.info(f"Document {document.filename} uploaded successfully")
    
    return db_document


@app.get("/documents", tags=["Documents"])
async def list_documents(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    Get all documents for current user
    
    - **skip**: number of documents to skip (pagination)
    - **limit**: max documents to return
    """
    logger.info(f"Listing documents for {current_user['username']}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get documents
    documents = db.query(Document).filter(
        Document.user_id == user.id
    ).offset(skip).limit(limit).all()
    
    return {
        "documents": documents,
        "total": len(documents),
        "skip": skip,
        "limit": limit
    }


@app.get("/documents/{document_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(
    document_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific document details
    
    - **document_id**: ID of document to retrieve
    """
    logger.info(f"Getting document {document_id} for {current_user['username']}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


# ============================================
# ANALYSIS ENDPOINTS
# ============================================

@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def start_analysis(
    analysis: AnalysisCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start AI analysis on a document
    
    - **document_id**: ID of document to analyze
    - **analysis_type**: summary, extraction, classification
    """
    logger.info(f"Analysis request by {current_user['username']}: type={analysis.analysis_type}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check document exists and belongs to user
    document = db.query(Document).filter(
        Document.id == analysis.document_id,
        Document.user_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create analysis record
    db_analysis = Analysis(
        user_id=user.id,
        document_id=document.id,
        analysis_type=analysis.analysis_type,
        status="pending"  # Will be "processing" when AI starts
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    logger.info(f"Analysis {db_analysis.id} created")
    
    return db_analysis


@app.get("/results/{analysis_id}", response_model=AnalysisResponse, tags=["Analysis"])
async def get_analysis_result(
    analysis_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis results
    
    - **analysis_id**: ID of analysis to retrieve
    """
    logger.info(f"Getting analysis {analysis_id} for {current_user['username']}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get analysis
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis


@app.get("/results", tags=["Analysis"])
async def list_analyses(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    Get all analyses for current user
    
    - **skip**: number of analyses to skip (pagination)
    - **limit**: max analyses to return
    """
    logger.info(f"Listing analyses for {current_user['username']}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get analyses
    analyses = db.query(Analysis).filter(
        Analysis.user_id == user.id
    ).offset(skip).limit(limit).all()
    
    return {
        "analyses": analyses,
        "total": len(analyses)
    }


# ============================================
# ERROR HANDLING
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
