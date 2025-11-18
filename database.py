from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL



engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries
    pool_pre_ping=True,  # Test connection before using
    pool_recycle=3600,  # Recycle connections every hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# DATABASE MODELS (Tables)

class User(Base):
    """User model - stores user account information"""
    __tablename__ = "users"

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (connect to other tables)
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Document(Base):
    """Document model - stores uploaded documents"""
    __tablename__ = "documents"

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), default="text")  # pdf, txt, docx, etc.
    file_size = Column(Integer)  # bytes
    s3_url = Column(String(500))  # URL in AWS S3
    status = Column(String(20), default="uploaded")  # uploaded, processing, analyzed
    content = Column(Text)  # Store document text content
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key relationship
    owner = relationship("User", back_populates="documents")
    # Reverse relationship to analyses
    analyses = relationship("Analysis", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class Analysis(Base):
    """Analysis model - stores AI analysis results"""
    __tablename__ = "analyses"

    # Columns
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    analysis_type = Column(String(50))  # summary, extraction, classification, etc.
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    result = Column(Text)  # AI-generated analysis result
    error_message = Column(String(500))  # Error if processing failed
    tokens_used = Column(Integer, default=0)  # OpenAI tokens used (for cost tracking)
    processing_time = Column(Integer)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign key relationships
    owner = relationship("User", back_populates="analyses")
    document = relationship("Document", back_populates="analyses")

    def __repr__(self):
        return f"<Analysis(id={self.id}, type={self.analysis_type})>"


# ============================================
# DATABASE INITIALIZATION
# ============================================

def create_tables():
    """Create all tables in database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session - used in FastAPI endpoints"""
    db = SessionLocal()
    try:
        yield db  # Provide session to endpoint
    finally:
        db.close()  # Close session after request


# Create tables when module is imported
create_tables()
print("✓ Database tables created/verified")
