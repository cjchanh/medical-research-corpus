#!/usr/bin/env python3
"""Record-authority tiers — the evidence hierarchy used to re-rank retrieval.

Lower tier number = stronger evidence. Mirrors the principle that a systematic
review outranks a case report, and a peer-reviewed article outranks a preprint —
so a clean-but-weak source never beats a strong one on relevance score alone.
"""
from __future__ import annotations


def authority_tier(doc: dict) -> tuple[int, str]:
    # EPMC pub_type is coarse; study design usually lives in the title. Scan both.
    sig = ((doc.get("pub_type") or "") + " " + (doc.get("title") or "")).lower()
    if doc.get("is_trial"):
        return (4, "trial-registry")
    if doc.get("is_preprint"):
        return (5, "preprint")
    if "meta-analysis" in sig or "systematic review" in sig:
        return (1, "systematic-review")
    if "randomized" in sig or "randomised" in sig or "clinical trial" in sig:
        return (2, "RCT/trial")
    if "scoping review" in sig:
        return (2, "scoping-review")
    if "case report" in sig or "case series" in sig:
        return (4, "case-report")
    if "cohort" in sig or "observational" in sig:
        return (3, "cohort/observational")
    if "review" in sig:
        return (3, "review")
    return (3, "research-article")
