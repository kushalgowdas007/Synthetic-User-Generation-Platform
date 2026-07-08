PERSONA_PROMPT = """
You are an expert UX Researcher, Consumer Psychologist, and Behavioral Scientist.

Generate {persona_count} realistic and diverse synthetic user personas.

Return ONLY valid JSON.

Return a JSON array.

Each persona must contain:

{
    "name": "",
    "age": "",
    "gender": "",
    "occupation": "",
    "education": "",
    "income": "",
    "location": "",
    "bio": "",
    "personality_traits": [],
    "lifestyle": "",
    "hobbies": [],
    "goals": [],
    "pain_points": [],
    "buying_behavior": "",
    "technology_usage": "",
    "psychological_profile": {
        "motivation": "",
        "values": [],
        "decision_style": "",
        "risk_tolerance": "",
        "emotional_traits": []
    },
    "behavior_pattern": {
        "shopping": "",
        "communication": "",
        "social_media": "",
        "daily_routine": "",
        "brand_loyalty": ""
    },
    "big_five_personality": {
        "openness": "",
        "conscientiousness": "",
        "extraversion": "",
        "agreeableness": "",
        "neuroticism": ""
    }
}

Rules:

- Every persona must be unique.
- Different occupations.
- Different personalities.
- Different buying behaviour.
- Different technology usage.
- Different goals.
- Different lifestyles.

User Details:

Age: {age}

Gender: {gender}

Profession: {profession}

Location: {location}

Interests: {interests}

Generate exactly {persona_count} personas.
"""