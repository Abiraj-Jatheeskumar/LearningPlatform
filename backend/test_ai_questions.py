"""
Test the AI question generation endpoint with a sample PDF
"""
import requests
import os

# Backend URL
BASE_URL = "http://127.0.0.1:3001"

# Login first to get token
def login():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "instructor@example.com",
            "password": "password123"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

# Test the question generation endpoint
def test_question_generation(token):
    # Create a simple test PDF file
    test_pdf_path = "test_sample.pdf"
    
    # For testing, we'll use a simple text file
    # In real scenario, upload an actual PDF
    with open(test_pdf_path, "w") as f:
        f.write("This is a test file for question generation.")
    
    try:
        with open(test_pdf_path, "rb") as f:
            files = {
                "file": ("test_sample.pdf", f, "application/pdf")
            }
            data = {
                "category": "Python Programming"
            }
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            print("\n📤 Uploading file and generating questions...")
            response = requests.post(
                f"{BASE_URL}/api/questions/generate-from-file",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Success!")
                print(f"   Total slides/pages: {result.get('totalSlides', 0)}")
                print(f"   Total questions generated: {result.get('totalQuestions', 0)}")
                print(f"\n📝 Generated Questions:")
                for i, q in enumerate(result.get('questions', []), 1):
                    print(f"\n   Question {i}:")
                    print(f"   Q: {q['question']}")
                    print(f"   Options: {q['options']}")
                    print(f"   Correct: {q['correctAnswer']}")
                    print(f"   Difficulty: {q['difficulty']}")
            else:
                print(f"\n❌ Failed: {response.status_code}")
                print(response.text)
    finally:
        # Clean up test file
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)

if __name__ == "__main__":
    print("🧪 Testing AI Question Generation API\n")
    print("=" * 60)
    
    token = login()
    if token:
        test_question_generation(token)
    else:
        print("Cannot proceed without authentication token")
