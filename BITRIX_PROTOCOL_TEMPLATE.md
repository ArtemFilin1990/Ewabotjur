# Bitrix24 Protocol Template Generator

This script generates a protocol template for Bitrix24 in both DOCX and Markdown formats.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic usage with 10 rows (default):

```bash
python make_protocol_template_bitrix.py \
  --out-docx protocol_bitrix_template.docx \
  --out-md protocol_bitrix_template.md
```

Custom number of rows:

```bash
python make_protocol_template_bitrix.py \
  --out-docx protocol_bitrix_template.docx \
  --out-md protocol_bitrix_template.md \
  --rows 15
```

## Arguments

- `--out-docx`: Path for output DOCX file (required)
- `--out-md`: Path for output Markdown file (required)
- `--rows`: Number of disagreement rows in the table (default: 10, must be >= 1)

## Template Variables

The generated template includes placeholder variables that need to be replaced with actual Bitrix24 field codes:

### Standard Bitrix24 Variables
- `{DocumentNumber}` - Document number
- `{DocumentCreateTime~d.m.Y}` - Document creation date
- `{MyCompanyRequisiteRqCompanyName}` - Supplier company name
- `{RequisiteRqCompanyName}` - Buyer company name

### Custom Fields (TBD placeholders)
All variables in the format `{UF_CRM__TBD__*}` should be replaced with actual Bitrix24 custom field codes `{UF_CRM_XXXXXXXXXXXX}` from your portal's field list (⚙ Fields).

Example custom fields:
- `{UF_CRM__TBD__CITY__}` - City
- `{UF_CRM__TBD__CONTRACT_TYPE__}` - Contract type
- `{UF_CRM__TBD__CONTRACT_NUMBER__}` - Contract number
- `{UF_CRM__TBD__CONTRACT_DATE__}` - Contract date
- `{UF_CRM__TBD__SUPPLIER_REPRESENTATIVE_POSITION__}` - Supplier representative position
- `{UF_CRM__TBD__SUPPLIER_REPRESENTATIVE_NAME__}` - Supplier representative name
- `{UF_CRM__TBD__SUPPLIER_BASIS__}` - Supplier basis
- `{UF_CRM__TBD__BUYER_REPRESENTATIVE_POSITION__}` - Buyer representative position
- `{UF_CRM__TBD__BUYER_REPRESENTATIVE_NAME__}` - Buyer representative name
- `{UF_CRM__TBD__BUYER_BASIS__}` - Buyer basis

For each table row (1 to N):
- `{UF_CRM__TBD__CLAUSE_N_NUMBER__}` - Clause number
- `{UF_CRM__TBD__CLAUSE_N_BUYER_TEXT__}` - Buyer's version
- `{UF_CRM__TBD__CLAUSE_N_SUPPLIER_TEXT__}` - Supplier's version
- `{UF_CRM__TBD__CLAUSE_N_AGREED_TEXT__}` - Agreed version

## Output

The script generates two files:

1. **DOCX file**: A formatted Word document with tables and proper styling
2. **MD file**: A Markdown file with the same content, suitable for version control and preview

Both files contain the same template structure with all placeholder variables ready for Bitrix24 integration.
