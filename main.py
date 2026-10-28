#!/usr/bin/env python3
"""MCP server: mcp-frcompliance - Francophone Web3 Compliance (FR/EN).

Bilingual FR/EN compliance retainer:

  * weekly MiCA digest (EU-level, with the articles that actually changed);
  * AMF national-level interpretation - France-specific positions and
    enforcement signals, explicitly NOT translated EU news;
  * KYC/AML documentation cycles generated as real, structured documents;
  * a French legal annex with per-right enumeration and droit moral handling;
  * compliance deadlines computed from seeded regulation dates;
  * glossary-assisted legal translation with a full audit trail.

The domain content lives in `content.py`; the bilingual legal term engine
lives in `glossary.py`. Both are real implementations, not stubs.
"""

from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from content import (
    AMF_INTERPRETATIONS,
    COMPLIANCE_DEADLINES,
    FRENCH_LEGAL_ANNEXES,
    KYC_DOCUMENTS,
    MICA_DIGESTS,
    REFERENCE_DATE,
    SERVICE_PLAN,
)
from glossary import translate_text

SERVICE_NAME = "mcp-frcompliance"
VERSION = "1.0.0"

app = Server(SERVICE_NAME)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _error(tool: str, message: str, **extra: Any) -> list[TextContent]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return [TextContent(type="text", text=json.dumps(payload, indent=2, ensure_ascii=False))]


def _ok(tool: str, **fields: Any) -> list[TextContent]:
    payload = {"status": "ok", "tool": tool, "service": SERVICE_NAME, "version": VERSION}
    payload.update(fields)
    return [TextContent(type="text", text=json.dumps(payload, indent=2, ensure_ascii=False))]


def _parse_date(value: str) -> date:
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def _localized(entry: dict[str, Any], language: str, *keys: str) -> dict[str, Any]:
    """Build a language-specific view of a bilingual content entry."""
    lang = language.lower()
    out: dict[str, Any] = {}
    for key in keys:
        if f"{key}_{lang}" in entry:
            out[key] = entry[f"{key}_{lang}"]
        elif key in entry:
            out[key] = entry[key]
    return out


def _reference_date() -> date:
    return REFERENCE_DATE


# --------------------------------------------------------------------------
# Tool definitions
# --------------------------------------------------------------------------

TOOLS: list[Tool] = [
    Tool(
        name="get_mica_digest",
        description=(
            "Return the MiCA regulatory digest in French or English: dated entries covering the "
            "articles that changed, with key changes, effective dates and EUR-Lex citations, "
            "filtered to a look-back window."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["fr", "en"],
                    "default": "fr",
                    "description": "Digest language.",
                },
                "weeks_back": {
                    "type": "integer",
                    "default": 4,
                    "minimum": 1,
                    "maximum": 520,
                    "description": "How many weeks of history to include.",
                },
                "topic": {
                    "type": "string",
                    "description": "Optional topic filter (stablecoin, CASP, ART, market abuse...).",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="get_amf_interpretation",
        description=(
            "Return AMF (Autorite des marches financiers) France-specific interpretations and "
            "enforcement positions, with the reference number, date, enforcement signals and an "
            "explicit France-specific marker distinguishing them from translated EU news."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic filter (staking, custody, PSAN, MiCA, marketing...).",
                },
                "language": {
                    "type": "string",
                    "enum": ["fr", "en"],
                    "default": "fr",
                    "description": "Response language.",
                },
                "enforcement_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return only positions that carry an enforcement signal.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="generate_kyc_doc",
        description=(
            "Generate a structured KYC/AML document for an individual or an entity: document "
            "sections, required identity documents, beneficial-owner declaration, source-of-funds "
            "thresholds, PEP and sanctions screening steps, retention rules and signature blocks, "
            "in the requested language."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "enum": ["individual", "entity"],
                    "description": "Whether the customer is a natural person or a legal entity.",
                },
                "language": {
                    "type": "string",
                    "enum": ["fr", "en"],
                    "default": "fr",
                    "description": "Document language.",
                },
                "jurisdiction": {
                    "type": "string",
                    "default": "France",
                    "description": "Jurisdiction whose rules apply.",
                },
                "risk_profile": {
                    "type": "string",
                    "enum": ["standard", "elevated", "high"],
                    "default": "standard",
                    "description": "Risk band, which drives the enhanced measures applied.",
                },
                "service": {
                    "type": "string",
                    "description": "Optional service being onboarded (e.g. token_issuance, custody).",
                },
            },
            "required": ["entity_type"],
        },
    ),
    Tool(
        name="get_french_legal_annex",
        description=(
            "Return a French legal annex for a token operation: per-right enumeration including "
            "droit moral (moral rights are perpetual and inalienable in French law and are "
            "therefore never assigned), governing law, jurisdiction, MiCA/AMF article references, "
            "and the two-column IP exit-rights table."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "operation_type": {
                    "type": "string",
                    "enum": ["token_issuance", "custody", "trading"],
                    "description": "The operation the annex covers.",
                },
                "language": {
                    "type": "string",
                    "enum": ["fr", "en"],
                    "default": "fr",
                    "description": "Annex language.",
                },
            },
            "required": ["operation_type"],
        },
    ),
    Tool(
        name="get_compliance_deadlines",
        description=(
            "Compute compliance deadlines for a jurisdiction as of a given date: days remaining, "
            "status (upcoming / due / overdue), the regulation behind each deadline, and the "
            "France-specific entries."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "jurisdiction": {
                    "type": "string",
                    "default": "France",
                    "description": "Jurisdiction whose calendar applies.",
                },
                "as_of": {
                    "type": "string",
                    "description": "ISO date (YYYY-MM-DD) to compute from; defaults to today.",
                },
                "include_overdue": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include deadlines already passed.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="translate_legal_doc",
        description=(
            "Translate a legal document between French and English using a curated bilingual "
            "regulatory glossary. Legal citations and numbers are preserved verbatim; every "
            "applied term is reported; terms with no glossary entry are flagged as requiring a "
            "certified translator."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate."},
                "source_lang": {
                    "type": "string",
                    "enum": ["fr", "en"],
                    "description": "Source language.",
                },
                "target_lang": {
                    "type": "string",
                    "enum": ["fr", "en"],
                    "description": "Target language.",
                },
                "domain": {
                    "type": "string",
                    "default": "regulatory",
                    "description": "Domain context (regulatory, aml, contract, technical).",
                },
            },
            "required": ["text", "source_lang", "target_lang"],
        },
    ),
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    arguments = arguments or {}

    if name == "get_mica_digest":
        language = (arguments.get("language") or "fr").lower()
        weeks_back = int(arguments.get("weeks_back", 4))
        topic = (arguments.get("topic") or "").strip().lower()
        reference = _reference_date()
        cutoff = reference - timedelta(weeks=weeks_back)

        entries = []
        for digest in MICA_DIGESTS:
            published = _parse_date(digest["date"])
            if published < cutoff or published > reference:
                continue
            if topic and topic not in digest["topics"] and topic not in digest["title_en"].lower():
                continue
            entries.append(
                {
                    "id": digest["id"],
                    "date": digest["date"],
                    **_localized(digest, language, "title", "summary", "key_changes"),
                    "articles": digest["articles"],
                    "source_urls": digest["source_urls"],
                    "topics": digest["topics"],
                }
            )
        entries.sort(key=lambda item: item["date"], reverse=True)
        return _ok(
            name,
            language=language,
            weeks_back=weeks_back,
            as_of=reference.isoformat(),
            window_start=cutoff.isoformat(),
            count=len(entries),
            filter_topic=topic or None,
            digests=entries,
            subscription=SERVICE_PLAN,
        )

    if name == "get_amf_interpretation":
        topic = (arguments.get("topic") or "").strip().lower()
        language = (arguments.get("language") or "fr").lower()
        enforcement_only = bool(arguments.get("enforcement_only", False))

        scored: list[tuple[int, dict[str, Any]]] = []
        for position in AMF_INTERPRETATIONS:
            if enforcement_only and not position.get("enforcement"):
                continue
            haystacks = [
                position.get("title_fr", ""),
                position.get("title_en", ""),
                position.get("summary_fr", ""),
                position.get("summary_en", ""),
                " ".join(position.get("topics", [])),
            ]
            haystack = " ".join(haystacks).lower()
            if not topic:
                score = 1
            else:
                score = 0
                for token in topic.replace(",", " ").split():
                    if token in haystack:
                        score += 2
                    for tagged in position.get("topics", []):
                        if token == tagged.lower() or token in tagged.lower():
                            score += 3
            if score:
                scored.append((score, position))
        scored.sort(key=lambda item: (-item[0], item[1]["date"]), reverse=False)
        scored.sort(key=lambda item: item[1]["date"], reverse=True)

        results = []
        for score, position in scored:
            results.append(
                {
                    "id": position["id"],
                    "reference": position["reference"],
                    "date": position["date"],
                    "relevance_score": score,
                    **_localized(position, language, "title", "summary", "details"),
                    "topics": position["topics"],
                    "enforcement_signal": position.get("enforcement", False),
                    "sanction_examples": position.get("sanctions", []),
                    "france_specific": True,
                    "source_type": "AMF national position (France)",
                    "not_translated_eu_news": (
                        "France-specific AMF position with its own reference number; this is not "
                        "a translation of EU-level news."
                    ),
                    "source_urls": position.get("source_urls", []),
                }
            )
        return _ok(
            name,
            language=language,
            topic=topic or None,
            enforcement_only=enforcement_only,
            count=len(results),
            interpretations=results,
            coverage_note=(
                "AMF positions are authored at the national level for France; they may be "
                "stricter than, or add to, the corresponding EU text."
            ),
        )

    if name == "generate_kyc_doc":
        entity_type = (arguments.get("entity_type") or "").lower()
        if entity_type not in ("individual", "entity"):
            return _error(
                name,
                f"entity_type must be 'individual' or 'entity', got {entity_type!r}",
                valid=["individual", "entity"],
            )
        language = (arguments.get("language") or "fr").lower()
        jurisdiction = arguments.get("jurisdiction") or "France"
        risk_profile = (arguments.get("risk_profile") or "standard").lower()
        service = arguments.get("service")

        key = f"{entity_type}_{language}"
        template = KYC_DOCUMENTS.get(key) or KYC_DOCUMENTS[f"{entity_type}_fr"]
        risk = _localized(template, language, "risk_measures")
        measures = list(risk.get(risk_profile, risk.get("standard", [])))

        sections = []
        for section in template["sections"]:
            sections.append(
                {
                    "id": section["id"],
                    "number": section["number"],
                    **_localized(section, language, "title", "body"),
                    "fields": section.get("fields", []),
                }
            )

        retention = next(
            (entry for entry in COMPLIANCE_DEADLINES if entry["id"] == "retention-records"),
            None,
        )
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return _ok(
            name,
            document={
                "title": template["title"][language],
                "entity_type": entity_type,
                "language": language,
                "jurisdiction": jurisdiction,
                "risk_profile": risk_profile,
                "service_onboarded": service,
                "reference": f"KYC-{entity_type.upper()}-{jurisdiction[:2].upper()}-"
                f"{generated_at[:10].replace('-', '')}",
                "generated_at": generated_at,
                "sections": sections,
                "required_documents": template["required_documents"],
                "screening_steps": template["screening_steps"],
                "risk_measures_applied": measures,
                "retention_rule": {
                    "retention_period": template["retention_period"],
                    "basis": template["retention_basis"],
                    "trigger": retention["label"] if retention else "MiCA accounting-records rule",
                },
                "signature_blocks": template["signature_blocks"],
                "declaration": template["declaration"][language],
            },
            count_sections=len(sections),
            required_document_count=len(template["required_documents"]),
            next_steps=[
                "Collect the required identity documents listed above.",
                "Complete screening (sanctions, PEP, adverse media) before account activation.",
                "Run the source-of-funds threshold test for the declared risk profile.",
                "Sign the declaration; a signed KYC pack is the audit trail's first entry.",
            ],
        )

    if name == "get_french_legal_annex":
        operation_type = (arguments.get("operation_type") or "").lower()
        if operation_type not in FRENCH_LEGAL_ANNEXES:
            return _error(
                name,
                f"unknown operation_type {operation_type!r}",
                valid=sorted(FRENCH_LEGAL_ANNEXES),
            )
        language = (arguments.get("language") or "fr").lower()
        annex = FRENCH_LEGAL_ANNEXES[operation_type]

        rights = []
        for right in annex["rights"]:
            rights.append(
                {
                    "id": right["id"],
                    **_localized(right, language, "label", "description"),
                    "category": right["category"],
                    "assignable": right["assignable"],
                    "term": right["term"],
                    "assignment_clause": right["assignment_clause"][language],
                }
            )

        exit_rights = annex["exit_rights"]
        ip_table = [
            {
                "artifact": _localized(item, language, "artifact"),
                "leaves_with_customer": item["leaves_with_customer"],
                "stays_with_provider": item["stays_with_provider"],
            }
            for item in exit_rights
        ]

        return _ok(
            name,
            operation_type=operation_type,
            language=language,
            title=annex["title"][language],
            preamble=annex["preamble"][language],
            rights=rights,
            moral_rights_handling={
                "summary": annex["moral_rights_summary"][language],
                "rule": (
                    "Under the French Code de la propriete intellectuelle (Art. L121-1), moral "
                    "rights are perpetual, inalienable and cannot be assigned or waived. The annex "
                    "therefore enumerates each right individually: economic rights may be "
                    "licensed or assigned, moral rights may only be exercised and waived as to "
                    "specific future works in a narrowly drawn, non-assignable instrument."
                ),
                "assignable": False,
                "perpetual": True,
            },
            governing_law=annex["governing_law"][language],
            jurisdiction=annex["jurisdiction"][language],
            dispute_resolution=annex["dispute_resolution"][language],
            regulatory_references=annex["regulatory_references"],
            ip_exit_rights_table=ip_table,
            signature=annex["signature"][language],
        )

    if name == "get_compliance_deadlines":
        jurisdiction = arguments.get("jurisdiction") or "France"
        as_of_raw = arguments.get("as_of")
        if as_of_raw:
            try:
                as_of = _parse_date(as_of_raw)
            except ValueError:
                return _error(
                    name,
                    f"could not parse as_of {as_of_raw!r}",
                    expected="YYYY-MM-DD",
                )
        else:
            as_of = datetime.now(timezone.utc).date()
        include_overdue = bool(arguments.get("include_overdue", True))

        entries = []
        for deadline in COMPLIANCE_DEADLINES:
            if jurisdiction.lower() not in [j.lower() for j in deadline["jurisdictions"]]:
                continue
            due = _parse_date(deadline["due_date"])
            days_remaining = (due - as_of).days
            if days_remaining < 0:
                status = "overdue"
            elif days_remaining <= 30:
                status = "due"
            elif days_remaining <= 90:
                status = "upcoming_90d"
            else:
                status = "upcoming"
            if status == "overdue" and not include_overdue:
                continue
            entries.append(
                {
                    "id": deadline["id"],
                    "label": deadline["label"],
                    "regulation": deadline["regulation"],
                    "due_date": deadline["due_date"],
                    "days_remaining": days_remaining,
                    "status": status,
                    "jurisdictions": deadline["jurisdictions"],
                    "owner": deadline["owner"],
                    "recurring": deadline.get("recurring", False),
                    "source_urls": deadline.get("source_urls", []),
                }
            )
        entries.sort(key=lambda item: item["days_remaining"])

        france = [e for e in entries if "France" in e["jurisdictions"]]
        overdue = [e for e in entries if e["status"] == "overdue"]
        due_soon = [e for e in entries if e["status"] == "due"]
        return _ok(
            name,
            jurisdiction=jurisdiction,
            as_of=as_of.isoformat(),
            count=len(entries),
            france_specific_count=len(france),
            overdue_count=len(overdue),
            due_soon_count=len(due_soon),
            deadlines=entries,
            summary={
                "next_deadline": entries[0] if entries else None,
                "overdue": overdue,
                "due_within_30_days": due_soon,
            },
        )

    if name == "translate_legal_doc":
        text = arguments.get("text")
        if not isinstance(text, str) or not text.strip():
            return _error(name, "text is required and must be a non-empty string")
        source_lang = (arguments.get("source_lang") or "").lower()
        target_lang = (arguments.get("target_lang") or "").lower()
        if source_lang not in ("fr", "en") or target_lang not in ("fr", "en"):
            return _error(
                name,
                "source_lang and target_lang must each be 'fr' or 'en'",
                valid=["fr", "en"],
            )
        domain = arguments.get("domain") or "regulatory"

        result = translate_text(text, source_lang, target_lang)
        return _ok(
            name,
            source_lang=source_lang,
            target_lang=target_lang,
            domain=domain,
            original=text,
            translated=result["translated"],
            same_language=result.get("same_language", False),
            terms_applied=result["terms_applied"],
            terms_applied_count=len(result["terms_applied"]),
            protected_spans=result["protected_spans"],
            untranslated_terms=result["untranslated_terms"],
            requires_certified_translator=result["requires_certified_translator"],
            disclaimer=(
                "Glossary-assisted translation produced by the platform's bilingual regulatory "
                "term engine. It preserves legal citations and figures verbatim and reports "
                "every term it substituted, but it is NOT a certified legal translation. "
                "Terms flagged as untranslated, and any document that will be signed or filed, "
                "require review by a certified translator or French-qualified counsel."
            ),
        )

    return _error(name, f"unknown tool {name!r}", available=[t.name for t in TOOLS])


async def _main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(_main())
