"""
Groq Service — Doctor consultation AI with integrated web search.
The AI can search for drug info, treatment guidelines, and prescriptions
before drawing conclusions — just like a doctor who does their research.
"""

import base64
import json
import re
from typing import Optional

from groq import AsyncGroq
from app.config import settings
from app.services.search_service import search_medical, format_for_prompt

_client: Optional[AsyncGroq] = None


def get_groq_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


# ── SEARCH TOOL DEFINITION FOR GROQ TOOL CALLING ──────────────

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_medical_info",
        "description": (
            "Search the internet for current medical information. Use this when you need to: "
            "look up drug interactions, dosages or contraindications; verify treatment guidelines; "
            "check prescriptions or medications; research a specific condition; find current "
            "medical recommendations. Always search before giving drug-specific advice."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific medical search query e.g. 'metformin side effects Nigeria' or 'malaria treatment guidelines 2024'"
                }
            },
            "required": ["query"]
        }
    }
}


# ── SYSTEM PROMPT ──────────────────────────────────────────────

def build_doctor_system_prompt(patient_context: str = "", health_notes: str = "") -> str:
    base = """You are Dr. MedBot, a highly experienced AI physician specialising in internal medicine, primary care, and tropical medicine — focused on Nigeria and West Africa.

CONSULTATION RULES — follow strictly:

1. READ THE FILE FIRST: You have the patient's full medical history and your own clinical notes from past sessions. Reference them naturally.

2. GATHER BEFORE CONCLUDING: Never jump to diagnosis without enough information. Ask 2-3 focused, conversational questions per turn. Use SOCRATES for pain: Site, Onset, Character, Radiation, Associations, Time, Exacerbating/Relieving, Severity.

3. SEARCH BEFORE CONCLUDING: When you need to recommend a drug, verify a dosage, check interactions, or confirm treatment guidelines — use the search tool first. Never guess on drug specifics.

4. LANGUAGE: Always respond in the exact language the patient used — Yoruba, Hausa, Igbo, Pidgin, French, or English.

5. AFRICAN CONTEXT: Always consider: malaria, typhoid, sickle cell, hypertension, diabetes, TB. Don't assume a Western disease profile.

6. REMEMBER PAST SESSIONS: Use your clinical notes. Reference what the patient mentioned before. Ask follow-ups on previously noted concerns.

7. EMERGENCIES: If symptoms suggest emergency — say so immediately and clearly. Direct to hospital NOW.

8. TONE: Warm, caring, professional. You are their trusted family doctor who has known them for years.

9. CONSULTATION STAGES:
   - Turns 1-2: Warm greeting, acknowledge complaint, ask clarifying questions
   - Turns 3-4: Deeper clinical questions, search relevant drug/condition info
   - Turns 5+: Considered assessment with differentials, searched-and-verified recommendations

10. NEVER say "you have X" in early turns — say "this could suggest X, but I need to understand more..."

11. Always end assessments with a brief disclaimer that this supplements but does not replace in-person care."""

    if patient_context:
        base += f"""

══════════════════════════════════════
PATIENT MEDICAL FILE
══════════════════════════════════════
{patient_context}
══════════════════════════════════════"""

    if health_notes:
        base += f"""

══════════════════════════════════════
YOUR CLINICAL NOTES FROM PAST SESSIONS
══════════════════════════════════════
{health_notes}
══════════════════════════════════════
Reference these naturally. Ask follow-ups on previously flagged concerns."""

    return base


NOTE_EXTRACTION_PROMPT = """You are a clinical documentation AI. Extract clinically relevant information from this conversation for future sessions.

Return ONLY valid JSON:
{
  "presenting_complaints": ["symptom1"],
  "suspected_conditions": ["condition1"],
  "lifestyle_notes": "diet/exercise/sleep/stress observations or null",
  "family_history_notes": "family history mentioned or null",
  "medication_concerns": "adherence issues or side effects or null",
  "pain_patterns": "location/timing/severity or null",
  "mental_health_notes": "mood/anxiety/stress or null",
  "important_flags": ["red flag to follow up"],
  "key_concerns": "top thing to follow up next session or null",
  "raw_notes": "2-3 sentence clinical observation or null"
}
If nothing to note for a field, use null. Return ONLY the JSON."""

SYMPTOM_CHECK_PROMPT = """Medical triage AI. Analyze symptoms, return ONLY valid JSON:
{
  "symptoms_identified": ["symptom1"],
  "triage_level": "URGENT",
  "triage_explanation": "brief explanation",
  "possible_conditions": [{"condition": "Name", "likelihood": "high/medium/low", "icd10": "code or null"}],
  "recommendations": "clear actionable advice",
  "when_to_seek_emergency": "specific warning signs",
  "follow_up_questions": ["clarifying question"]
}
Consider Nigerian/African context. Return ONLY the JSON."""

IMAGE_PROMPT = """Medical image analysis AI. Return ONLY valid JSON:
{
  "image_content": "what is visible",
  "medical_observations": ["observation1"],
  "possible_conditions": ["condition1"],
  "urgency": "none/low/medium/high/emergency",
  "recommendations": "what patient should do",
  "confidence": "low/medium/high",
  "limitations": "what cannot be determined from image"
}
Return ONLY the JSON."""


# ── SPEECH TO TEXT ─────────────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    client = get_groq_client()
    transcription = await client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=settings.GROQ_WHISPER_MODEL,
        response_format="verbose_json",
        temperature=0.0,
    )
    return {
        "text": transcription.text,
        "language_detected": getattr(transcription, "language", None),
        "duration_seconds": getattr(transcription, "duration", None),
    }


# ── DOCTOR CONSULTATION WITH SEARCH ───────────────────────────

async def consult_patient(
    user_message: str,
    language: str = "en",
    conversation_history: list = None,
    patient_context: str = "",
    health_notes: str = "",
) -> str:
    """
    Full doctor consultation with integrated web search.
    The AI can call search_medical_info before concluding.
    """
    client = get_groq_client()
    system = build_doctor_system_prompt(patient_context, health_notes)

    messages = [{"role": "system", "content": system}]
    if conversation_history:
        messages.extend(conversation_history[-20:])
    messages.append({"role": "user", "content": user_message})

    # First call — AI may decide to search
    response = await client.chat.completions.create(
        model=settings.GROQ_LLM_MODEL,
        messages=messages,
        tools=[SEARCH_TOOL],
        tool_choice="auto",
        max_tokens=1200,
        temperature=0.4,
    )

    choice = response.choices[0]

    # Handle tool calls (search requests)
    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        # Add assistant's tool call message
        messages.append({
            "role": "assistant",
            "content": choice.message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in choice.message.tool_calls
            ]
        })

        # Execute all search calls
        for tool_call in choice.message.tool_calls:
            if tool_call.function.name == "search_medical_info":
                try:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", user_message)
                    results = await search_medical(query, max_results=4)
                    search_text = format_for_prompt(results)
                except Exception:
                    search_text = "Search unavailable."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Search results for '{query}':\n\n{search_text}"
                })

        # Second call with search results injected
        final_response = await client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=messages,
            max_tokens=1200,
            temperature=0.4,
        )
        return final_response.choices[0].message.content

    return choice.message.content


# ── EXTRACT HEALTH NOTES FROM CONVERSATION ────────────────────

async def extract_health_notes(conversation_messages: list) -> dict:
    if not conversation_messages or len(conversation_messages) < 2:
        return {}
    client = get_groq_client()
    convo_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in conversation_messages
    ])
    response = await client.chat.completions.create(
        model=settings.GROQ_LLM_MODEL,
        messages=[
            {"role": "system", "content": NOTE_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract notes:\n\n{convo_text}"},
        ],
        max_tokens=800,
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(match.group()) if match else {}


# ── SYMPTOM ANALYSIS ───────────────────────────────────────────

async def analyze_symptoms(
    symptoms_text: str,
    language: str = "en",
    patient_context: str = "",
) -> dict:
    client = get_groq_client()
    text = symptoms_text
    if language != "en":
        text = await translate_text(symptoms_text, source=language, target="en")

    system = SYMPTOM_CHECK_PROMPT
    if patient_context:
        system += f"\n\nPATIENT HISTORY:\n{patient_context}"

    response = await client.chat.completions.create(
        model=settings.GROQ_LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Analyze: {text}"},
        ],
        max_tokens=1500,
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    if language != "en":
        for field in ["recommendations", "triage_explanation"]:
            if result.get(field):
                result[field] = await translate_text(result[field], source="en", target=language)
    return result


# ── IMAGE ANALYSIS ─────────────────────────────────────────────

async def analyze_image(image_bytes: bytes, image_type: str = "symptom") -> dict:
    client = get_groq_client()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = "image/png" if image_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"

    prompts = {
        "symptom": "Analyze this medical symptom image. What do you observe?",
        "medication": "Identify this medication. Name, dosage, markings?",
        "document": "Extract and summarize the medical information.",
    }

    response = await client.chat.completions.create(
        model=settings.GROQ_VISION_MODEL,
        messages=[
            {"role": "system", "content": IMAGE_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                {"type": "text", "text": prompts.get(image_type, prompts["symptom"])},
            ]},
        ],
        max_tokens=1000,
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "medical_observations": [raw], "urgency": "low",
            "confidence": "low", "recommendations": "Consult a healthcare professional.",
            "limitations": "Structured analysis unavailable."
        }


# ── TRANSLATION ────────────────────────────────────────────────

async def translate_text(text: str, source: str, target: str) -> str:
    if source == target:
        return text
    client = get_groq_client()
    lang_names = settings.LANGUAGE_NAMES
    response = await client.chat.completions.create(
        model=settings.GROQ_LLM_MODEL,
        messages=[
            {"role": "system", "content": (
                f"Translate from {lang_names.get(source, source)} to {lang_names.get(target, target)}. "
                "Preserve medical accuracy. Return ONLY the translated text."
            )},
            {"role": "user", "content": text},
        ],
        max_tokens=2000,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


# ── BUILD CONTEXT STRINGS ──────────────────────────────────────

def build_patient_context(patient) -> str:
    if not patient:
        return ""
    from app.utils.helpers import calculate_age, calculate_bmi
    age = calculate_age(patient.date_of_birth)
    bmi = calculate_bmi(patient.height_cm, patient.weight_kg)
    lines = [
        f"Patient: {patient.first_name} {patient.last_name}",
        f"Age: {age or 'unknown'} | Gender: {patient.gender or 'not specified'}",
        f"Blood Group: {patient.blood_group or 'unknown'} | BMI: {bmi or 'unknown'}",
        f"Location: {patient.state or ''}, {patient.country or 'Nigeria'}",
        f"Allergies: {', '.join(patient.allergies) if patient.allergies else 'none reported'}",
    ]
    if patient.medical_conditions:
        conds = [f"{c.condition_name} ({c.status})" for c in patient.medical_conditions]
        lines.append(f"Conditions: {', '.join(conds)}")
    if patient.medications:
        meds = [f"{m.drug_name} {m.dosage or ''} {m.frequency or ''}".strip()
                for m in patient.medications if m.status == "active"]
        if meds:
            lines.append(f"Current Medications: {', '.join(meds)}")
    return "\n".join(lines)


def build_health_notes_context(notes) -> str:
    if not notes:
        return ""
    lines = []
    if notes.conversation_count:
        lines.append(f"Total consultations: {notes.conversation_count}")
    if notes.presenting_complaints:
        lines.append(f"Recurring complaints: {', '.join(notes.presenting_complaints)}")
    if notes.suspected_conditions:
        lines.append(f"Previously suspected: {', '.join(notes.suspected_conditions)}")
    if notes.lifestyle_notes:
        lines.append(f"Lifestyle: {notes.lifestyle_notes}")
    if notes.family_history_notes:
        lines.append(f"Family history: {notes.family_history_notes}")
    if notes.medication_concerns:
        lines.append(f"Medication concerns: {notes.medication_concerns}")
    if notes.pain_patterns:
        lines.append(f"Pain patterns: {notes.pain_patterns}")
    if notes.mental_health_notes:
        lines.append(f"Mental health: {notes.mental_health_notes}")
    if notes.important_flags:
        lines.append(f"⚑ FLAGS: {', '.join(notes.important_flags)}")
    if notes.key_concerns:
        lines.append(f"Follow up on: {notes.key_concerns}")
    if notes.last_summary:
        lines.append(f"Last session: {notes.last_summary}")
    if notes.raw_notes:
        lines.append(f"Notes: {notes.raw_notes}")
    return "\n".join(lines)