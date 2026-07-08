"""Scene-aware retrieval strategy routing with lightweight memory lookup."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


QUESTION_PATTERNS = {
    "definition": re.compile(r"\b(define|what is|what are|meaning of|stands for)\b", re.I),
    "comparison": re.compile(r"\b(compare|difference|differentiate|versus|vs\.?|contrast)\b", re.I),
    "procedure": re.compile(r"\b(how should|procedure|workflow|steps|commission|acceptance|qa program|programme)\b", re.I),
    "calculation": re.compile(r"\b(calculate|derive|formula|equation|constant|half-life|output factor|monitor unit|mu)\b", re.I),
    "table_or_figure": re.compile(r"\b(table|figure|chart|diagram|image|appendix)\b", re.I),
}

DOMAIN_TERMS = {
    "dosimetry": {
        "dosimetry", "dose", "absorbed", "calibration", "ionization", "chamber",
        "output factor", "small field", "brachytherapy", "reference dosimeter",
    },
    "quality_management": {
        "quality", "qa", "qc", "fmea", "risk", "audit", "chart review",
        "process map", "failure mode", "tolerance", "safety",
    },
    "imaging_guidance": {
        "igrt", "image", "imaging", "ct", "cbct", "registration", "localization",
        "surface guided", "setup", "fusion",
    },
    "treatment_planning": {
        "treatment planning", "tps", "commissioning", "beam model", "imrt",
        "vmat", "dose calculation", "monitor unit", "plan review",
    },
    "equipment": {
        "linac", "accelerator", "equipment", "machine", "record and verify",
        "mlc", "epid", "tomotherapy",
    },
    "facility_safety": {
        "facility", "shielding", "room", "radiation protection", "staffing",
        "programme", "infrastructure",
    },
}

OOD_TERMS = {
    "bread", "crypto", "municipal", "portfolio", "dental", "antibiotic",
    "stock", "recipe", "weather", "legal", "tax",
    "sourdough", "python", "web framework", "finance", "dashboard",
    "filing", "proprietorship", "california", "violin", "violinist",
    "baroque", "ornamentation", "soil", "blueberries", "garden",
    "chess", "opening", "kitchen", "faucet", "cartridge", "kyoto",
    "itinerary", "marathon", "knee injury", "camera", "lens",
    "photography", "mortgage", "refinance", "mold", "bathroom",
    "grout", "jazz", "piano", "voicings", "wi-fi", "wifi",
    "packet loss", "home network", "flour", "neapolitan", "pizza",
    "dough",
}


@dataclass
class RoutingDecision:
    strategy: str
    backend: str
    reason: str
    evidence_top_k: int | None = None
    memory_match_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "backend": self.backend,
            "reason": self.reason,
            "evidence_top_k": self.evidence_top_k,
            "memory_match_count": self.memory_match_count,
        }


def _contains_any(query_l: str, terms: Iterable[str]) -> bool:
    return any(term in query_l for term in terms)


def analyze_scene(query: str, report_id: str | None = None) -> dict[str, Any]:
    """Build a compact, serializable scene representation for routing."""
    query_l = query.lower()
    domain_tags = [
        tag for tag, terms in DOMAIN_TERMS.items()
        if _contains_any(query_l, terms)
    ]
    matched_patterns = [
        name for name, pattern in QUESTION_PATTERNS.items()
        if pattern.search(query)
    ]

    if _contains_any(query_l, OOD_TERMS) and not domain_tags:
        task_type = "out_of_scope"
    elif "table_or_figure" in matched_patterns:
        task_type = "asset_lookup"
    elif "calculation" in matched_patterns:
        task_type = "calculation_or_formula"
    elif "definition" in matched_patterns:
        task_type = "definition"
    elif "comparison" in matched_patterns:
        task_type = "comparison"
    elif "procedure" in matched_patterns:
        task_type = "procedure_or_qa"
    elif len(domain_tags) >= 2 or re.search(r"\b(across|between|multiple|several|overall)\b", query_l):
        task_type = "multi_report_synthesis"
    else:
        task_type = "direct_fact"

    complexity = "low"
    if task_type in {"comparison", "multi_report_synthesis", "procedure_or_qa"}:
        complexity = "medium"
    if len(query.split()) >= 22 or len(domain_tags) >= 3:
        complexity = "high"

    return {
        "task_type": task_type,
        "domain_tags": domain_tags,
        "matched_patterns": matched_patterns,
        "has_report_scope": bool(report_id),
        "query_length_tokens": len(query.split()),
        "complexity": complexity,
        "query_style": "question" if "?" in query else "instruction",
    }


def load_experience_memory(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def find_memory_matches(scene: dict[str, Any], records: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """Return prior records with the same task type and overlapping domain tags."""
    scene_tags = set(scene.get("domain_tags") or [])
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in records:
        past_scene = record.get("scene_features") or {}
        score = 0
        if past_scene.get("task_type") == scene.get("task_type"):
            score += 2
        past_tags = set(past_scene.get("domain_tags") or [])
        score += len(scene_tags & past_tags)
        if score > 0 and record.get("evidence_status") == "sufficient":
            scored.append((score, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [record for _, record in scored[:limit]]


def select_retrieval_strategy(
    scene: dict[str, Any],
    dense_available: bool,
    memory_matches: list[dict[str, Any]] | None = None,
) -> RoutingDecision:
    """Choose a retrieval strategy under a stable agent-facing interface."""
    memory_matches = memory_matches or []
    for record in memory_matches:
        strategy = record.get("strategy_used")
        backend = record.get("retrieval_backend")
        if strategy and backend in {"sparse", "hybrid"}:
            return RoutingDecision(
                strategy=strategy,
                backend=backend if dense_available or backend == "sparse" else "sparse",
                reason="Reused a successful prior strategy for a similar scene.",
                evidence_top_k=record.get("evidence_top_k"),
                memory_match_count=len(memory_matches),
            )

    task_type = scene.get("task_type")
    if task_type == "out_of_scope":
        return RoutingDecision("ood_sparse_probe", "sparse", "Probe cheaply before abstention.", evidence_top_k=3)
    if scene.get("has_report_scope"):
        return RoutingDecision("scoped_sparse", "sparse", "Report scope is explicit; lexical matching is reliable.", evidence_top_k=6)
    if task_type == "definition":
        return RoutingDecision("definition_sparse_microchunk", "sparse", "Definition queries benefit from lexical cues and definition microchunks.", evidence_top_k=5)
    if task_type == "asset_lookup":
        return RoutingDecision("asset_aware_sparse", "sparse", "Table or figure cue detected; retrieve text evidence and surface asset-aware trace.", evidence_top_k=8)
    if task_type in {"comparison", "multi_report_synthesis", "procedure_or_qa"}:
        if dense_available:
            return RoutingDecision("hybrid_rrf_synthesis", "hybrid", "Synthesis queries benefit from dense plus lexical fusion.", evidence_top_k=8)
        return RoutingDecision("broad_sparse_synthesis", "sparse", "Dense index is unavailable; use broader sparse evidence for synthesis.", evidence_top_k=8)
    if task_type == "calculation_or_formula":
        return RoutingDecision("formula_sparse", "sparse", "Formula and calculation queries need exact lexical terms.", evidence_top_k=6)
    if dense_available:
        return RoutingDecision("hybrid_direct", "hybrid", "Dense index is available for direct fact lookup.", evidence_top_k=5)
    return RoutingDecision("sparse_direct", "sparse", "Portable sparse backend is available.", evidence_top_k=5)


def append_experience_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(record)
    payload.setdefault("timestamp_utc", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
