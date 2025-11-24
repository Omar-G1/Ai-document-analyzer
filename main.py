# main.py - FastAPI application with Gemini AI integration

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import asyncio

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
from ai_service import analyze_with_gemini, get_supported_analysis_types

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Document Analyzer API",
    description="Backend API for document analysis with Google Gemini AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API is running"""
    return {
        "message": "AI Document Analyzer API",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/analysis-types", tags=["Analysis"])
async def get_analysis_types():
    """Get supported analysis types"""
    return {
        "supported_types": get_supported_analysis_types(),
        "description": {
            "summary": "Generate a concise summary of the document",
            "extraction": "Extract key information, names, dates, numbers",
            "classification": "Classify document type and purpose",
            "sentiment": "Analyze sentiment and tone"
        }
    }


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
    
    Returns JWT token for authentication
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
    
    logger.info(f"✓ User {user.username} created successfully")
    
    # Return token
    return create_token_response(user.username)


@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Login with username and password
    
    Returns JWT token for use in authenticated endpoints
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
    
    logger.info(f"✓ User {user.username} logged in successfully")
    
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
    
    - **filename**: name of document (max 255 chars)
    - **file_type**: pdf, txt, docx, email, etc
    - **content**: document text content (max 10000 chars)
    
    Returns document ID and status
    """
    logger.info(f"Document upload by {current_user['username']}: {document.filename}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        logger.error(f"User not found during upload: {current_user['username']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create document record
    db_document = Document(
        user_id=user.id,
        filename=document.filename,
        file_type=document.file_type or "text",
        content=document.content,
        file_size=len(document.content.encode('utf-8')),
        status="uploaded",
        s3_url=None  # Can be filled later when uploading to S3
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    logger.info(f"✓ Document {document.filename} uploaded (ID: {db_document.id})")
    
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
    
    - **skip**: pagination offset
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
    
    # Get documents count
    total = db.query(Document).filter(Document.user_id == user.id).count()
    
    # Get documents
    documents = db.query(Document).filter(
        Document.user_id == user.id
    ).offset(skip).limit(limit).all()
    
    logger.info(f"✓ Retrieved {len(documents)} documents for user {user.username}")
    
    return {
        "documents": documents,
        "total": total,
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
        logger.warning(f"Document {document_id} not found for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(
    document_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document (and all its analyses)"""
    logger.info(f"Deleting document {document_id} for {current_user['username']}")
    
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
    
    # Delete document (cascade deletes analyses)
    db.delete(document)
    db.commit()
    
    logger.info(f"✓ Document {document_id} deleted")
    
    return {"message": "Document deleted successfully"}


# ============================================
# ANALYSIS ENDPOINTS
# ============================================

@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def start_analysis(
    analysis: AnalysisCreate,
    current_user = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Start AI analysis on a document using Google Gemini
    
    - **document_id**: ID of document to analyze
    - **analysis_type**: summary, extraction, classification, or sentiment
    
    Analysis runs in background. Check /results/{analysis_id} for completion.
    """
    logger.info(f"Analysis request by {current_user['username']}: type={analysis.analysis_type}")
    
    # Validate analysis type
    valid_types = get_supported_analysis_types()
    if analysis.analysis_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid analysis type. Valid types: {valid_types}"
        )
    
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
        logger.warning(f"Document {analysis.document_id} not found for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create analysis record with "processing" status
    db_analysis = Analysis(
        user_id=user.id,
        document_id=document.id,
        analysis_type=analysis.analysis_type,
        status="processing"
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    analysis_id = db_analysis.id
    logger.info(f"✓ Analysis {analysis_id} created, status: processing")
    
    # Run AI analysis in background
    background_tasks.add_task(
        process_analysis,
        analysis_id=analysis_id,
        document_content=document.content,
        analysis_type=analysis.analysis_type
    )
    
    return db_analysis


def process_analysis(analysis_id: int, document_content: str, analysis_type: str):
    """
    Background task: Process document with Gemini AI
    
    This runs asynchronously and updates the database with results
    """
    logger.info(f"Background task: Processing analysis {analysis_id}")
    
    try:
        db = SessionLocal()
        
        # Update status to "processing"
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found during processing")
            return
        
        analysis.status = "processing"
        db.commit()
        
        # Call Gemini AI
        logger.info(f"Calling Gemini for analysis {analysis_id}")
        ai_result = analyze_with_gemini(document_content, analysis_type)
        
        # Update analysis with results
        if ai_result['status'] == 'success':
            analysis.status = "completed"
            analysis.result = ai_result['result']
            analysis.processing_time = int(ai_result['processing_time'])
            analysis.tokens_used = ai_result['tokens_used']
            logger.info(f"✓ Analysis {analysis_id} completed successfully")
        else:
            analysis.status = "failed"
            analysis.error_message = ai_result['error_message']
            logger.error(f"✗ Analysis {analysis_id} failed: {ai_result['error_message']}")
        
        db.commit()
        logger.info(f"✓ Analysis {analysis_id} updated in database")
        
    except Exception as e:
        logger.error(f"Error in process_analysis: {e}")
        try:
            db = SessionLocal()
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.status = "failed"
                analysis.error_message = str(e)
                db.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update analysis status: {inner_e}")
    finally:
        db.close()


@app.get("/results/{analysis_id}", response_model=AnalysisResponse, tags=["Analysis"])
async def get_analysis_result(
    analysis_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis results
    
    - **analysis_id**: ID of analysis to retrieve
    - Returns status: "processing", "completed", or "failed"
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
        logger.warning(f"Analysis {analysis_id} not found for user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    logger.info(f"✓ Retrieved analysis {analysis_id}: status={analysis.status}")
    
    return analysis


@app.get("/results", tags=["Analysis"])
async def list_analyses(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    status: str = None
):
    """
    Get all analyses for current user
    
    - **skip**: pagination offset
    - **limit**: max analyses to return
    - **status**: filter by status (processing, completed, failed)
    """
    logger.info(f"Listing analyses for {current_user['username']}")
    
    # Get user
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    query = db.query(Analysis).filter(Analysis.user_id == user.id)
    
    # Filter by status if provided
    if status:
        query = query.filter(Analysis.status == status)
    
    # Get total count
    total = query.count()
    
    # Get analyses
    analyses = query.offset(skip).limit(limit).all()
    
    logger.info(f"✓ Retrieved {len(analyses)} analyses for user {user.username}")
    
    return {
        "analyses": analyses,
        "total": total,
        "skip": skip,
        "limit": limit
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
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# STARTUP EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    logger.info("=" * 60)
    logger.info("AI Document Analyzer API Starting Up")
    logger.info("=" * 60)
    logger.info(f"Supported analysis types: {get_supported_analysis_types()}")
    logger.info("API is ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

