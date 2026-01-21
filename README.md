# Telegram Bot «Юрист» - Documentation + Implementation

Welcome to the documentation repository for **Telegram Bot "Юрист"**, an AI-powered legal assistant designed to automate routine legal workflows and deliver professional legal documents in minutes.

## 📚 Repository Contents

### Core Documentation

1. **[SRS_Telegram_Bot_Jurist.md](./SRS_Telegram_Bot_Jurist.md)**  
   Complete Software Requirements Specification (SRS) for the Telegram Bot "Юрист"
   - 9 canonical legal scenarios
   - Technical architecture and requirements
   - Functional and non-functional requirements
   - Prompt router specifications
   - Data schemas and integrations
   - MVP to v2 roadmap

2. **[issue_pack.md](./issue_pack.md)**  
   Comprehensive issue pack breaking down development into epics and tasks
   - 12 development epics
   - Detailed task breakdowns
   - Definition of Done (DoD) for each task
   - Priority assignments (P0-P4)
   - Sprint planning guidance

3. **[PROMOTIONAL_CONTENT.md](./PROMOTIONAL_CONTENT.md)**  
   Product promotion and marketing materials guide
   - 4 promotional scenarios (landing page, social media, email, demo)
   - Brand voice and messaging guidelines
   - Success metrics and CTAs
   - Competitive positioning
   - Marketing campaign templates
   - FAQ for sales and marketing teams

### Implementation

- `mcp-dadata`: MCP server exposing DaData tools (findById/party, suggest/party)
- `tg-bot`: Telegram bot that talks to DaData ONLY via MCP (stdio), stores case fields, supports upload (stores file_id), wizard, and generates markdown bundles

## 🎯 Project Overview

**Telegram Bot "Юрист"** is a specialized legal technology solution that provides:

- ⚡ **9 Canonical Legal Workflows** - From contract analysis to case law research
- 📄 **Smart Document Processing** - PDF/DOCX with OCR support
- 🎯 **Intelligent Routing** - Deterministic scenario detection (75%+ confidence)
- 📊 **Professional Outputs** - DOCX, XLSX, MD export formats
- 🏢 **Company Verification** - DaData integration for due diligence
- 🔐 **Privacy-First** - TTL-based memory, isolated artifacts

## 🚀 Key Features

### 9 Legal Scenarios

1. 🧱 Legal Document Structuring
2. 🔍 Dispute Preparation  
3. ✍️ Legal Opinion Generation
4. ⚖️ Client-Friendly Legal Explanations
5. 📬 Claim Response Drafting
6. 📋 Business Correspondence Context Analysis
7. 🧩 Contract Agent (RF jurisdiction)
8. 📑 Risk Table Generation
9. 📊 Case Law Analytics

### Performance Targets

- **<20 seconds** for text processing
- **<120 seconds** for document processing
- **75%+ confidence** for automatic routing
- **3 export formats** (DOCX, XLSX, MD)

## ⚙️ Configuration

### 1. MCP DaData Server

1. Get your DaData API key from https://dadata.ru/
2. Copy `mcp-dadata/.env.example` to `mcp-dadata/.env`
3. Set `DADATA_API_KEY` in `.env`

### 2. Telegram Bot

1. Create a bot via @BotFather and get your token
2. Copy `tg-bot/.env.example` to `tg-bot/.env`
3. Set `TELEGRAM_BOT_TOKEN` in `.env`
4. Verify `MCP_DADATA_ARGS` points to the correct path

### 3. Build and Run

```bash
# Build MCP server
cd mcp-dadata
npm install
npm run build

# Start bot (in separate terminal)
cd ../tg-bot
npm install
npm start
```

## 📖 How to Use This Repository

### For Developers

Start with **[SRS_Telegram_Bot_Jurist.md](./SRS_Telegram_Bot_Jurist.md)** to understand:
- Technical architecture
- API specifications
- Data schemas (DTO)
- Integration requirements

Then reference **[issue_pack.md](./issue_pack.md)** for:
- Sprint planning
- Task breakdown
- Implementation priorities
- Testing requirements

### For Product/Marketing Teams

Start with **[PROMOTIONAL_CONTENT.md](./PROMOTIONAL_CONTENT.md)** to access:
- Ready-to-use promotional templates
- Brand messaging guidelines
- Campaign strategies
- Sales enablement materials

Refer to **[SRS_Telegram_Bot_Jurist.md](./SRS_Telegram_Bot_Jurist.md)** for:
- Accurate feature descriptions
- Technical metrics for claims
- Roadmap and future capabilities

### For Project Managers

Review all three documents:
1. **SRS** - Understand scope and requirements
2. **Issue Pack** - Plan sprints and allocate resources
3. **Promotional Content** - Align marketing with development roadmap

## 🎯 Quick Start

### Understanding the Product

1. Read the **Product Overview** section in PROMOTIONAL_CONTENT.md
2. Review the **9 Canonical Prompts** in SRS section 3
3. Understand the **Prompt Router** logic in SRS section 7

### Planning Development

1. Review **MVP Backlog** in SRS section 16.1
2. Check **Epics 1-12** in issue_pack.md
3. Assign priorities based on P0-P4 ratings

### Creating Marketing Materials

1. Choose a **Promotional Scenario** from PROMOTIONAL_CONTENT.md
2. Follow **Content Guidelines** (DO/DON'T lists)
3. Use **Call-to-Action Templates** for consistency
4. Reference **Success Metrics** from SRS for accurate claims

## 🔒 Security & Privacy

The bot is designed with privacy-first principles:
- TTL-based session memory
- Isolated artifact storage
- No long-term data retention
- Secure API key management
- PII masking in logs

See SRS section 6 (NFR) for complete security requirements.

## 📊 Development Roadmap

### MVP (1-2 weeks)
- 9 canonical scenarios operational
- PDF/DOCX/TXT file intake
- DOCX/XLSX export
- DaData integration
- Basic commands and memory management

### v1 (2-4 weeks)
- OCR support
- Manual scenario override
- Enhanced confidence calibration
- Improved DOCX/XLSX templates

### v2 (4-8 weeks)
- Corporate features (whitelist, roles)
- Extended scoring
- Case archiving and export
- Advanced observability

See SRS section 16 for detailed roadmap.

## 🤝 Contributing

This repository contains documentation and implementation. For development contributions:

1. Review the SRS for technical specifications
2. Check issue_pack.md for current priorities
3. Follow the Definition of Done (DoD) for each task
4. Ensure all changes maintain security and privacy standards

## 📞 Support & Contact

For questions about:
- **Technical specifications**: See SRS_Telegram_Bot_Jurist.md
- **Development tasks**: See issue_pack.md
- **Marketing materials**: See PROMOTIONAL_CONTENT.md

## 📝 License

[Add license information here]

## 🔄 Document Versions

- **SRS**: Software Requirements Specification v1.0
- **Issue Pack**: Task breakdown v1.0
- **Promotional Content**: Marketing guide v1.0

Last Updated: 2026-01-21

---

**Note**: This repository contains documentation and an initial bot implementation. The bot should follow the specifications outlined in these documents.

## 🤖 Bot commands
- /new
- /scenario <name>
- /set key=value
- /get key
- /fields
- /upload_doc (then send a file)
- /upload_att (then send a file)
- /dadata <inn|ogrn> [kpp]
- /wizard
- /generate
- /export_json

