"""
LLM Connector Module
====================

Multi-provider LLM connector for RAG answer generation.

Providers:
    - Google Gemini (gemini-2.5-flash)          <- primary
    - OpenAI (GPT-4o-mini)
    - Anthropic (Claude)
    - Hugging Face Local (LaMini-Flan-T5)
    - Hugging Face Inference API

Prompt engineering
------------------
This module deliberately holds **no inline prompt strings**. Every prompt comes
from the versioned library in ``app/prompts`` so that:

    * prompts can be A/B tested (``app/eval``),
    * capable models use a strict-JSON *structured output* path while small
      local models fall back to delimiter parsing, and
    * all user input passes through safety **guardrails** (prompt-injection
      blocking, PII redaction) and retrieved context is fenced as untrusted
      data before it ever reaches the model.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional

import openai
import anthropic

from app.prompts.library import REGISTRY
from app.prompts.guardrails import check_user_input, wrap_untrusted_context


class LLMConfig:
    """Centralized LLM configuration."""

    # gemini-3.5-flash: latest fast model, supports JSON structured output.
    # Override with the GEMINI_MODEL env var (e.g. gemini-2.5-flash-lite for a
    # more generous free-tier quota).
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    OPENAI_MODEL = "gpt-4o-mini"  # Cost-effective default
    ANTHROPIC_MODEL = "claude-3-haiku-20240307"
    HUGGINGFACE_API_MODEL = "google/flan-t5-base"  # Publicly available, fast

    # Providers capable of reliable JSON / structured output. Small local
    # models are excluded and use the delimiter-parsed fallback instead.
    STRUCTURED_OUTPUT_PROVIDERS = {"gemini", "openai", "anthropic"}

    # Which rag_answer prompt version to use in production. v2 (few-shot) is the
    # best speed/quality/format trade-off per the eval harness; v1 and v3 remain
    # available for A/B comparison.
    DEFAULT_RAG_PROMPT_VERSION = 2


class LLMConnector:
    """Multi-provider LLM connector for RAG answer generation."""

    def __init__(self, provider: str = "gemini", rag_prompt_version: Optional[int] = None):
        self.provider = provider
        self.rag_prompt_version = rag_prompt_version or LLMConfig.DEFAULT_RAG_PROMPT_VERSION

        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")

        # Lazy-loaded clients / pipelines
        self._hf_pipeline = None
        self._gemini_model = None

        if self.provider == "huggingface_local":
            self._init_huggingface()

    def _init_huggingface(self):
        """Initialize local Hugging Face model."""
        if self._hf_pipeline is None:
            print("Initializing local Hugging Face model (LaMini-Flan-T5-248M)...")
            from transformers import pipeline
            self._hf_pipeline = pipeline(
                "text2text-generation",
                model="MBZUAI/LaMini-Flan-T5-248M",
                max_length=512,
            )

    def supports_structured_output(self) -> bool:
        return self.provider in LLMConfig.STRUCTURED_OUTPUT_PROVIDERS

    # ------------------------------------------------------------------ #
    # RAG answer generation
    # ------------------------------------------------------------------ #

    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate a grounded, cited answer.

        Pipeline: guardrail the query -> fence the retrieved context as
        untrusted data -> render the versioned rag_answer prompt -> call the
        provider -> strip any private chain-of-thought before returning.
        """
        # 1. Safety: block injection / redact PII on the user's question.
        guard = check_user_input(query)
        if guard.blocked:
            return (
                "ANSWER:\nI can't help with that request.\n\n"
                f"SOURCES:\n- (blocked: {guard.reason})"
            )

        # 2. Assemble fenced, untrusted context.
        context_text = "\n\n".join(
            f"Source: {doc['metadata'].get('source', 'Unknown')}\n"
            f"Content: {doc['content']}"
            for doc in context_docs
        )
        fenced_context = wrap_untrusted_context(context_text)

        # 3. Render the selected prompt variant from the library.
        template = REGISTRY.get("rag_answer", self.rag_prompt_version)
        system_prompt, user_prompt = template.render(
            context=fenced_context, query=guard.text
        )

        # 4. Dispatch and clean up.
        answer = self._call_provider(system_prompt, user_prompt)
        answer = self._strip_thinking(answer)
        if answer.startswith("Error"):
            return answer
        return self._clean_answer(answer)

    @staticmethod
    def _strip_thinking(text: str) -> str:
        """Remove a chain-of-thought <thinking>...</thinking> block if present."""
        return re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.S | re.I).strip()

    @staticmethod
    def _clean_answer(text: str) -> str:
        """
        Reduce the model's scaffolded output to just the answer prose.

        The prompts ask the model to reply as ``ANSWER:\\n<body>\\n\\nSOURCES:\\n- ...``.
        The UI already renders sources as dedicated cards, so we strip the
        ``ANSWER:`` label and the trailing ``SOURCES:`` block to leave a clean,
        readable answer. If the markers are absent, the text is returned as-is.
        """
        # Drop the trailing SOURCES section (citations are shown as cards).
        body = re.split(r"\n\s*SOURCES?\s*:", text, maxsplit=1, flags=re.I)[0]
        # Drop a leading "ANSWER:" label (the UI already has an "Answer" header).
        body = re.sub(r"^\s*ANSWER\s*:\s*", "", body, flags=re.I)
        return body.strip()

    def _call_provider(self, system_prompt: str, user_prompt: str) -> str:
        """Route a (system, user) prompt to the configured provider."""
        if self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        elif self.provider == "openai":
            return self._call_openai(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt)
        elif self.provider == "huggingface_local":
            return self._call_huggingface_local(system_prompt, user_prompt)
        elif self.provider == "huggingface_api":
            return self._call_huggingface_api(system_prompt, user_prompt)
        else:
            return f"Error: Invalid LLM provider '{self.provider}'."

    def _call_gemini(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Call the Google Gemini API."""
        if not self.gemini_api_key:
            return "Error: Gemini API key not found. Set GEMINI_API_KEY environment variable."

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_api_key)
            generation_config: Dict[str, Any] = {
                "temperature": 0.4,
                "max_output_tokens": 1024,
            }
            if json_mode:
                # Native structured-output mode: forces valid JSON.
                generation_config["response_mime_type"] = "application/json"

            model = genai.GenerativeModel(
                model_name=LLMConfig.GEMINI_MODEL,
                system_instruction=system_prompt or None,
                generation_config=generation_config,
            )
            response = model.generate_content(user_prompt)
            return response.text
        except Exception as e:
            return f"Error calling Gemini: {str(e)}"

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API."""
        if not self.openai_api_key:
            return "Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable."

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=LLMConfig.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API."""
        if not self.anthropic_api_key:
            return "Error: Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."

        try:
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            response = client.messages.create(
                model=LLMConfig.ANTHROPIC_MODEL,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except Exception as e:
            return f"Error calling Anthropic: {str(e)}"

    def _call_huggingface_local(self, system_prompt: str, user_prompt: str) -> str:
        """Call local Hugging Face model."""
        if self._hf_pipeline is None:
            self._init_huggingface()

        try:
            # Combine prompts for T5 models
            full_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
            response = self._hf_pipeline(full_prompt)
            return response[0]["generated_text"]
        except Exception as e:
            return f"Error with local model: {str(e)}"

    def _call_huggingface_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call Hugging Face Inference API."""
        if not self.huggingface_api_key:
            return "Error: Hugging Face API key not found. Set HUGGINGFACE_API_KEY environment variable."

        try:
            import requests

            api_url = f"https://router.huggingface.co/models/{LLMConfig.HUGGINGFACE_API_MODEL}"
            headers = {
                "Authorization": f"Bearer {self.huggingface_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "inputs": f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "return_full_text": False,
                },
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", str(result))
                elif isinstance(result, dict):
                    return result.get("generated_text", str(result))
                return str(result)
            else:
                return f"Error from Hugging Face API ({response.status_code}): {response.text}"

        except requests.exceptions.RequestException as e:
            return f"Error connecting to Hugging Face: {str(e)}"
        except Exception as e:
            return f"Error calling Hugging Face API: {str(e)}"

    # ------------------------------------------------------------------ #
    # Follow-up questions
    # ------------------------------------------------------------------ #

    def generate_follow_up_questions(self, query: str, answer: str) -> List[str]:
        """Generate follow-up questions based on the query and answer."""
        template = REGISTRY.get("follow_up")
        _, user_prompt = template.render(query=query, answer=answer)

        try:
            response = self._call_provider("", user_prompt)
            questions = [q.strip() for q in response.split("\n") if q.strip() and "?" in q]
            return questions[:3]
        except Exception as e:
            print(f"Error generating follow-up questions: {str(e)}")
            return []

    # ------------------------------------------------------------------ #
    # Document analysis (structured output where supported)
    # ------------------------------------------------------------------ #

    def analyze_document(self, text: str) -> dict:
        """
        Analyze a document -> summary, tags, complexity.

        Capable providers use the strict-JSON structured-output prompt (v2);
        small/local models fall back to the delimiter-parsed prompt (v1).
        """
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        if self.supports_structured_output():
            return self._analyze_structured(text)
        return self._analyze_delimited(text)

    def _analyze_structured(self, text: str) -> dict:
        """JSON structured-output path for capable models."""
        template = REGISTRY.get("analyze_document", 2)
        system_prompt, user_prompt = template.render(text=text)

        try:
            if self.provider == "gemini":
                raw = self._call_gemini(system_prompt, user_prompt, json_mode=True)
            else:
                raw = self._call_provider(system_prompt, user_prompt)
            data = self._parse_json_object(raw)
            return {
                "summary": data.get("summary") or "Analysis unavailable",
                "tags": data.get("tags") or ["general"],
                "complexity": self._normalize_complexity(data.get("complexity")),
            }
        except Exception as e:
            print(f"Structured analysis failed ({e}); falling back to delimited.")
            return self._analyze_delimited(text)

    def _analyze_delimited(self, text: str) -> dict:
        """Delimiter-parsed path for small/local models."""
        template = REGISTRY.get("analyze_document", 1)
        _, user_prompt = template.render(text=text)

        try:
            response = self._call_provider("", user_prompt)

            summary, tags, complexity = "", [], "intermediate"
            if "SUMMARY:" in response:
                summary = response.split("SUMMARY:")[1].split("TAGS:")[0].strip()
            if "TAGS:" in response:
                tags_section = response.split("TAGS:")[1].split("COMPLEXITY:")[0].strip()
                tags = [t.strip() for t in tags_section.split(",") if t.strip()]
            if "COMPLEXITY:" in response:
                complexity = self._normalize_complexity(
                    response.split("COMPLEXITY:")[1].strip()
                )

            return {
                "summary": summary or "Analysis unavailable",
                "tags": tags or ["general"],
                "complexity": complexity,
            }
        except Exception as e:
            print(f"Error analyzing document: {str(e)}")
            return {"summary": "Error analyzing document", "tags": [], "complexity": "intermediate"}

    @staticmethod
    def _parse_json_object(raw: str) -> dict:
        """Extract a JSON object from a model reply, tolerating stray fences."""
        raw = raw.strip()
        # Strip ```json ... ``` fences if the model added them anyway.
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
        if fence:
            raw = fence.group(1)
        else:
            brace = re.search(r"\{.*\}", raw, re.S)
            if brace:
                raw = brace.group(0)
        return json.loads(raw)

    @staticmethod
    def _normalize_complexity(value: Optional[str]) -> str:
        text = (value or "").lower()
        for level in ("beginner", "intermediate", "advanced"):
            if level in text:
                return level
        return "intermediate"

    # ------------------------------------------------------------------ #
    # Connection / metadata
    # ------------------------------------------------------------------ #

    def check_connection(self) -> dict:
        """
        Check if the LLM provider is accessible.

        IMPORTANT: this must NOT consume a generation request. On free-tier
        Gemini the generation quota is tiny (~20/day/model), so probing with a
        real prompt would exhaust the day's budget after a few status refreshes.
        For Gemini we list models instead (a separate, cheap quota); for other
        providers we fall back to a lightweight generation probe.
        """
        model_name = self._model_name()
        try:
            if self.provider == "gemini":
                ok, details = self._gemini_healthcheck()
                status = "connected" if ok else "disconnected"
                return {"status": status, "model": model_name, "details": details}

            test_response = self._call_provider("", "Say 'OK' if you can read this.")
            if "Error" in test_response:
                return {"status": "disconnected", "model": model_name, "details": test_response}
            return {"status": "connected", "model": model_name, "details": "Connection successful"}
        except Exception as e:
            return {"status": "disconnected", "model": model_name, "details": str(e)}

    def _gemini_healthcheck(self) -> tuple[bool, str]:
        """Verify Gemini is reachable without spending a generation request."""
        if not self.gemini_api_key:
            return False, "Gemini API key not found. Set GEMINI_API_KEY."
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_api_key)
            # Listing models validates the key + connectivity on a quota that is
            # separate from (and far larger than) the generateContent quota.
            next(iter(genai.list_models()))
            return True, "Connection successful"
        except Exception as e:
            return False, f"Error reaching Gemini: {str(e)}"

    def _model_name(self) -> Optional[str]:
        return {
            "gemini": LLMConfig.GEMINI_MODEL,
            "openai": LLMConfig.OPENAI_MODEL,
            "anthropic": LLMConfig.ANTHROPIC_MODEL,
            "huggingface_api": LLMConfig.HUGGINGFACE_API_MODEL,
            "huggingface_local": "LaMini-Flan-T5-248M",
        }.get(self.provider)

    @staticmethod
    def get_available_providers() -> List[str]:
        """Return list of available LLM providers."""
        return [
            "gemini",
            "openai",
            "anthropic",
            "huggingface_local",
            "huggingface_api",
        ]
