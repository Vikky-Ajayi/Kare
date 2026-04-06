"""
Drug Interaction Service — 100% FREE, no API keys needed.

Uses:
  1. RxNorm API (NIH) — drug name → RxCUI lookup
  2. RxNav Interaction API (NIH) — interaction checking between drugs
  3. OpenFDA API — drug label info / additional safety data

Docs:
  RxNorm: https://rxnav.nlm.nih.gov/RxNormAPIs.html
  Interaction: https://rxnav.nlm.nih.gov/InteractionAPIs.html
  OpenFDA: https://open.fda.gov/apis/drug/
"""

import asyncio
from typing import List, Optional

import httpx

from app.config import settings


# ─────────────────────────────────────────────
# DRUG NAME → RXCUI LOOKUP
# ─────────────────────────────────────────────

async def get_rxcui(drug_name: str) -> Optional[str]:
    """
    Resolve a drug name to its RxNorm CUI (Concept Unique Identifier).
    This is needed before checking interactions.
    """
    url = f"{settings.RXNORM_BASE_URL}/rxcui.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"name": drug_name, "search": 1})

    if response.status_code != 200:
        return None

    data = response.json()
    rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]
    return rxcui


async def search_drugs(query: str) -> list:
    """
    Search for drugs by name — returns list of matches with RxCUI.
    Good for autocomplete / drug name validation.
    """
    url = f"{settings.RXNORM_BASE_URL}/drugs.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"name": query})

    if response.status_code != 200:
        return []

    data = response.json()
    drug_group = data.get("drugGroup", {}).get("conceptGroup", [])
    results = []

    for group in drug_group:
        for concept in group.get("conceptProperties", []):
            results.append({
                "rxcui": concept.get("rxcui"),
                "name": concept.get("name"),
                "tty": concept.get("tty"),    # term type (e.g. SCD = clinical drug)
                "synonyms": [],
            })

    return results[:10]   # cap at 10 results


async def get_drug_info(rxcui: str) -> dict:
    """Get detailed drug information by RxCUI."""
    url = f"{settings.RXNORM_BASE_URL}/rxcui/{rxcui}/properties.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)

    if response.status_code != 200:
        return {}

    data = response.json()
    props = data.get("properties", {})

    return {
        "rxcui": props.get("rxcui"),
        "name": props.get("name"),
        "synonym": props.get("synonym"),
        "tty": props.get("tty"),
    }


# ─────────────────────────────────────────────
# DRUG INTERACTION CHECKING
# ─────────────────────────────────────────────

async def check_interactions_by_rxcui(rxcui_list: List[str]) -> list:
    """
    Check for interactions between drugs given their RxCUI codes.
    Uses the NIH Drug Interaction API (free, no key needed).
    """
    if len(rxcui_list) < 2:
        return []

    rxcuis_str = "+".join(rxcui_list)
    url = f"{settings.RXNORM_BASE_URL}/interaction/list.json"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params={"rxcuis": rxcuis_str})

    if response.status_code != 200:
        return []

    data = response.json()
    interaction_type_groups = data.get("fullInteractionTypeGroup", [])
    interactions = []

    for group in interaction_type_groups:
        source = group.get("sourceName", "NIH")
        for interaction_type in group.get("fullInteractionType", []):
            comment = interaction_type.get("comment", "")
            for pair in interaction_type.get("interactionPair", []):
                severity = pair.get("severity", "unknown")
                description = pair.get("description", "")
                concepts = pair.get("interactionConcept", [])

                drug1 = ""
                drug2 = ""
                if len(concepts) >= 2:
                    drug1 = concepts[0].get("minConceptItem", {}).get("name", "")
                    drug2 = concepts[1].get("minConceptItem", {}).get("name", "")

                interactions.append({
                    "drug_1": drug1,
                    "drug_2": drug2,
                    "severity": severity,
                    "description": description,
                    "source": source,
                })

    return interactions


async def check_interactions_by_name(drug_names: List[str]) -> dict:
    """
    Main entry point: check interactions by drug names.
    Resolves names to RxCUI, then checks interactions.
    Returns full result with AI-friendly data.
    """
    # Step 1: Resolve all drug names to RxCUI concurrently
    rxcui_tasks = [get_rxcui(name) for name in drug_names]
    rxcui_results = await asyncio.gather(*rxcui_tasks, return_exceptions=True)

    # Build mapping of name → rxcui
    resolved = {}
    failed = []
    for name, rxcui in zip(drug_names, rxcui_results):
        if isinstance(rxcui, Exception) or rxcui is None:
            failed.append(name)
        else:
            resolved[name] = rxcui

    if len(resolved) < 2:
        return {
            "drugs_checked": drug_names,
            "resolved": resolved,
            "unresolved": failed,
            "interactions": [],
            "error": f"Could not resolve these drugs to RxCUI: {failed}" if failed else None,
        }

    # Step 2: Check interactions
    rxcui_list = list(resolved.values())
    interactions = await check_interactions_by_rxcui(rxcui_list)

    return {
        "drugs_checked": drug_names,
        "resolved": resolved,
        "unresolved": failed,
        "interactions": interactions,
        "interactions_found": len(interactions),
    }


# ─────────────────────────────────────────────
# OPENFDA — DRUG LABEL / WARNINGS
# ─────────────────────────────────────────────

async def get_drug_warnings(drug_name: str) -> dict:
    """
    Get drug warnings and adverse reactions from OpenFDA.
    Returns boxed warnings, contraindications, and adverse reactions.
    """
    url = f"{settings.OPENFDA_BASE_URL}/drug/label.json"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            url,
            params={
                "search": f'openfda.brand_name:"{drug_name}"',
                "limit": 1,
            },
        )

    if response.status_code != 200:
        return {}

    data = response.json()
    results = data.get("results", [])

    if not results:
        return {}

    label = results[0]
    return {
        "drug_name": drug_name,
        "boxed_warning": label.get("boxed_warning", [None])[0],
        "warnings": label.get("warnings", [None])[0],
        "contraindications": label.get("contraindications", [None])[0],
        "adverse_reactions": label.get("adverse_reactions", [None])[0],
        "drug_interactions": label.get("drug_interactions", [None])[0],
    }
