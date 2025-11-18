# ai_models/llm_evaluation/ai_wrapper.py

import google.generativeai as genai
# 🌟 FIX: Use the modern, stable import path from langchain_core
from langchain_core.language_models.llms import LLM 
from pydantic import BaseModel
from typing import Optional, List, Mapping, Any

class GeminiLC(LLM, BaseModel):
    """Tiny LangChain wrapper around google-generativeai for text-only operations."""
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.0

    @property
    def _llm_type(self) -> str:
        return "gemini_langchain_wrapper"

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature
        }

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        # Note: This simple wrapper only handles text prompts.
        model = genai.GenerativeModel(self.model_name)
        resp = model.generate_content(prompt)
        return (
            getattr(resp, "text", None)
            or getattr(resp, "output_text", None)
            or str(resp)
        )
