from pages.workspace import workspace_ui
from services.gemini_service import generate_persona
from services.faker_service import enrich_persona
from pages.persona_cards import display_persona

def main():
    data = workspace_ui()

    if data:
        persona = generate_persona(data)
        persona = enrich_persona(persona)
        display_persona(persona)

if __name__ == "__main__":
    main()