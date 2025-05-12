from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas import ChatQuestion, ChatResponse, ChatSessionData, ChatAnswerData, EligibilityResult

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/start_chat", response_model=ChatResponse)
async def start_chat(session_data: ChatSessionData):
    """
    Start a new chat session or resume an existing one
    """
    # In a real implementation, this would fetch data from a database
    # For now, we'll just return a mock response
    return ChatResponse(
        nextQuestion=ChatQuestion(
            id=1,
            text="Do you have a family history of breast cancer?"
        )
    )

@router.post("/submit_answer", response_model=ChatResponse)
async def submit_answer(answer_data: ChatAnswerData):
    """
    Submit an answer and get the next question
    """
    # In a real implementation, this would store the answer in a database
    # and determine the next question based on a decision tree
    
    next_question_id = answer_data.questionId + 1
    next_questions = {
        2: "How old are you?",
        3: "Have you had genetic testing for BRCA1 or BRCA2?",
        4: "Have you had a mammogram in the last year?",
    }
    
    if next_question_id > 4:
        # End of questions
        return ChatResponse(
            question=ChatQuestion(
                id=answer_data.questionId,
                text=f"Question {answer_data.questionId}"
            )
        )
    
    return ChatResponse(
        question=ChatQuestion(
            id=answer_data.questionId,
            text=f"Question {answer_data.questionId}"
        ),
        nextQuestion=ChatQuestion(
            id=next_question_id,
            text=next_questions.get(next_question_id, "Default question")
        )
    )

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get the chat history for a session
    """
    # In a real implementation, this would fetch data from a database
    return {
        "history": [
            {"question": "Question 1", "answer": "Answer 1"},
            {"question": "Question 2", "answer": "Answer 2"},
        ]
    }
