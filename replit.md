# Mining Due Diligence AI Agent

## Overview

This application is a Streamlit-based Mining Due Diligence AI Agent designed to analyze technical documents (PDFs, DOCX, XLSX) of mining projects. It generates dual quantified scores (Investment Score 0-100 and Sustainability Score 0-100) and produces comprehensive due diligence reports. The agent evaluates projects across weighted categories for both investment and sustainability, providing actionable recommendations. Key capabilities include a global comparables database, custom scoring templates, comprehensive financial modeling (NPV/IRR, sensitivity analysis, real-time commodity pricing), AI-powered strategic narratives, comparables benchmarking, and a two-tier AI system for standard and advanced valuation methodologies.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions

The application utilizes Streamlit for an interactive, chat-style web interface with a modern white-themed UI, Inter typography, and blue/purple gradients. It features a professional landing page with full navigation.

### Technical Implementations

The system is modular, with components for document extraction, AI analysis, scoring, report generation, financial modeling, market data, financial exports, and comparables matching, enabling independent testing and scalability.

#### AI Analysis Component (Hybrid AI System)

The platform uses a hybrid AI approach with two complementary models:

**Oreplot Light (GPT-5.1)**:
- OpenAI's GPT-5.1 with `reasoning_effort="high"` for all document extraction and analysis
- Superior vision capabilities for PDF/image processing and table extraction
- Reliable JSON structured output for financial data parsing
- Optimized for mining technical reports, processing PDFs up to 500 pages
- Enhanced prompts for NI 43-101 reports, resource/reserve statements, financial data, drill hole data

**Oreplot Advanced (Hybrid: GPT-5.1 + Claude Opus 4.5)**:
- GPT-5.1: Document extraction and financial data parsing (superior vision & JSON reliability)
- Claude Opus 4.5: Investment narratives and strategic analysis (superior reasoning & writing)
- Claude generates executive summaries, key value drivers, risk assessments, and investment theses
- Fallback to GPT-5.1 for narratives if Claude unavailable

Both models use Replit AI Integrations (no separate API keys required - charges billed to credits). Robust retry logic with exponential backoff handles API rate limits.

#### Document Processing Pipeline

Advanced multi-format processing leverages GPT-5.1 Vision for PDFs (up to 500 pages), DOCX/XLSX for native parsing, and high-detail extraction for images. An enhanced `pytesseract` OCR provides a fallback for improved accuracy on technical documents. The system supports bulk uploads with maximum 80 files per upload, processed in batches of 10 files with real-time progress tracking. This prevents timeouts and memory issues during large bulk uploads while maintaining stability. Specifically targets resource/reserve statements, financial tables, drill hole data, and production schedules while preserving structure and numerical accuracy. **Oreplot Advanced API text limit: 8MB per extraction** (respects OpenAI's 10.5MB message limit with safety margin).

**Parallel Processing**: PDF page extraction uses `ThreadPoolExecutor` with 5 concurrent workers (`MAX_PARALLEL_PAGES=5`) for 5x faster processing. AI Training embeddings use 3 concurrent workers (`MAX_PARALLEL_EMBEDDINGS=3`) for faster document training while respecting API rate limits. Both Oreplot Light and Advanced benefit from parallel document extraction.

#### Dual Scoring Engine

**Investment Scoring**: A flexible, weighted categorical system evaluates projects across six customizable categories (Geology/Prospectivity, Resource Potential, Economics, Legal & Title, Permitting & ESG, Data Quality) to produce a normalized score (0-100).

**Sustainability Scoring**: Evaluates projects against industry-standard ESG criteria across four weighted categories (Environmental Performance, Social Performance, Governance, Climate & Energy).

Both scores are calculated independently and displayed with category breakdowns, evidence traceability, and identified information gaps. A severity-based penalty engine ensures scoring consistency and accuracy by applying penalties for critical missing items while distinguishing from minor gaps, and validates scores based on evidence requirements.

#### Financial Analysis & Valuation Module

Provides comprehensive financial modeling, including NPV/IRR calculations, payback period, production profiles, cash flow generation, and sensitivity analysis. It integrates real-time commodity pricing and offers professional Excel export capabilities.

#### Comparables Benchmarking

An intelligent project matching system uses a weighted similarity scoring (commodity, deposit style, development stage, jurisdiction, resource scale) to identify and present the top 3 most similar projects from a global database. This database is automatically updated weekly via an ingestion service that uses AI-powered research and an admin approval queue.

#### Two-Tier AI System

The platform features a subscription-based two-tier AI system with clear visual differentiation throughout the UI:
- **Light AI (Standard Tier)**: Includes all core platform capabilities (document analysis, dual scoring, financial analysis, comparables, PDF reports). Displayed with blue badges in the UI.
- **Advanced AI (Professional Tier)**: Functions as an AI agent with document upload interface (up to 5GB), GPT-5.1 powered data extraction, and automatic valuation calculations. Displayed with purple badges in the UI. Includes 5 professional valuation methodologies:

#### AI Chat Interface (`components/ai_chat.py`)

Both Oreplot Light and Advanced feature an integrated AI Chat interface that replaces the old Project Description field:
- **Context-Aware Conversations**: Users can highlight important points about uploaded documents and the AI understands the full context
- **Analysis Correction**: After analysis completes, users can point out errors and the AI can provide corrections
- **Persistent Chat**: Message history is maintained via session state throughout the analysis workflow
- **Tier-Specific Styling**: Blue theme for Light AI, purple theme for Advanced AI
- **Dual Display Modes**: Compact input mode during document upload, full chat interface after analysis results
- **Hybrid AI Backend**: Uses Claude (Advanced) or GPT-4o (Light) for intelligent responses based on analysis tier

Advanced AI includes 5 professional valuation methodologies:
  1. **Probability-Weighted DCF**: Risk-adjusted NPV with stage-gate success probabilities
  2. **Income Approach DCF**: Traditional cash flow projection model
  3. **Monte Carlo Risk Modeling**: 10,000+ simulations with commodity price/cost uncertainty
  4. **Cost Approach (Kilburn Method)**: Exploration asset floor value based on replacement cost
  5. **Decision Tree EMV**: Stage-gate expected monetary value analysis

**Analysis Type Tracking**: All analyses are tagged with their type ('light_ai' or 'advanced_ai') in the database. This enables:
- Visual badges on Projects page showing which AI tier was used
- Report listings with color-coded analysis type indicators
- PDF reports with analysis type header (Light AI vs Advanced AI)
- Advanced AI analyses can be saved to the project repository using "Save to Projects" feature

#### Advanced AI Technical Implementation

The Advanced AI system (`advanced_ai_analyzer.py`) uses a unified analyzer that:
1. Extracts financial and technical data from uploaded documents using structured GPT-5.1 prompts
2. Runs all 5 valuation methods on extracted data with type-safe handling
3. Generates AI-powered valuation narrative for investment committees
4. Consolidates results with summary and cross-method recommendations

**Strict Input Validation**: All valuation engines require THREE core inputs to calculate valuations:
- `annual_production` - Annual production quantity (oz, tonnes, etc.)
- `commodity_price` - Current or assumed commodity price
- `operating_cost` or `AISC` - All-in sustaining cost or operating cost

If ANY of these inputs are missing or invalid, the engine returns an `insufficient_data` error instead of fabricating values. This prevents misleading valuations based on document-reported NPVs or synthetic defaults.

**Valuation Engine Dependency Chain**:
- Income DCF runs FIRST and calculates the base NPV from actual production/price/cost data
- Probability DCF and Decision Tree EMV use the calculated NPV from Income DCF (NOT document-reported NPVs)
- Monte Carlo requires all three inputs independently
- Kilburn Method works independently for exploration asset floor values

**Smart Data Normalization**: When extraction returns zero or missing values, the system attempts to derive them:
- `annual_production` from life_of_mine_production / mine_life OR throughput × grade × recovery
- `commodity_price` from commodity_price_assumption OR annual_revenue / annual_production
- `operating_cost` from annual_opex / annual_production
- Shows derivation notes to users when values are calculated from other fields

**User Feedback**: When data is insufficient:
- Each methodology shows specific missing inputs (not generic errors)
- Missing Inputs Report section displays what's needed for complete valuations
- Tips provided for what data to include in uploaded documents

All valuation engines include robust type safety with:
- `safe_float()` and `safe_int()` helper functions to prevent crashes on None/missing data
- Division-by-zero guards using conditional defaults for non-critical values
- Graceful degradation when OpenAI API is not configured
- Short-circuit logic when extraction fails (returns error-only payload)

### System Design Choices

The application is a comprehensive platform with full navigation, user management (dashboard, project management, report repository, settings), and session state management for seamless transitions.

#### AI Training System (Enhanced RAG)

Admin-only feature for uploading training documents (up to 4 GB) to improve AI extraction accuracy for both Oreplot Light and Advanced. Uses Enhanced RAG (Retrieval-Augmented Generation) with vector embeddings for automatic learning.

**How It Works:**
1. Admin uploads high-quality mining documents (NI 43-101 reports, feasibility studies)
2. System automatically chunks documents and creates vector embeddings using OpenAI text-embedding-3-small
3. When analyzing new documents, the AI retrieves similar training content via cosine similarity
4. Relevant training examples are automatically injected into prompts
5. No manual approval workflow - just upload and the AI improves

**Key Features:**
- Simplified 3-tab interface: Upload & Train, Training Library, Statistics
- Automatic document chunking (1500 chars with 200 char overlap)
- Vector similarity search with 0.5 threshold
- Minimum 2 results fallback when threshold not met
- Unique file identification using content hash (prevents duplicate filename collisions)
- Category and commodity filtering for targeted retrieval
- Real-time statistics tracking

**Categories:**
- 30-Geoscience Data
- 40-Spatial Data
- 50-3D and Analysis
- 60-Reporting
- 70-Literature
- 2024 Environmental Report on Ishkoday
- Geoscience Data
- Metallurgical Data
- Technical Reports

**Database Tables:**
- `training_embeddings` - Stores document chunks with vector embeddings
- `training_stats` - Global training statistics

**Integration:**
- `training_rag.py` - Core module for embedding creation, retrieval, and context building
- Integrated into `ai_analyzer.py` (Oreplot Light) and `advanced_ai_analyzer.py` (Oreplot Advanced)
- `build_enhanced_context()` retrieves relevant training content before analysis

**Legacy Tables (deprecated):**
- `training_collections`, `training_documents`, `training_chunks`, `training_examples`, `training_categories`

## External Dependencies

### AI Services
- **OpenAI API**: For AI analysis and document text extraction (GPT-5.1).

### Document Processing Libraries
- **PyPDF2**: For PDF text extraction (fallback).
- **python-docx**: For Microsoft Word document parsing.
- **openpyxl**: For Excel spreadsheet reading and exports.
- **pytesseract**: For OCR.
- **Pillow (PIL)**: For image handling in OCR.

### Web Framework
- **Streamlit**: For the web application and UI.

### Report Generation
- **FPDF**: For creating and formatting PDF reports.

### Reliability & Error Handling
- **tenacity**: For retry logic with exponential backoff for API calls.

### Database Interaction
- **SQLAlchemy**: ORM for database interactions.

### Market Data
- **Metals-API**: For real-time commodity pricing.

### Scheduler & Background Jobs
- **APScheduler**: For automated weekly comparables database updates.