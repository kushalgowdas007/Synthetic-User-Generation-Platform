from typing import Dict

from backend.memory.memory_store import MemoryStore
from backend.memory.conversation import ConversationHistory
from backend.memory.opinion_tracker import OpinionTracker
from backend.memory.consistency import ConsistencyChecker
from backend.services.gemini_service import generate_response


class InterviewAgent:
    """
    Handles conversational interviews with synthetic personas.
    """

    def __init__(self):

        self.memory = MemoryStore()
        self.conversation = ConversationHistory()
        self.opinions = OpinionTracker()
        self.consistency = ConsistencyChecker()

        self.persona = {}
        self.persona_id = ""

    def start_interview(self, persona_id: str, persona_data: Dict):

        self.persona_id = persona_id
        self.persona = persona_data

        return {
            "status": "success",
            "message": f"Interview started with {persona_data.get('name', 'Persona')}"
        }

    def build_prompt(self, question: str):

        memories = self.memory.get_memories(self.persona_id)
        opinions = self.opinions.get_opinions(self.persona_id)
        history = self.conversation.get_history(self.persona_id)

        memory_text = "\n".join(
            [f"- {m.text}" for m in memories]
        ) or "No memories yet."

        opinion_text = "\n".join(
            [f"- {o.topic}: {o.value}" for o in opinions]
        ) or "No opinions recorded."

        history_text = "\n".join(
            [f"{msg.role}: {msg.message}" for msg in history]
        ) or "No previous conversation."

        prompt = f"""
You are a realistic synthetic user.

Never reveal that you are an AI.

Always stay consistent with your previous answers.

Speak naturally in first person.

--------------------------
PERSONA
--------------------------
{self.persona}

--------------------------
MEMORIES
--------------------------
{memory_text}

--------------------------
OPINIONS
--------------------------
{opinion_text}

--------------------------
CONVERSATION HISTORY
--------------------------
{history_text}

--------------------------
QUESTION
--------------------------
{question}

Answer naturally as this person.
"""

        return prompt

    def generate_reply(self, prompt: str):

        return generate_response(prompt)

    def update_memory(self, response: str):

        self.memory.add_memory(
            self.persona_id,
            response
        )

    def track_opinion(self, response: str):

        text = response.lower()

        if "online shopping" in text:
            self.opinions.add_opinion(
                self.persona_id,
                "shopping",
                "prefers online shopping"
            )

        if "android" in text:
            self.opinions.add_opinion(
                self.persona_id,
                "technology",
                "likes Android"
            )

        if "iphone" in text:
            self.opinions.add_opinion(
                self.persona_id,
                "technology",
                "likes iPhone"
            )

        if "vegetarian" in text:
            self.opinions.add_opinion(
                self.persona_id,
                "food",
                "vegetarian"
            )

    def ask_question(self, question: str):

        self.conversation.save_message(
            self.persona_id,
            "user",
            question
        )

        prompt = self.build_prompt(question)

        print("\n" + "=" * 60)
        print("Generating response from Gemini...")
        print(f"Persona: {self.persona.get('name')}")
        print(f"Question: {question}")

        try:
            response = self.generate_reply(prompt)

            print("Response received successfully.")

        except Exception as e:

            print("Interview Error:", e)

            response = "Sorry, I couldn't generate a response."

        print("=" * 60)
        history = [
            msg.message
            for msg in self.conversation.get_history(
                self.persona_id
            )
        ]

        check1 = self.consistency.check_persona(
            self.persona,
            response
        )

        check2 = self.consistency.check_history(
            history,
            response
        )

        if (
            not check1["consistent"]
            or not check2["consistent"]
        ):
            print("⚠ Consistency Warning")
            print(check1)
            print(check2)

        self.conversation.save_message(
            self.persona_id,
            "persona",
            response
        )

        self.update_memory(response)

        self.track_opinion(response)

        return response

    def end_interview(self):

        return {
            "status": "success",
            "message": "Interview completed successfully."
        }