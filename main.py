#!/usr/bin/env python3
"""MCP server for frcompliance - Francophone Web3 Compliance (FR/EN)"""

import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("mcp-frcompliance")

# Simulated data
MICA_DIGESTS = [
    {
        "id": "mica-2024-12",
        "title": "MiCA Digest - December 2024",
        "language": "fr",
        "summary": "Nouveaux seuils pour les stablecoins, exigences de réserve mises à jour",
        "key_changes": [
            "Seuil de 200M EUR pour les stablecoins significatifs",
            "Exigences de réserve: 1:1 pour les asset-referenced tokens",
            "Rapport trimestriel obligatoire pour les émetteurs > 50M EUR"
        ],
        "effective_date": "2025-01-01",
        "source_urls": ["https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32023R1114"]
    },
    {
        "id": "mica-2024-11",
        "title": "MiCA Digest - November 2024",
        "language": "en",
        "summary": "Updated stablecoin thresholds, reserve requirements revised",
        "key_changes": [
            "€200M threshold for significant stablecoins",
            "1:1 reserve requirements for asset-referenced tokens",
            "Quarterly reporting mandatory for issuers > €50M"
        ],
        "effective_date": "2025-01-01",
        "source_urls": ["https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1114"]
    }
]

AMF_INTERPRETATIONS = [
    {
        "id": "amf-2024-001",
        "title": "Position AMF sur le staking en tant que service",
        "reference": "DOC-2024-08",
        "summary": "Le staking non-custodial ne constitue pas un service d'investissement",
        "details": "L'AMF considère que le staking non-custodial où l'utilisateur garde le contrôle de ses clés ne relève pas du régime des PSAN.",
        "language": "fr",
        "date": "2024-10-15",
        "status": "active"
    },
    {
        "id": "amf-2024-002",
        "title": "AMF Position on Staking as a Service",
        "reference": "DOC-2024-08-EN",
        "summary": "Non-custodial staking does not constitute an investment service",
        "details": "The AMF considers that non-custodial staking where users retain key control does not fall under the PSAN regime.",
        "language": "en",
        "date": "2024-10-15",
        "status": "active"
    }
]

KYC_TEMPLATES = {
    "individual_fr": {
        "sections": ["identité", "adresse", "source_fonds", "déclaration_fiscale", "signature"],
        "required_docs": ["passeport", "justificatif_domicile", "relevé_bancaire", "avis_imposition"]
    },
    "individual_en": {
        "sections": ["identity", "address", "source_of_funds", "tax_declaration", "signature"],
        "required_docs": ["passport", "proof_of_address", "bank_statement", "tax_return"]
    },
    "entity_fr": {
        "sections": ["identité_entité", "bénéficiaires_effectifs", "structure_actionnariale", "activité", "signature"],
        "required_docs": ["kbis", "statuts", "registre_bénéficiaires", "organigramme", "procuration"]
    },
    "entity_en": {
        "sections": ["entity_identity", "beneficial_owners", "shareholder_structure", "activity", "signature"],
        "required_docs": ["certificate_incorporation", "bylaws", "beneficial_owners_register", "org_chart", "power_of_attorney"]
    }
}

FRENCH_LEGAL_ANNEXES = {
    "token_issuance_fr": {
        "title": "Annexe Juridique - Émission de Token (France)",
        "clauses": [
            "Conformité MiCA Article 16-23",
            "Déclaration AMF préalable obligatoire",
            "Prospectus allégé si < 8M EUR",
            "Droits des investisseurs: rétractation 14 jours",
            "Responsabilité des dirigeants: solidaire"
        ],
        "jurisdiction": "France",
        "language": "fr"
    },
    "token_issuance_en": {
        "title": "Legal Annex - Token Issuance (France)",
        "clauses": [
            "MiCA Articles 16-23 Compliance",
            "Prior AMF Notification Required",
            "Light Prospectus if < €8M",
            "Investor Rights: 14-day Withdrawal",
            "Director Liability: Joint & Several"
        ],
        "jurisdiction": "France",
        "language": "en"
    }
}

app = Server("mcp-frcompliance")

TOOLS = [
    Tool(
        name="get_mica_digest",
        description="Get MiCA regulatory digest (FR/EN)",
        inputSchema={
            "type": "object",
            "properties": {
                "language": {"type": "string", "enum": ["fr", "en"], "default": "fr", "description": "Language"},
                "months_back": {"type": "integer", "default": 3, "description": "Months of history"}
            }
        }
    ),
    Tool(
        name="get_amf_interpretation",
        description="Get AMF regulatory interpretation",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic (staking, custody, trading, etc.)"},
                "language": {"type": "string", "enum": ["fr", "en"], "default": "fr"}
            }
        }
    ),
    Tool(
        name="generate_kyc_doc",
        description="Generate KYC documentation template",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_type": {"type": "string", "enum": ["individual", "entity"], "description": "Individual or entity"},
                "language": {"type": "string", "enum": ["fr", "en"], "default": "fr"},
                "jurisdiction": {"type": "string", "default": "France", "description": "Jurisdiction"}
            },
            "required": ["entity_type"]
        }
    ),
    Tool(
        name="get_french_legal_annex",
        description="Get French legal annex for token operations",
        inputSchema={
            "type": "object",
            "properties": {
                "operation_type": {"type": "string", "description": "Operation type (token_issuance, custody, trading)"},
                "language": {"type": "string", "enum": ["fr", "en"], "default": "fr"}
            },
            "required": ["operation_type"]
        }
    ),
    Tool(
        name="translate_legal_doc",
        description="Translate legal document between FR/EN",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "source_lang": {"type": "string", "enum": ["fr", "en"], "description": "Source language"},
                "target_lang": {"type": "string", "enum": ["fr", "en"], "description": "Target language"},
                "domain": {"type": "string", "default": "regulatory", "description": "Domain context"}
            },
            "required": ["text", "source_lang", "target_lang"]
        }
    )
]

@app.list_tools()
async def list_tools():
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_mica_digest":
        language = arguments.get("language", "fr")
        months_back = arguments.get("months_back", 3)
        
        digests = [d for d in MICA_DIGESTS if d["language"] == language]
        
        result = {
            "status": "ok",
            "tool": "get_mica_digest",
            "language": language,
            "months_back": months_back,
            "count": len(digests),
            "digests": digests
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_amf_interpretation":
        topic = arguments.get("topic", "").lower()
        language = arguments.get("language", "fr")
        
        interpretations = [i for i in AMF_INTERPRETATIONS if i["language"] == language]
        if topic:
            interpretations = [i for i in interpretations if topic in i["title"].lower() or topic in i["summary"].lower()]
        
        result = {
            "status": "ok",
            "tool": "get_amf_interpretation",
            "topic": topic,
            "language": language,
            "count": len(interpretations),
            "interpretations": interpretations
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "generate_kyc_doc":
        entity_type = arguments.get("entity_type")
        language = arguments.get("language", "fr")
        jurisdiction = arguments.get("jurisdiction", "France")
        
        template_key = f"{entity_type}_{language}"
        template = KYC_TEMPLATES.get(template_key, KYC_TEMPLATES.get(f"individual_{language}"))
        
        result = {
            "status": "ok",
            "tool": "generate_kyc_doc",
            "entity_type": entity_type,
            "language": language,
            "jurisdiction": jurisdiction,
            "template": template,
            "generated_at": datetime.now().isoformat()
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_french_legal_annex":
        operation_type = arguments.get("operation_type")
        language = arguments.get("language", "fr")
        
        annex_key = f"{operation_type}_{language}"
        annex = FRENCH_LEGAL_ANNEXES.get(annex_key)
        
        if not annex:
            return [TextContent(type="text", text=json.dumps({"error": f"Annex not found for {operation_type} in {language}"}))]
        
        result = {
            "status": "ok",
            "tool": "get_french_legal_annex",
            "operation_type": operation_type,
            "language": language,
            "annex": annex
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "translate_legal_doc":
        text = arguments.get("text")
        source_lang = arguments.get("source_lang")
        target_lang = arguments.get("target_lang")
        domain = arguments.get("domain", "regulatory")
        
        # Simulated translation
        translations = {
            ("fr", "en"): {
                "conformité": "compliance",
                "réglementation": "regulation",
                "émetteur": "issuer",
                "investisseur": "investor",
                "obligation": "obligation",
                "sanction": "penalty"
            },
            ("en", "fr"): {
                "compliance": "conformité",
                "regulation": "réglementation",
                "issuer": "émetteur",
                "investor": "investisseur",
                "obligation": "obligation",
                "penalty": "sanction"
            }
        }
        
        translated = text
        mapping = translations.get((source_lang, target_lang), {})
        for src, tgt in mapping.items():
            translated = translated.replace(src, tgt)
        
        result = {
            "status": "ok",
            "tool": "translate_legal_doc",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "domain": domain,
            "original": text,
            "translated": translated,
            "note": "Simulated translation - use professional legal translation for production"
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def serve():
        reader, writer = await stdio_server()
        await app.run(reader, writer)
    
    asyncio.run(serve())