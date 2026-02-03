# backend/app/services/teaching_engine.py
from typing import List, Optional, Tuple
from app.prompts.tutoring_prompts import (
    EXPLAIN_PROMPT,
    QUESTION_PROMPT,
    CORRECTION_PROMPT,
)

# Keep the state class as is
class TeachingState:
    def __init__(self):
        self.current_concept: Optional[str] = None
        self.last_question: Optional[str] = None
        self.waiting_for_answer: bool = False

def get_explanation_prompt(concept: str) -> str:
    """Returns the prompt string for explaining a concept."""
    return EXPLAIN_PROMPT.format(concept=concept)

def get_check_answer_prompt(question: str, user_answer: str) -> str:
    """Returns the prompt string for checking an answer."""
    return QUESTION_PROMPT.format(question=question, user_answer=user_answer)

def get_correction_prompt(concept: str) -> str:
    """Returns the prompt string for correcting a concept."""
    return CORRECTION_PROMPT.format(concept=concept)