# mcp-frcompliance

MCP server for **Francophone Web3 Compliance (FR/EN)** - bilingual MiCA digests, AMF
national-level interpretation, KYC/AML documentation cycles, French legal annex with
droit moral handling, compliance deadlines, and glossary-assisted legal translation.

Pricing in the V3 catalogue: $120/mo digest headline, $120-400/mo full retainer.
Annual ~10x with ~17% discount.

## Tools

### `get_mica_digest`
Return the MiCA regulatory digest in French or English: dated entries covering the
articles that changed, with key changes, effective dates and EUR-Lex citations,
filtered to a look-back window.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `language` | string enum `fr`/`en` | `fr` | Digest language |
| `weeks_back` | integer | 4 | How many weeks of history to include (1-520) |
| `topic` | string | - | Optional topic filter (stablecoin, CASP, ART, market abuse...) |

Returns entries with title, summary, key_changes, articles, source_urls, and topics.

### `get_amf_interpretation`
Return AMF (Autorite des marches financiers) France-specific interpretations and
enforcement positions, with reference number, date, enforcement signals and an
explicit France-specific marker distinguishing them from translated EU news.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | - | Topic filter (staking, custody, PSAN, MiCA, marketing...) |
| `language` | string enum `fr`/`en` | `fr` | Response language |
| `enforcement_only` | boolean | `false` | Return only positions with enforcement signals |

Returns scored matches with relevance, enforcement signal, sanction examples, and
the "not_translated_eu_news" note.

### `generate_kyc_doc`
Generate a structured KYC/AML document for an individual or an entity: document
sections, required identity documents, beneficial-owner declaration, source-of-funds
thresholds, PEP and sanctions screening steps, retention rules and signature blocks,
in the requested language.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `entity_type` | string enum `individual`/`entity` | **required** | Customer type |
| `language` | string enum `fr`/`en` | `fr` | Document language |
| `jurisdiction` | string | `France` | Jurisdiction whose rules apply |
| `risk_profile` | string enum `standard`/`elevated`/`high` | `standard` | Risk band driving enhanced measures |
| `service` | string | - | Optional service being onboarded |

Returns the full document with sections, required documents, screening steps,
risk measures, retention rule, and declaration.

### `get_french_legal_annex`
Return a French legal annex for a token operation: per-right enumeration including
droit moral (moral rights are perpetual and inalienable in French law and are
therefore never assigned), governing law, jurisdiction, MiCA/AMF article references,
and the two-column IP exit-rights table.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `operation_type` | string enum `token_issuance`/`custody`/`trading` | **required** | Operation the annex covers |
| `language` | string enum `fr`/`en` | `fr` | Annex language |

Returns title, preamble, enumerated rights with moral rights handling, governing law,
jurisdiction, dispute resolution, regulatory references, and IP exit-rights table.

### `get_compliance_deadlines`
Compute compliance deadlines for a jurisdiction as of a given date: days remaining,
status (upcoming / due / overdue), the regulation behind each deadline, and the
France-specific entries.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `jurisdiction` | string | `France` | Jurisdiction whose calendar applies |
| `as_of` | string | today | ISO date (YYYY-MM-DD) to compute from |
| `include_overdue` | boolean | `true` | Include deadlines already passed |

Returns deadlines sorted by days_remaining with summary (next, overdue, due_soon).

### `translate_legal_doc`
Translate a legal document between French and English using a curated bilingual
regulatory glossary. Legal citations and numbers are preserved verbatim; every
applied term is reported; terms with no glossary entry are flagged as requiring a
certified translator.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | string | **required** | Text to translate |
| `source_lang` | string enum `fr`/`en` | **required** | Source language |
| `target_lang` | string enum `fr`/`en` | **required** | Target language |
| `domain` | string | `regulatory` | Domain context (regulatory, aml, contract, technical) |

Returns translated text, terms_applied (with source/target/position), protected_spans,
untranslated_terms, requires_certified_translator flag, and a disclaimer.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

State is persisted as JSON in `./state/frcompliance_state.json`. Override the location with
`MCP_FRCOMPLIANCE_STATE_DIR`.

## Connecting to an MCP client

```json
{
  "mcpServers": {
    "frcompliance": {
      "command": "python3",
      "args": ["/tmp/v3-services/mcp-frcompliance/main.py"]
    }
  }
}
```

## License

MIT