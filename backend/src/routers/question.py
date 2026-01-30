from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime
from ..models.question import Question
from ..middleware.auth import get_current_user, require_instructor
from ..services.file_extractor import extract_text_from_file
from ..services.ai_question_generator import generate_questions_from_slides


router = APIRouter(prefix="/api/questions", tags=["questions"])


class QuestionOption(BaseModel):
    question: str
    options: List[str]
    correctAnswer: int
    difficulty: str
    category: str
    tags: Optional[List[str]] = []
    timeLimit: Optional[int] = 30


class QuestionResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    correctAnswer: int
    difficulty: str
    category: str
    tags: List[str]
    timeLimit: Optional[int] = 30
    createdAt: Optional[str] = None


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question_data: QuestionOption,
    user: dict = Depends(require_instructor)
):
    """Create a new question (instructor only)"""
    try:
        print(f"📝 Creating question by user: {user.get('email', 'unknown')}")
        print(f"📝 Question data: {question_data.dict()}")
        
        # MongoDB will automatically create the database and collection
        # when the first document is inserted
        question_dict = question_data.dict()
        question_dict["createdAt"] = datetime.now().isoformat()
        question_dict["createdBy"] = user.get("id", "")
        question_dict["createdByEmail"] = user.get("email", "")
        
        print(f"📝 Attempting to save question to MongoDB...")
        created_question = await Question.create(question_dict)
        print(f"✅ Question created successfully with ID: {created_question.get('id', '')}")
        
        # Convert to response format
        response = QuestionResponse(
            id=created_question.get("id", ""),
            question=created_question.get("question", ""),
            options=created_question.get("options", []),
            correctAnswer=created_question.get("correctAnswer", 0),
            difficulty=created_question.get("difficulty", "medium"),
            category=created_question.get("category", ""),
            tags=created_question.get("tags", []),
            timeLimit=created_question.get("timeLimit", 30),
            createdAt=created_question.get("createdAt")
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error creating question: {e}")
        print(f"❌ Full traceback:\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question: {str(e)}"
        )


@router.get("/", response_model=List[QuestionResponse])
async def get_all_questions(
    user: dict = Depends(get_current_user)
):
    """Get all questions"""
    try:
        questions = await Question.find_all()
        
        # Convert to response format
        response = []
        for q in questions:
            response.append(QuestionResponse(
                id=q.get("id", ""),
                question=q.get("question", ""),
                options=q.get("options", []),
                correctAnswer=q.get("correctAnswer", 0),
                difficulty=q.get("difficulty", "medium"),
                category=q.get("category", ""),
                tags=q.get("tags", []),
                timeLimit=q.get("timeLimit", 30),
                createdAt=q.get("createdAt")
            ))
        
        return response
    except Exception as e:
        print(f"Error retrieving questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve questions: {str(e)}"
        )


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question_by_id(
    question_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific question by ID"""
    try:
        question = await Question.find_by_id(question_id)
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return QuestionResponse(
            id=question.get("id", ""),
            question=question.get("question", ""),
            options=question.get("options", []),
            correctAnswer=question.get("correctAnswer", 0),
            difficulty=question.get("difficulty", "medium"),
            category=question.get("category", ""),
            tags=question.get("tags", []),
            timeLimit=question.get("timeLimit", 30),
            createdAt=question.get("createdAt")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve question: {str(e)}"
        )


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    question_data: QuestionOption,
    user: dict = Depends(require_instructor)
):
    """Update a question (instructor only)"""
    try:
        update_dict = question_data.dict()
        updated_question = await Question.update(question_id, update_dict)
        
        if not updated_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return QuestionResponse(
            id=updated_question.get("id", ""),
            question=updated_question.get("question", ""),
            options=updated_question.get("options", []),
            correctAnswer=updated_question.get("correctAnswer", 0),
            difficulty=updated_question.get("difficulty", "medium"),
            category=updated_question.get("category", ""),
            tags=updated_question.get("tags", []),
            timeLimit=updated_question.get("timeLimit", 30),
            createdAt=updated_question.get("createdAt")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update question: {str(e)}"
        )


@router.delete("/{question_id}")
async def delete_question(
    question_id: str,
    user: dict = Depends(require_instructor)
):
    """Delete a question (instructor only)"""
    try:
        success = await Question.delete(question_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return {"success": True, "message": "Question deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete question: {str(e)}"
        )


@router.post("/generate-from-file")
async def generate_questions_from_file(
    file: UploadFile = File(...),
    category: str = Form("General"),
    user: dict = Depends(require_instructor)
):
    """
    Upload PDF/PPTX and automatically generate questions using AI
    """
    try:
        print(f"🤖 AI Question Generation started by: {user.get('email')}")
        print(f"📄 File: {file.filename}, Category: {category}")
        
        # Extract text from file
        print("📄 Extracting text from file...")
        slides_text = await extract_text_from_file(file)
        print(f"✅ Extracted {len(slides_text)} slides/pages")
        
        if not slides_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content found in the file"
            )
        
        # Generate questions using AI
        print("🤖 Generating questions using Azure OpenAI...")
        generated_questions = await generate_questions_from_slides(slides_text, category)
        print(f"✅ Generated {len(generated_questions)} questions")
        
        if not generated_questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not generate questions from the file content"
            )
        
        # Save questions to database
        saved_questions = []
        for question_data in generated_questions:
            question_data["createdAt"] = datetime.now().isoformat()
            question_data["createdBy"] = user.get("id", "")
            question_data["createdByEmail"] = user.get("email", "")
            question_data["tags"] = question_data.get("tags", []) + ["AI Generated"]
            
            created_question = await Question.create(question_data)
            saved_questions.append(QuestionResponse(
                id=created_question.get("id", ""),
                question=created_question.get("question", ""),
                options=created_question.get("options", []),
                correctAnswer=created_question.get("correctAnswer", 0),
                difficulty=created_question.get("difficulty", "medium"),
                category=created_question.get("category", ""),
                tags=created_question.get("tags", []),
                timeLimit=created_question.get("timeLimit", 30),
                createdAt=created_question.get("createdAt")
            ))
        
        print(f"✅ Saved {len(saved_questions)} questions to database")
        
        return {
            "success": True,
            "message": f"Successfully generated and saved {len(saved_questions)} questions",
            "questions": saved_questions,
            "totalSlides": len(slides_text),
            "totalQuestions": len(saved_questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in AI question generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


