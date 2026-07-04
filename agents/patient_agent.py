import json
import logging
import os
from typing import Optional

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None  # type: ignore[assignment]

from config import MODEL_NAME, GROQ_API_KEY, TIMEOUT_SECONDS
from schemas.outputs import GuidelineOutput, RiskOutput, PatientOutput
from security.content_filter import filter_patient_output
from utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)


class PatientAgent:
    """Converts clinical findings into plain-language patient communication."""

    def __init__(self, client=None, dependencies=None):
        api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        self.client = client
        if self.client is None and api_key and Groq is not None:
            self.client = Groq(api_key=api_key)
        self.dependencies = dependencies

    def run(
        self,
        patient: dict,
        guidelines: GuidelineOutput,
        risk: RiskOutput,
    ) -> PatientOutput:
        """Run the patient agent and return patient-friendly output."""
        logger.info("[PatientAgent] Generating patient communication...")
        try:
            prompt = self._build_prompt(patient, guidelines, risk)
            response_text = self._call_llm(prompt)
            return self._parse_response(response_text)
        except Exception as e:
            logger.error("[PatientAgent] Failed: %s", e)
            return PatientOutput(
                summary="Unable to generate patient summary.",
                lifestyle_advice=[],
            )

    def _build_prompt(
        self, patient: dict, guidelines: GuidelineOutput, risk: RiskOutput
    ) -> str:
        recs = "\n".join(f"- {r}" for r in guidelines.recommendations[:4])
        return f"""You are a patient educator. A patient has the following profile:
- Age: {patient.get('age')}
- Blood pressure: {patient.get('bp')}
- LDL cholesterol: {patient.get('ldl')} mg/dL
- Conditions: {', '.join(patient.get('conditions', []))}
- Cardiovascular risk: {risk.classification} (ASCVD 10-year risk: {risk.score}%)

Clinical guidelines recommend:
{recs}

Write a SHORT, friendly explanation (2-3 sentences) the patient can understand,
then list 3-4 specific lifestyle tips.

Respond ONLY with valid JSON, no markdown:
{{"summary": "...", "lifestyle_advice": ["...", "...", "..."]}}"""

    def _call_llm(self, prompt: str) -> str:
        """Call Groq LLM API with retry logic."""
        if not self.client:
            raise RuntimeError("GROQ_API_KEY not configured")

        def _request():
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                max_tokens=400,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_SECONDS,
            )
            return response.choices[0].message.content

        return retry_with_backoff(_request, operation_name="PatientAgent/LLM")

    def _parse_response(self, text: str) -> PatientOutput:
        """Parse JSON response from LLM with content filtering."""
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
            parsed = json.loads(cleaned)
            filtered = filter_patient_output(
                parsed.get("summary", ""),
                parsed.get("lifestyle_advice", []),
                add_disclaimer=False,
            )
            return PatientOutput(
                summary=filtered["summary"],
                lifestyle_advice=filtered["lifestyle_advice"],
            )
        except json.JSONDecodeError:
            logger.warning("[PatientAgent] Could not parse JSON response.")
            filtered = filter_patient_output(text, [], add_disclaimer=False)
            return PatientOutput(summary=filtered["summary"], lifestyle_advice=[])
