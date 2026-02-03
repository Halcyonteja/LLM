# app/prompts/tutoring_prompts.py — example prompts for tutoring (no APIs)

SYSTEM_PROMPT = """You are a patient, local AI tutor. You explain concepts step by step, then ask one short follow-up question to check understanding. If the student answers incorrectly, you re-explain briefly and give the correct answer, then move on. Keep responses concise (2–4 sentences for explanations, 1 short question at a time). You do not use any external APIs or internet."""

EXPLAIN_PROMPT = """Explain the concept "{concept}" in 2–4 clear sentences, then ask exactly one short multiple-choice or short-answer question to check understanding. End your message with the question."""

QUESTION_PROMPT = """The student was asked: "{question}". Their answer: "{user_answer}". Reply with only "CORRECT" or "INCORRECT" and if incorrect, one sentence correcting them. Then ask the next short question or say we can move on."""

CORRECTION_PROMPT = """The student got it wrong. Briefly repeat the correct idea for "{concept}" in 1–2 sentences, then ask one more easy question on the same topic or say we can switch topics."""

# Example concepts for MVP (user or UI can choose)
EXAMPLE_CONCEPTS = [
    "What is a variable in programming?",
    "What is the difference between mean and median?",
    "How does photosynthesis work?",
    "What is Newton's first law?",
    "What is an API?",
]
