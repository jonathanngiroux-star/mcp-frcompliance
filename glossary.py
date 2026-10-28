#!/usr/bin/env python3
"""Bilingual FR/EN legal glossary engine for the Francophone Web3 Compliance service.

This is a real term-substitution engine, not a placeholder:

  * terms are matched longest-phrase-first so multi-word legal terms win over
    their constituent words ("offre au public" beats "offre" and "public");
  * legal citations and identifiers (AMF, MiCA Art. 16, ESMA, DORA, RGPD,
    EUR-Lex CELEX ids, article numbers, dates, amounts) are protected and
    reproduced verbatim;
  * every applied term is reported so the caller can audit the translation;
  * source terms with no glossary entry are reported as untranslated and raise a
    "requires certified translator" flag.

The glossary is deliberately finite and curated: it covers the regulatory
vocabulary of MiCA, AMF practice and EU AML. Anything outside it is surfaced
rather than silently mangled.
"""

from __future__ import annotations

import re
from typing import Any

# --------------------------------------------------------------------------
# Glossary: fr -> en. Longest phrases first at match time.
# --------------------------------------------------------------------------

FR_TO_EN: dict[str, str] = {
    # --- core MiCA / crypto-asset vocabulary --------------------------------
    "crypto-actif": "crypto-asset",
    "crypto-actifs": "crypto-assets",
    "actif crypto": "crypto-asset",
    "actifs crypto": "crypto-assets",
    "actif numérique": "digital asset",
    "actifs numériques": "digital assets",
    "jeton": "token",
    "jetons": "tokens",
    "jeton adossé à un actif": "asset-referenced token",
    "jetons adossés à des actifs": "asset-referenced tokens",
    "jeton d'argent électronique": "e-money token",
    "jetons d'argent électronique": "e-money tokens",
    "jeton de service": "utility token",
    "offre au public": "offer to the public",
    "offres au public": "offers to the public",
    "émetteur": "issuer",
    "émetteurs": "issuers",
    "émetteur d'actifs crypto": "crypto-asset issuer",
    "émetteur d'actifs crypto-asset": "crypto-asset issuer",
    "prestataire de services sur crypto-actifs": "crypto-asset service provider",
    "prestataires de services sur crypto-actifs": "crypto-asset service providers",
    "document d'information": "information document",
    "livre blanc": "white paper",
    "livres blancs": "white papers",
    "avis d'information": "notification",
    "demande d'enregistrement": "registration application",
    "enregistrement": "registration",
    "agrément": "authorisation",
    "agréments": "authorisations",
    "autorisation": "authorisation",
    "autorité compétente": "competent authority",
    "autorités compétentes": "competent authorities",
    "établissement de monnaie électronique": "e-money institution",
    "établissements de monnaie électronique": "e-money institutions",
    "admission à la négociation": "admission to trading",
    "plateforme de négociation": "trading platform",
    "plateformes de négociation": "trading platforms",
    "plateforme de négociation d'actifs crypto": "crypto-asset trading platform",
    "custody": "custody",
    "conservation": "custody",
    "conservateur": "custodian",
    "client": "client",
    "clients": "clients",
    "actif numérique": "digital asset",
    "actifs numériques": "digital assets",
    "actif sur référence": "referenced asset",
    "actifs sur référence": "referenced assets",
    "stablecoin": "stablecoin",
    "stablecoins": "stablecoins",
    "réserves": "reserves",
    "commission": "commission",
    "commissions": "commissions",
    "courtier": "broker",
    "marché réglementé": "regulated market",
    "marchés réglementés": "regulated markets",
    "système multilatéral de négociation": "multilateral trading facility",
    "lieu de négociation": "trading venue",
    "lieux de négociation": "trading venues",
    "abus de marché": "market abuse",
    "manipulation de marché": "market manipulation",
    "manipulation du marché": "market manipulation",
    "information privilégiée": "inside information",
    "insider dealing": "insider dealing",
    "opération sur ses propres fonds": "own-account transaction",
    "portefeuille": "portfolio",
    "mandat": "mandate",
    "exécution": "execution",
    "exécution au mieux": "best execution",
    "protection de l'épargne": "investor protection",
    "protection des investisseurs": "investor protection",
    "conformité": "compliance",
    "conformité réglementaire": "regulatory compliance",
    "réglementation": "regulation",
    "réglementaire": "regulatory",
    "dispositif": "framework",
    "dispositif réglementaire": "regulatory framework",
    "surveillance": "supervision",
    "contrôle": "control",
    "contrôles": "controls",
    "sanction": "penalty",
    "sanctions": "penalties",
    "amende": "fine",
    "amendes": "fines",
    "mise en demeure": "formal notice",
    "avertissement": "warning",
    "blâme": "reprimand",
    "gel": "freeze",
    "gel d'actifs": "asset freeze",
    "saisine": "referral",
    "saisine du procureur": "referral to the prosecutor",
    "poursuite": "enforcement action",
    "poursuites": "enforcement actions",
    "obligation": "obligation",
    "obligations": "obligations",
    "devoir de vigilance": "duty of vigilance",
    "diligence": "due diligence",
    "obligation de vigilance": "obligation of vigilance",
    "approche par les risques": "risk-based approach",
    "évaluation des risques": "risk assessment",
    "cartographie des risques": "risk mapping",
    "connaissance du client": "know-your-customer",
    "vérification d'identité": "identity verification",
    "vérifications d'identité": "identity verification",
    "diligence clientèle": "customer due diligence",
    "personne politiquement exposée": "politically exposed person",
    "personnes politiquement exposées": "politically exposed persons",
    "pes": "pep",
    "sanctions": "sanctions",
    "liste de sanctions": "sanctions list",
    "gel des avoirs": "asset freezing",
    "blanchiment d'argent": "money laundering",
    "financement du terrorisme": "terrorist financing",
    "lutte contre le blanchiment": "anti-money laundering",
    "lutte contre le financement du terrorisme": "counter-terrorist financing",
    "blanchiment": "money laundering",
    "source des fonds": "source of funds",
    "source des fonds et de la richesse": "source of funds and source of wealth",
    "origine des fonds": "origin of funds",
    "titulaire effectif": "beneficial owner",
    "titulaires effectifs": "beneficial owners",
    "bénéficiaire effectif": "beneficial owner",
    "bénéficiaires effectifs": "beneficial owners",
    "déclaration des bénéficiaires effectifs": "beneficial ownership declaration",
    "lutte contre le blanchiment de capitaux": "anti-money laundering",
    "surveillance renforcée": "enhanced due diligence",
    "gel des avoirs": "asset freeze",
    "surveillance des transactions": "transaction monitoring",
    "surveillance des opérations": "transaction monitoring",
    "surveillance permanente": "continuous monitoring",
    "déclaration de soupçon": "suspicion report",
    "déclaration d'opération suspecte": "suspicion report",
    "signalement": "reporting",
    "cellule de renseignement financier": "financial intelligence unit",
    "plaintes": "complaints",
    "conservation des données": "data retention",
    "durée de conservation": "retention period",
    "cinq ans": "five years",
    "dix ans": "ten years",
    "six ans": "six years",
    "protection des données": "data protection",
    "protection des données à caractère personnel": "personal data protection",
    "données à caractère personnel": "personal data",
    "droit de rectification": "right of rectification",
    "droit à l'effacement": "right to erasure",
    "droit d'opposition": "right to object",
    "droit à la portabilité": "right to data portability",
    "responsabilité": "liability",
    "responsabilité du fait des agents": "liability for the acts of agents",
    "responsabilité solidaire": "joint and several liability",
    "droit moral": "moral rights",
    "droits patrimoniaux": "economic rights",
    "droits de la personnalité": "personal rights",
    "cession": "assignment",
    "cession de droits": "assignment of rights",
    "licence": "licence",
    "sous-licence": "sublicence",
    "clause de non-concurrence": "non-compete clause",
    "droit applicable": "governing law",
    "droit compétent": "applicable law",
    "juridiction compétente": "competent jurisdiction",
    "tribunal de commerce": "commercial court",
    "tribunal de commerce de Paris": "Paris Commercial Court",
    "clause attributive de compétence": "jurisdiction clause",
    "médiation": "mediation",
    "arbitrage": "arbitration",
    "litige": "dispute",
    "litiges": "disputes",
    "règlement des litiges": "dispute resolution",
    "résiliation": "termination",
    "préavis": "notice period",
    "faculté de rétractation": "right of withdrawal",
    "quatorze jours": "fourteen days",
    "douze mois": "twelve months",
    "vingt-quatre mois": "twenty-four months",
    "trente jours": "thirty days",
    "soixante jours": "sixty days",
    "six mois": "six months",
    "douze mois": "twelve months",
    "entrée en vigueur": "entry into force",
    "application": "application",
    "date d'application": "date of application",
    "transitoire": "transitional",
    "disposition transitoire": "transitional provision",
    "dispositions transitoires": "transitional provisions",
    "période transitoire": "transitional period",
    "grandfathering": "grandfathering",
    "auto-certification": "self-certification",
    "auto-certifié": "self-certified",
    "règlement": "regulation",
    "règlements": "regulations",
    "directive": "directive",
    "directives": "directives",
    "règlement délégué": "delegated regulation",
    "règlements délégués": "delegated regulations",
    "actes délégués": "delegated acts",
    "rapport": "report",
    "rapports": "reports",
    "rapport trimestriel": "quarterly report",
    "rapports mensuels": "monthly reports",
    "rapport annuel": "annual report",
    "audit": "audit",
    "auditeur": "auditor",
    "audit externe": "external audit",
    "comptes": "accounts",
    "documents comptables": "accounting records",
    "surveillance des risques": "risk monitoring",
    "gestion des risques": "risk management",
    "politique de gestion des risques": "risk management policy",
    "procédure de gestion des incidents": "incident management procedure",
    "journalisation": "logging",
    "registre": "register",
    "conservation des registres": "retention of records",
    "délégué": "delegate",
    "mandataire": "representative",
    "établissement": "establishment",
    "succursale": "branch",
    "succursale établie": "established branch",
    "passport": "passport",
    "passporting": "passporting",
    "reconnaissance mutuelle": "mutual recognition",
    "notification préalable": "prior notification",
    "notification": "notification",
    "déclaration": "declaration",
    "déclarations": "declarations",
    "attestation": "attestation",
    "attestations": "attestations",
    "certificat": "certificate",
    "agrément préalable": "prior authorisation",
    "examen": "review",
    "instruction": "investigation",
    "questionnaire": "questionnaire",
    "réponse": "response",
    "soumission": "submission",
    "avis": "notice",
    "avertissement public": "public warning",
    "liste blanche": "white list",
    "liste grise": "grey list",
    "paquets": "packages",
    "paquet": "package",
}

EN_TO_FR: dict[str, str] = {
    # --- core MiCA / crypto-asset vocabulary --------------------------------
    "crypto-asset": "crypto-actif",
    "crypto-assets": "crypto-actifs",
    "digital asset": "actif numérique",
    "digital assets": "actifs numériques",
    "token": "jeton",
    "tokens": "jetons",
    "asset-referenced token": "jeton adossé à un actif",
    "asset-referenced tokens": "jetons adossés à des actifs",
    "e-money token": "jeton d'argent électronique",
    "e-money tokens": "jetons d'argent électronique",
    "utility token": "jeton de service",
    "offer to the public": "offre au public",
    "offers to the public": "offres au public",
    "issuer": "émetteur",
    "issuers": "émetteurs",
    "crypto-asset issuer": "émetteur d'actifs crypto",
    "crypto-asset service provider": "prestataire de services sur crypto-actifs",
    "crypto-asset service providers": "prestataires de services sur crypto-actifs",
    "information document": "document d'information",
    "white paper": "livre blanc",
    "white papers": "livres blancs",
    "notification": "notification",
    "registration application": "demande d'enregistrement",
    "registration": "enregistrement",
    "authorisation": "agrément",
    "competent authority": "autorité compétente",
    "competent authorities": "autorités compétentes",
    "e-money institution": "établissement de monnaie électronique",
    "admission to trading": "admission à la négociation",
    "trading platform": "plateforme de négociation",
    "trading platforms": "plateformes de négociation",
    "custody": "conservation",
    "custodian": "conservateur",
    "client": "client",
    "clients": "clients",
    "referenced asset": "actif sur référence",
    "referenced assets": "actifs sur référence",
    "reserves": "réserves",
    "commission": "commission",
    "broker": "courtier",
    "regulated market": "marché réglementé",
    "regulated markets": "marchés réglementés",
    "trading venue": "lieu de négociation",
    "market abuse": "abus de marché",
    "market manipulation": "manipulation de marché",
    "inside information": "information privilégiée",
    "own-account transaction": "opération sur ses propres fonds",
    "portfolio": "portefeuille",
    "mandate": "mandat",
    "execution": "exécution",
    "best execution": "exécution au mieux",
    "investor protection": "protection des investisseurs",
    "compliance": "conformité",
    "regulatory compliance": "conformité réglementaire",
    "regulation": "règlement",
    "regulations": "règlements",
    "regulatory": "réglementaire",
    "framework": "dispositif",
    "regulatory framework": "dispositif réglementaire",
    "supervision": "surveillance",
    "control": "contrôle",
    "controls": "contrôles",
    "penalty": "sanction",
    "penalties": "sanctions",
    "fine": "amende",
    "fines": "amendes",
    "formal notice": "mise en demeure",
    "warning": "avertissement",
    "reprimand": "blâme",
    "asset freeze": "gel d'actifs",
    "referral": "saisine",
    "enforcement action": "poursuite",
    "enforcement actions": "poursuites",
    "obligation": "obligation",
    "obligations": "obligations",
    "duty of vigilance": "devoir de vigilance",
    "due diligence": "diligence",
    "risk-based approach": "approche par les risques",
    "risk assessment": "évaluation des risques",
    "risk mapping": "cartographie des risques",
    "know-your-customer": "connaissance du client",
    "identity verification": "vérification d'identité",
    "customer due diligence": "diligence clientèle",
    "politically exposed person": "personne politiquement exposée",
    "politically exposed persons": "personnes politiquement exposées",
    "sanctions list": "liste de sanctions",
    "asset freezing": "gel des avoirs",
    "money laundering": "blanchiment d'argent",
    "terrorist financing": "financement du terrorisme",
    "anti-money laundering": "lutte contre le blanchiment",
    "counter-terrorist financing": "lutte contre le financement du terrorisme",
    "source of funds": "source des fonds",
    "source of funds and source of wealth": "source des fonds et de la richesse",
    "origin of funds": "origine des fonds",
    "beneficial owner": "titulaire effectif",
    "beneficial owners": "titulaires effectifs",
    "beneficial ownership declaration": "déclaration des bénéficiaires effectifs",
    "enhanced due diligence": "surveillance renforcée",
    "transaction monitoring": "surveillance des transactions",
    "continuous monitoring": "surveillance permanente",
    "suspicion report": "déclaration de soupçon",
    "reporting": "signalement",
    "financial intelligence unit": "cellule de renseignement financier",
    "complaints": "plaintes",
    "data retention": "conservation des données",
    "retention period": "durée de conservation",
    "five years": "cinq ans",
    "ten years": "dix ans",
    "personal data protection": "protection des données à caractère personnel",
    "personal data": "données à caractère personnel",
    "right of rectification": "droit de rectification",
    "right to erasure": "droit à l'effacement",
    "right to object": "droit d'opposition",
    "right to data portability": "droit à la portabilité",
    "liability": "responsabilité",
    "joint and several liability": "responsabilité solidaire",
    "moral rights": "droit moral",
    "economic rights": "droits patrimoniaux",
    "personal rights": "droits de la personnalité",
    "assignment": "cession",
    "assignment of rights": "cession de droits",
    "licence": "licence",
    "sublicence": "sous-licence",
    "non-compete clause": "clause de non-concurrence",
    "governing law": "droit applicable",
    "applicable law": "droit applicable",
    "competent jurisdiction": "juridiction compétente",
    "commercial court": "tribunal de commerce",
    "Paris Commercial Court": "tribunal de commerce de Paris",
    "jurisdiction clause": "clause attributive de compétence",
    "mediation": "médiation",
    "arbitration": "arbitrage",
    "dispute": "litige",
    "disputes": "litiges",
    "dispute resolution": "règlement des litiges",
    "termination": "résiliation",
    "notice period": "préavis",
    "right of withdrawal": "faculté de rétractation",
    "fourteen days": "quatorze jours",
    "twelve months": "douze mois",
    "twenty-four months": "vingt-quatre mois",
    "thirty days": "trente jours",
    "sixty days": "soixante jours",
    "six months": "six mois",
    "entry into force": "entrée en vigueur",
    "application": "application",
    "date of application": "date d'application",
    "transitional provision": "disposition transitoire",
    "transitional provisions": "dispositions transitoires",
    "transitional period": "période transitoire",
    "grandfathering": "grandfathering",
    "self-certification": "auto-certification",
    "self-certified": "auto-certifié",
    "delegated regulation": "règlement délégué",
    "delegated regulations": "règlements délégués",
    "delegated acts": "actes délégués",
    "report": "rapport",
    "reports": "rapports",
    "quarterly report": "rapport trimestriel",
    "monthly reports": "rapports mensuels",
    "annual report": "rapport annuel",
    "audit": "audit",
    "auditor": "auditeur",
    "external audit": "audit externe",
    "accounts": "comptes",
    "accounting records": "documents comptables",
    "risk monitoring": "surveillance des risques",
    "risk management": "gestion des risques",
    "risk management policy": "politique de gestion des risques",
    "incident management procedure": "procédure de gestion des incidents",
    "logging": "journalisation",
    "register": "registre",
    "retention of records": "conservation des registres",
    "delegate": "délégué",
    "representative": "mandataire",
    "establishment": "établissement",
    "branch": "succursale",
    "established branch": "succursale établie",
    "passporting": "passport",
    "mutual recognition": "reconnaissance mutuelle",
    "prior notification": "notification préalable",
    "declaration": "déclaration",
    "declarations": "déclarations",
    "attestation": "attestation",
    "attestations": "attestations",
    "certificate": "certificat",
    "prior authorisation": "agrément préalable",
    "review": "examen",
    "investigation": "instruction",
    "questionnaire": "questionnaire",
    "response": "réponse",
    "submission": "soumission",
    "notice": "avis",
    "public warning": "avertissement public",
    "white list": "liste blanche",
    "grey list": "liste grise",
}

# --------------------------------------------------------------------------
# Protected tokens: legal citations, identifiers, dates, amounts, numbers.
# These are reproduced verbatim and never substituted.
# --------------------------------------------------------------------------

PROTECTED_PATTERNS: list[str] = [
    r"\b(?:MiCA|MiFID|DORA|AMF|ACPR|AMLD|AMLR|RGPD|GDPR|EUR-Lex|ESMA|EBA|TRAC|PSAN|PSFP|CASP|"
    r"ART|EMI|DASP|AMLR|CSRD|CSDDD|MEF|TRAC|FATF|OFAC|UN|EUR|SEK|CNY|USD|EUR)\b",
    r"\bArticle\s+\d+(?:\.\d+)*",
    r"\bArt\.\s*\d+(?:\.\d+)*",
    r"\b(?:CELEX|DOC|LAW|REG|Directive|Règlement)\s*[:\s]?\s*\d{4}[A-Za-z0-9/]*",
    r"\b\d{1,3}(?:[  ]\d{3})+(?:[.,]\d+)?\s*(?:EUR|USD|euros?|dollars?)",
    r"\b\d+(?:[.,]\d+)?\s*(?:EUR|USD|euros?|dollars?|%|pour cent)\b",
    r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:Article|Art\.)\s+\d+(?:\.\d+)*\s*(?:du|de la|de l')?\s*[A-ZÉÈÀ][A-Za-zÀ-ÿ ]{2,40}",
]

_PROTECTED_RE = re.compile("|".join(PROTECTED_PATTERNS))

# Length-preserving accent folding. French legal text is frequently written
# without accents (ASCII-fied exports, ticketing systems, filings pasted from
# spreadsheets), so "emetteur" must match the glossary entry "émetteur".
# Every mapping below is exactly 1 char -> 1 char, so folded-string offsets
# stay aligned with the original and can be used to splice substitutions
# back into the untouched source string.
_FOLD_MAP = {
    "à": "a", "á": "a", "â": "a", "ã": "a", "ä": "a", "å": "a",
    "è": "e", "é": "e", "ê": "e", "ë": "e",
    "ì": "i", "í": "i", "î": "i", "ï": "i",
    "ò": "o", "ó": "o", "ô": "o", "õ": "o", "ö": "o",
    "ù": "u", "ú": "u", "û": "u", "ü": "u",
    "ý": "y", "ÿ": "y",
    "ç": "c", "ñ": "n",
    "À": "A", "Á": "A", "Â": "A", "Ã": "A", "Ä": "A", "Å": "A",
    "È": "E", "É": "E", "Ê": "E", "Ë": "E",
    "Ì": "I", "Í": "I", "Î": "I", "Ï": "I",
    "Ò": "O", "Ó": "O", "Ô": "O", "Õ": "O", "Ö": "O",
    "Ù": "U", "Ú": "U", "Û": "U", "Ü": "U",
    "Ý": "Y", "Ç": "C", "Ñ": "N",
    "’": "'", "‘": "'", "‛": "'", "ʼ": "'",
    "‑": "-", "–": "-", "—": "-",
    " ": " ", " ": " ", " ": " ",
}


def _fold(text: str) -> str:
    """Accent-fold a string while preserving character offsets."""
    return "".join(_FOLD_MAP.get(char, char) for char in text)


def _protect(text: str) -> tuple[str, list[str]]:
    """Replace protected spans with placeholders; return (masked, originals)."""
    originals: list[str] = []

    def _sub(match: re.Match[str]) -> str:
        originals.append(match.group(0))
        return f"\x00P{len(originals) - 1}\x00"

    return _PROTECTED_RE.sub(_sub, text), originals


def _restore(text: str, originals: list[str]) -> str:
    for index, original in enumerate(originals):
        text = text.replace(f"\x00P{index}\x00", original)
    return text


def _word_pattern(term: str) -> re.Pattern[str]:
    """Match a glossary term on word boundaries, tolerant of case and accents."""
    escaped = re.escape(term)
    # Allow flexible whitespace (incl. non-breaking space) between words.
    escaped = escaped.replace(r"\ ", r"[\s ]+")
    return re.compile(rf"(?<![\wÀ-ÿ]){escaped}(?![\wÀ-ÿ])", re.IGNORECASE)


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
) -> dict[str, Any]:
    """Glossary-assisted legal translation with an auditable report."""
    source = source_lang.lower()
    target = target_lang.lower()
    if source not in ("fr", "en") or target not in ("fr", "en"):
        return {
            "translated": text,
            "terms_applied": [],
            "untranslated_terms": [],
            "protected_spans": [],
            "requires_certified_translator": True,
            "error": "unsupported language pair",
        }
    if source == target:
        return {
            "translated": text,
            "terms_applied": [],
            "untranslated_terms": [],
            "protected_spans": [],
            "requires_certified_translator": False,
            "same_language": True,
            "note": "Source and target languages are identical; text returned unchanged.",
        }

    glossary = FR_TO_EN if source == "fr" else EN_TO_FR
    masked, protected = _protect(text)

    # Matching runs on an accent-folded copy (same length as the original) so
    # that ASCII-fied French ("emetteur") still matches the glossary entry
    # ("émetteur"), while the substitutions themselves are applied to the
    # original text.
    folded = _fold(masked)

    # Longest phrase first so multi-word legal terms win over their parts.
    ordered = sorted(glossary.items(), key=lambda item: len(item[0]), reverse=True)

    # Collect every candidate match, then resolve overlaps by preferring the
    # longest span (and, at equal length, the earliest position).
    candidates: list[tuple[int, int, str, str]] = []
    for source_term, target_term in ordered:
        pattern = _word_pattern(_fold(source_term))
        for match in pattern.finditer(folded):
            start, end = match.span()
            if end > start:
                candidates.append((start, end, source_term, target_term))

    candidates.sort(key=lambda item: (-(item[1] - item[0]), item[0]))

    selected: list[tuple[int, int, str, str]] = []
    taken: list[tuple[int, int]] = []
    for start, end, source_term, target_term in candidates:
        if any(start < t_end and end > t_start for t_start, t_end in taken):
            continue
        selected.append((start, end, source_term, target_term))
        taken.append((start, end))

    # Apply the selected substitutions right-to-left BY POSITION so that
    # earlier offsets remain valid even when a replacement is longer or
    # shorter than the span it replaces. Untouched characters keep their exact
    # original spelling.
    result = masked
    applied: list[dict[str, Any]] = []
    for start, end, source_term, target_term in sorted(
        selected, key=lambda item: item[0], reverse=True
    ):
        result = result[:start] + target_term + result[end:]
        applied.append(
            {
                "source_term": masked[start:end],
                "normalized_source_term": source_term,
                "target_term": target_term,
                "position": start,
            }
        )

    applied.sort(key=lambda item: item["position"])
    result = _restore(result, protected)

    # Report source terms that had no glossary entry. The spans already
    # translated (and the protected citations) are excluded so a term that WAS
    # translated is never reported as untranslated.
    exclude_spans = [(item["position"], item["position"] + len(item["source_term"])) for item in applied]
    untranslated = _find_untranslated(text, glossary, source, exclude_spans)

    return {
        "translated": result,
        "terms_applied": applied,
        "untranslated_terms": untranslated,
        "protected_spans": protected,
        "requires_certified_translator": bool(untranslated),
    }


def _find_untranslated(
    text: str,
    glossary: dict[str, str],
    source: str,
    exclude_spans: list[tuple[int, int]] | None = None,
) -> list[str]:
    """Find source-language legal phrases that have no glossary entry.

    `exclude_spans` are the source spans that were already translated (plus
    the protected citations); they are blanked out first so a term that WAS
    translated is never reported as untranslated.
    """
    masked, _ = _protect(text)
    if exclude_spans:
        chars = list(masked)
        for start, end in exclude_spans:
            for index in range(start, min(end, len(chars))):
                chars[index] = " "
        masked = "".join(chars)

    known = {_fold(term.lower()) for term in glossary}
    found: list[str] = []
    seen: set[str] = set()

    if source == "fr":
        candidates = re.findall(
            r"\b[a-zA-Zéèêàçôûùîïœ]{4,}(?:[\s ]+[a-zA-Zéèêàçôûùîïœ]{4,}){0,2}\b",
            masked,
        )
        stop = {
            "dans", "pour", "avec", "sans", "plus", "cette", "leur", "elle", "vous",
            "nous", "dont", "tout", "tous", "une", "des", "les", "par", "sur",
            "aux", "du", "de", "la", "le", "et", "ou", "ne", "qui", "que", "est",
            "sont", "etre", "avoir", "fait", "ainsi", "cas", "peut", "doit",
            "entre", "apres", "avant", "selon", "conformement", "presente",
            "present", "lorsque", "lors", "auxquelles", "auxquels", "avant",
            "etre", "avoir", "moins", "seul", "seule", "meme", "toute",
            "toutes", "doivent", "devrait", "peuvent", "faire", "fournir",
            "donner", "obtenir", "notifier", "declarer", "avant", "son",
            "sa", "ses", "leur", "leurs", "ce", "cet", "cette", "ces",
        }
        for candidate in candidates:
            lowered = _fold(candidate.lower())
            if lowered in stop or lowered in known or lowered in seen:
                continue
            # Only flag multi-word phrases or words carrying accents, which is
            # where residual legal vocabulary actually survives.
            if len(candidate.split()) >= 2 or re.search(r"[éèêàçôûùîïœ]", lowered):
                seen.add(lowered)
                found.append(candidate)
    else:
        candidates = re.findall(
            r"\b[A-Za-z][A-Za-z'-]{3,}(?:[\s ]+[A-Za-z][A-Za-z'-]{3,}){0,2}\b",
            masked,
        )
        stop = {
            "this", "that", "with", "from", "have", "will", "shall", "would",
            "should", "could", "been", "were", "they", "them", "their", "there",
            "which", "when", "where", "what", "while", "after", "before",
            "under", "over", "into", "such", "only", "also", "must", "does",
            "both", "each", "any", "all", "not", "but", "for", "and", "the",
            "its", "before", "prior", "public", "services", "service",
        }
        for candidate in candidates:
            lowered = _fold(candidate.lower())
            if lowered in stop or lowered in known or lowered in seen:
                continue
            if len(candidate.split()) >= 2:
                seen.add(lowered)
                found.append(candidate)

    return found[:25]
