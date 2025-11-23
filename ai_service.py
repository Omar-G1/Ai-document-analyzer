# ai_service.py - Google Gemini AI integration for document analysis

import google.generativeai as genai
import logging
from config import GEMINI_API_KEY
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# ============================================
# GEMINI CONFIGURATION
# ============================================

# Configure Gemini with API key
genai.configure(api_key=GEMINI_API_KEY)

# ============================================
# ANALYSIS PROMPTS
# ============================================

ANALYSIS_PROMPTS = {
    "summary": """Please provide a concise summary of the following document in 2-3 sentences. 
Focus on the main points and key information.""",
    
    "extraction": """Extract and list all important information from this document:
- Key names (people, organizations)
- Important dates
- Numbers and amounts
- Main topics
- Any action items or decisions

Format as a structured list.""",
    
    "classification": """Analyze and classify this document:
1. Document Type: (e.g., report, proposal, memo, email, contract, etc.)
2. Purpose: What is the main purpose?
3. Urgency Level: (high, medium, low)
4. Industry/Domain: What industry or field?

Explain your classification briefly.""",
    
    "sentiment": """Analyze the sentiment and tone of this document:
1. Overall Sentiment: (positive, negative, neutral, mixed)
2. Tone: (formal, informal, urgent, friendly, etc.)
3. Confidence Level: (high, medium, low)
4. Key emotions expressed (if any)

Provide brief reasoning for your analysis.""",
}


# ============================================
# GEMINI ANALYSIS FUNCTION
# ============================================

def analyze_with_gemini(
    document_content: str,
    analysis_type: str = "summary"
) -> dict:
    """
    Analyze document using Google Gemini API
    
    Args:
        document_content (str): Document text to analyze
        analysis_type (str): Type of analysis (summary, extraction, classification, sentiment)
    
    Returns:
        dict: Contains status, result, processing_time, and metadata
    
    Example:
        >>> result = analyze_with_gemini("Your document text", "summary")
        >>> print(result["result"])
    """
    try:
        logger.info(f"Starting Gemini analysis: type={analysis_type}")
        
        # Validate analysis type
        if analysis_type not in ANALYSIS_PROMPTS:
            logger.warning(f"Unknown analysis type: {analysis_type}. Using summary.")
            analysis_type = "summary"
        
        # Get appropriate prompt
        prompt = ANALYSIS_PROMPTS[analysis_type]
        
        # Build full prompt
        full_prompt = f"""{prompt}

DOCUMENT TO ANALYZE:
-------------------
{document_content}
-------------------

Please provide a thorough and accurate analysis:"""
        
        # Create Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        # Record start time
        start_time = datetime.utcnow()
        
        # Generate response from Gemini
        logger.info(f"Calling Gemini API for {analysis_type} analysis")
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,  # Balanced creativity vs accuracy
                top_p=0.8,
                max_output_tokens=1024,
            )
        )
        
        # Record end time
        end_time = datetime.utcnow()
        
        # Calculate processing time
        processing_time = (end_time - start_time).total_seconds()
        
        # Get result text
        result_text = response.text
        
        logger.info(f"✓ Gemini analysis completed in {processing_time:.2f}s")
        logger.info(f"  Result length: {len(result_text)} characters")
        
        return {
            "status": "success",
            "result": result_text,
            "analysis_type": analysis_type,
            "model": "gemini-pro",
            "processing_time": processing_time,
            "tokens_used": 0,  # Gemini doesn't expose token count in free tier
            "timestamp": end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"✗ Gemini analysis error: {type(e).__name__}: {e}")
        return {
            "status": "error",
            "result": None,
            "analysis_type": analysis_type,
            "error_message": str(e),
            "model": "gemini-pro",
            "processing_time": 0,
            "tokens_used": 0,
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================
# BATCH ANALYSIS
# ============================================

def analyze_batch(documents: list, analysis_type: str = "summary") -> list:
    """
    Analyze multiple documents (one at a time)
    
    Args:
        documents (list): List of document texts
        analysis_type (str): Type of analysis to apply to all
    
    Returns:
        list: List of analysis results
    
    Example:
        >>> docs = ["Document 1", "Document 2"]
        >>> results = analyze_batch(docs, "summary")
    """
    logger.info(f"Starting batch analysis of {len(documents)} documents")
    results = []
    
    for idx, doc in enumerate(documents, 1):
        logger.info(f"Analyzing document {idx}/{len(documents)}")
        result = analyze_with_gemini(doc, analysis_type)
        results.append(result)
        
        # Small delay between requests to avoid rate limiting
        if idx < len(documents):
            time.sleep(0.5)
    
    logger.info(f"Batch analysis completed")
    return results


# ============================================
# SUPPORTED ANALYSIS TYPES
# ============================================

def get_supported_analysis_types() -> list:
    """
    Get list of supported analysis types
    
    Returns:
        list: Available analysis types
    
    Example:
        >>> types = get_supported_analysis_types()
        >>> print(types)
        ['summary', 'extraction', 'classification', 'sentiment']
    """
    return list(ANALYSIS_PROMPTS.keys())


# ============================================
# CONNECTION TEST
# ============================================

def test_gemini_connection() -> bool:
    """
    Test Gemini API connection
    
    Returns:
        bool: True if connection successful, False otherwise
    
    Example:
        >>> if test_gemini_connection():
        ...     print("Ready to analyze!")
    """
    try:
        logger.info("Testing Gemini API connection...")
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'Connection successful!'")
        
        if response.text:
            logger.info(f"✓ Gemini connection successful!")
            logger.info(f"  Response: {response.text[:50]}...")
            return True
        else:
            logger.error("✗ Gemini connection failed: no response")
            return False
            
    except Exception as e:
        logger.error(f"✗ Gemini connection error: {type(e).__name__}: {e}")
        return False


# ============================================
# UTILITY FUNCTIONS
# ============================================

def truncate_document(content: str, max_chars: int = 10000) -> str:
    """
    Truncate document if too long (Gemini has limits)
    
    Args:
        content (str): Document content
        max_chars (int): Maximum characters
    
    Returns:
        str: Truncated or original content
    """
    if len(content) > max_chars:
        logger.warning(f"Document truncated from {len(content)} to {max_chars} chars")
        return content[:max_chars] + "..."
    return content
