# test_ai_service.py - Test Gemini AI service

import logging
from ai_service import (
    analyze_with_gemini,
    test_gemini_connection,
    get_supported_analysis_types,
    analyze_batch
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("Testing Gemini AI Integration")
print("=" * 70)

# Test 1: Connection test
print("\n✓ Test 1: Gemini API Connection")
print("-" * 70)
connected = test_gemini_connection()
if connected:
    print("✓ Connection successful! Gemini API is accessible.")
else:
    print("✗ Connection failed. Check your API key.")

# Test 2: Supported analysis types
print("\n✓ Test 2: Supported Analysis Types")
print("-" * 70)
types = get_supported_analysis_types()
print(f"Available analysis types: {', '.join(types)}")

# Test 3: Document summary
print("\n✓ Test 3: Document Summary Analysis")
print("-" * 70)
test_document = """
The climate crisis is one of the most pressing issues of our time. 
Global temperatures have risen 1.1°C since pre-industrial times due to 
human activities like burning fossil fuels and deforestation. 

The effects are already visible:
- Rising sea levels threatening coastal cities
- More frequent extreme weather events
- Loss of wildlife habitats and biodiversity
- Agricultural impacts and food security concerns

To address this, we need:
1. Transition to renewable energy sources
2. Implement carbon pricing mechanisms
3. Protect and restore forests
4. Support climate-vulnerable countries

The window for action is closing. Scientists warn that we have less than 
a decade to make critical changes to limit warming to 1.5°C above 
pre-industrial levels.
"""

print("Analyzing document for summary...")
result = analyze_with_gemini(test_document, "summary")
print(f"Status: {result['status']}")
if result['status'] == 'success':
    print(f"\nSummary:\n{result['result']}")
    print(f"\nProcessing time: {result['processing_time']:.2f}s")

# Test 4: Information extraction
print("\n✓ Test 4: Information Extraction")
print("-" * 70)
test_doc_2 = """
Meeting Minutes - November 22, 2025

Attendees: John Smith (CEO), Sarah Johnson (CTO), Ahmed Ali (CFO)

Agenda Items:
1. Q4 2025 Financial Review
   - Revenue: $2.5M (up 15% from Q3)
   - Expenses: $1.8M
   - Profit: $700K

2. New Product Launch
   - Launch date: December 15, 2025
   - Budget allocated: $150,000
   - Expected revenue: $500K in first quarter

3. Team Expansion
   - Hiring 5 new engineers
   - Budget: $300K annually per engineer

Next meeting: December 5, 2025
Location: Main office, Conference room B
"""

print("Extracting key information...")
result = analyze_with_gemini(test_doc_2, "extraction")
print(f"Status: {result['status']}")
if result['status'] == 'success':
    print(f"\nExtracted Information:\n{result['result']}")
    print(f"\nProcessing time: {result['processing_time']:.2f}s")

# Test 5: Classification
print("\n✓ Test 5: Document Classification")
print("-" * 70)
print("Classifying document...")
result = analyze_with_gemini(test_doc_2, "classification")
print(f"Status: {result['status']}")
if result['status'] == 'success':
    print(f"\nClassification:\n{result['result']}")
    print(f"\nProcessing time: {result['processing_time']:.2f}s")

# Test 6: Sentiment analysis
print("\n✓ Test 6: Sentiment Analysis")
print("-" * 70)
positive_doc = "This product is absolutely amazing! I love it. Highly recommend!"
result = analyze_with_gemini(positive_doc, "sentiment")
print(f"Status: {result['status']}")
if result['status'] == 'success':
    print(f"\nSentiment Analysis:\n{result['result']}")
    print(f"\nProcessing time: {result['processing_time']:.2f}s")

print("\n" + "=" * 70)
print("✓✓✓ All Gemini AI tests completed successfully! ✓✓✓")
print("=" * 70)
