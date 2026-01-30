import os
import json
import httpx
from typing import Dict, Any, List

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

SYSTEM_PROMPT = """You are an academic MCQ generator.

Rules:
- Use ONLY the provided slide text.
- Do NOT use outside knowledge.
- Generate EXACTLY 1 multiple-choice question.
- The question must have 4 options.
- EXACTLY ONE option must be correct.
- Question length must be under 25 words.
- Assign difficulty: easy, medium, or hard.
- If slide text is too short or empty, return: {"status":"insufficient_content"}
- Output STRICT valid JSON only.
- No markdown. No extra text.

JSON format:
{
  "question": "question text here",
  "options": ["option1", "option2", "option3", "option4"],
  "correctAnswer": 0,
  "difficulty": "easy",
  "category": "General"
}"""


async def generate_question_from_text(text: str, category: str = "General") -> Dict[str, Any]:
    """
    Generate a single MCQ question from text using Azure OpenAI
    """
    if not all([AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT]):
        raise ValueError("Azure OpenAI credentials not configured")
    
    if not text or len(text.strip()) < 20:
        return {"status": "insufficient_content"}
    
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Slide text:\n{text}\n\nCategory: {category}"}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON response
            question_data = json.loads(content)
            
            # Check if insufficient content
            if question_data.get("status") == "insufficient_content":
                return {"status": "insufficient_content"}
            
            # Validate structure
            if not all(key in question_data for key in ["question", "options", "correctAnswer", "difficulty"]):
                raise ValueError("Invalid question structure")
            
            # Add category
            question_data["category"] = category
            question_data["timeLimit"] = 30
            question_data["tags"] = ["AI Generated"]
            
            return question_data
            
    except httpx.HTTPStatusError as e:
        raise Exception(f"Azure OpenAI API error: {e.response.status_code} - {e.response.text}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Question generation failed: {str(e)}")


async def generate_questions_from_slides(slides_text: List[str], category: str = "General") -> List[Dict[str, Any]]:
    """
    Generate multiple questions from a list of slide texts
    """
    questions = []
    
    for idx, text in enumerate(slides_text):
        try:
            question = await generate_question_from_text(text, category)
            if question.get("status") != "insufficient_content":
                questions.append(question)
        except Exception as e:
            print(f"Failed to generate question from slide {idx + 1}: {str(e)}")
            continue
    
    return questions
