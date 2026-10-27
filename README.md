# mcp-frcompliance

MCP server for Francophone Web3 Compliance (FR/EN) - MiCA digests, AMF interpretations, KYC templates, French legal annexes, legal translation.

## Tools

### get_mica_digest
Get MiCA regulatory digest in French or English.

**Parameters:**
- `language` (string, optional): "fr" or "en" (default: "fr")
- `months_back` (integer, optional): Months of history (default: 3)

### get_amf_interpretation
Get AMF regulatory interpretation on specific topics.

**Parameters:**
- `topic` (string, optional): Topic filter (staking, custody, trading, etc.)
- `language` (string, optional): "fr" or "en" (default: "fr")

### generate_kyc_doc
Generate KYC documentation template for individuals or entities.

**Parameters:**
- `entity_type` (string, required): "individual" or "entity"
- `language` (string, optional): "fr" or "en" (default: "fr")
- `jurisdiction` (string, optional): Jurisdiction (default: "France")

### get_french_legal_annex
Get French legal annex for token operations.

**Parameters:**
- `operation_type` (string, required): Operation type (token_issuance, custody, trading)
- `language` (string, optional): "fr" or "en" (default: "fr")

### translate_legal_doc
Translate legal document between French and English.

**Parameters:**
- `text` (string, required): Text to translate
- `source_lang` (string, required): "fr" or "en"
- `target_lang` (string, required): "fr" or "en"
- `domain` (string, optional): Domain context (default: "regulatory")

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Connecting to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "frcompliance": {
      "command": "python",
      "args": ["/path/to/mcp-frcompliance/main.py"],
      "cwd": "/path/to/mcp-frcompliance"
    }
  }
}
```

## License

MIT