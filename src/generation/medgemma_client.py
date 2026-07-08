"""Minimal local Hugging Face client for MedGemma-style generation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class MedGemmaClient:
    """Load a local instruction-tuned model and generate structured output.

    This client is intentionally generic. You can point it at a MedGemma model
    path or Hugging Face model ID through the configuration.
    """

    def __init__(self, model_name_or_path: str, max_new_tokens: int = 512):
        if not model_name_or_path:
            raise ValueError(
                "MEDGEMMA_MODEL_NAME_OR_PATH is empty. Please set it before running the answer stage."
            )
        self.model_name_or_path = model_name_or_path
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            device_map="auto",
            torch_dtype="auto",
        )
        self.generator = pipeline(
            task="text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        outputs = self.generator(
            prompt,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            return_full_text=False,
        )
        text = outputs[0]["generated_text"].strip()
        return self._extract_json(text)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"Model output did not contain JSON. Output was:\n{text}")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to parse model JSON output: {exc}\nRaw text:\n{text}"
            ) from exc
