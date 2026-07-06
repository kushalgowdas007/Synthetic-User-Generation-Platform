PERSONA_PROMPT = """
You are an expert UX Researcher.

Generate a realistic synthetic user persona.

Return ONLY valid JSON.

Include:

- Name
- Age
- Gender
- Occupation
- Income
- Personality Traits
- Behaviour
- Goals
- Pain Points
- Buying Behaviour
- Digital Usage

Product:
{product}

Description:
{description}

Audience:
{audience}

Research Goal:
{objective}
"""