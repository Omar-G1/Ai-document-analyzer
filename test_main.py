# test_main_updated.py - Test complete API with AI integration

from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)

print("=" * 70)
print("Testing Complete AI Document Analyzer API")
print("=" * 70)

# Test 1: Health check
print("\n✓ Test 1: Health Check")
response = client.get("/health")
print(f"  Status: {response.status_code}")
assert response.status_code == 200

# Test 2: Analysis types
print("\n✓ Test 2: Get Supported Analysis Types")
response = client.get("/analysis-types")
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  Types: {data['supported_types']}")

# Test 3: Signup
print("\n✓ Test 3: User Signup")
response = client.post("/auth/signup", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
})
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"  Token received: {token[:30]}...")
else:
    print(f"  Error: {response.json()}")

# Test 4: Login
print("\n✓ Test 4: User Login")
response = client.post("/auth/login", json={
    "username": "testuser",
    "password": "testpass123"
})
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"  Token received: {token[:30]}...")
else:
    print(f"  Error: {response.json()}")

headers = {"Authorization": f"Bearer {token}"}

# Test 5: Upload document
print("\n✓ Test 5: Upload Document")
response = client.post(
    "/documents/upload",
    json={
        "filename": "test_doc.txt",
        "file_type": "text",
        "content": "The climate crisis is urgent. We need renewable energy and carbon reduction."
    },
    headers=headers
)
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    doc = response.json()
    doc_id = doc["id"]
    print(f"  Document ID: {doc_id}")
    print(f"  Status: {doc['status']}")

# Test 6: List documents
print("\n✓ Test 6: List Documents")
response = client.get("/documents", headers=headers)
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  Total documents: {data['total']}")

# Test 7: Start analysis
print("\n✓ Test 7: Start Analysis (Summary)")
response = client.post(
    "/analyze",
    json={
        "document_id": doc_id,
        "analysis_type": "summary"
    },
    headers=headers
)
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    analysis = response.json()
    analysis_id = analysis["id"]
    print(f"  Analysis ID: {analysis_id}")
    print(f"  Status: {analysis['status']}")
else:
    print(f"  Error: {response.json()}")

# Test 8: Wait and check analysis results
print("\n✓ Test 8: Check Analysis Results (waiting for processing)")
for i in range(10):
    response = client.get(f"/results/{analysis_id}", headers=headers)
    if response.status_code == 200:
        analysis = response.json()
        print(f"  Attempt {i+1}: Status = {analysis['status']}")
        
        if analysis['status'] == 'completed':
            print(f"  ✓ Analysis completed!")
            print(f"  Result preview: {analysis['result'][:100]}...")
            print(f"  Processing time: {analysis['processing_time']}s")
            break
        elif analysis['status'] == 'failed':
            print(f"  ✗ Analysis failed: {analysis['error_message']}")
            break
    
    time.sleep(1)

# Test 9: List all analyses
print("\n✓ Test 9: List All Analyses")
response = client.get("/results", headers=headers)
print(f"  Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  Total analyses: {data['total']}")

print("\n" + "=" * 70)
print("✓✓✓ All API tests completed! ✓✓✓")
print("=" * 70)
