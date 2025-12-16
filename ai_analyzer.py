import os
import json
from typing import Dict, List, Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

openai_client = OpenAI(
    api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
    base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
)


def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower()
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, "status_code") and exception.status_code == 429)
    )


class MiningProjectAnalyzer:
    
    SCORING_CATEGORIES = {
        "geology_prospectivity": {
            "name": "Geology / Prospectivity",
            "weight": 35,
            "description": "Geological favorability, mineralization indicators, ore body characteristics"
        },
        "resource_potential": {
            "name": "Resource Potential / Model Confidence",
            "weight": 20,
            "description": "Resource estimates, geological modeling quality, confidence level"
        },
        "economics": {
            "name": "Economics / Unit-Cost & Upside Case",
            "weight": 15,
            "description": "CAPEX/OPEX estimates, unit costs, financial projections, upside scenarios"
        },
        "legal_title": {
            "name": "Legal & Title Risk",
            "weight": 10,
            "description": "Ownership clarity, concession validity, encumbrances, chain of title"
        },
        "permitting_esg": {
            "name": "Permitting & ESG / Community",
            "weight": 10,
            "description": "Permits status, environmental compliance, community relations, social license"
        },
        "data_quality": {
            "name": "Data Quality & QAQC",
            "weight": 10,
            "description": "Sampling protocols, assay quality, QA/QC procedures, data integrity"
        }
    }
    
    SUSTAINABILITY_CATEGORIES = {
        "environmental": {
            "name": "Environmental Performance",
            "weight": 35,
            "description": "Water management, biodiversity protection, tailings/waste management, emissions control"
        },
        "social": {
            "name": "Social Performance",
            "weight": 30,
            "description": "Community relations, indigenous rights, worker safety, local employment, social license"
        },
        "governance": {
            "name": "Governance",
            "weight": 20,
            "description": "Ethics, transparency, anti-corruption, stakeholder engagement, board oversight"
        },
        "climate": {
            "name": "Climate & Energy",
            "weight": 15,
            "description": "Carbon footprint, renewable energy use, climate adaptation, emissions reduction targets"
        }
    }
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(7),
        wait=wait_exponential(multiplier=1, min=2, max=128),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    def analyze_documents(documents_text: List[Dict[str, str]]) -> Dict[str, Any]:
        drill_databases = [doc for doc in documents_text if doc.get('is_drill_database')]
        qaqc_scores = [db.get('qaqc_score', 0) for db in drill_databases if db.get('success')]
        avg_qaqc_score = sum(qaqc_scores) / len(qaqc_scores) if qaqc_scores else None
        
        combined_text = "\n\n".join([
            f"=== Document: {doc['file_name']} ===\n{doc['text']}"
            for doc in documents_text if doc.get('success', False)
        ])
        
        if not combined_text.strip():
            return {
                "error": "No valid text extracted from documents. Please check file formats.",
                "categories": {},
                "extraction_errors": [doc['file_name'] for doc in documents_text if not doc.get('success', False)]
            }
        
        qaqc_context = ""
        if avg_qaqc_score is not None:
            qaqc_context = f"\n\nIMPORTANT: Drill database QAQC analysis has been performed automatically. The average QAQC score is {avg_qaqc_score}/10. Use this score as a strong indicator for the Data Quality & QAQC category (item 6 below). Consider the QAQC report findings in your rationale."
        
        training_context = ""
        try:
            from training_rag import build_enhanced_context, get_training_statistics
            stats = get_training_statistics()
            if stats.get('total_chunks', 0) > 0:
                training_context = build_enhanced_context(
                    document_text=combined_text[:10000],
                    category=None,
                    commodity=None
                )
        except Exception:
            pass
        
        prompt = f"""You are a mining industry expert conducting due diligence on a mining project. Analyze the following documents using OBJECTIVE CRITERIA and EXPLICIT THRESHOLDS.

{training_context}

IMPORTANT: Search the ENTIRE document thoroughly for each category. NI 43-101 reports contain detailed information throughout. Pay special attention to:
- Section 7: Geology and Mineralization (grades, intercepts, deposit types)
- Section 14: Mineral Resource Estimates (resource tables, tonnage, grade)
- Section 16-17: Mining and Recovery Methods  
- Section 21-22: Costs and Economic Analysis (CAPEX, OPEX, NPV, IRR)
- Tables and appendices often contain the quantitative data

Documents:
{combined_text[:500000]}{qaqc_context}

OBJECTIVE SCORING CRITERIA (0-10 scale):

Score 9-10: Exceptional - ALL critical info present with high detail + quantitative data
Score 7-8: Good - MOST critical info present with quantitative data, minor gaps only
Score 5-6: Moderate - Key info present but lacks detail or has notable gaps
Score 3-4: Weak - Significant gaps, minimal quantitative data, incomplete analysis
Score 0-2: Poor - Critical info mostly missing, cannot assess project properly

SCORING CATEGORIES:

1. GEOLOGY / PROSPECTIVITY (35%)
   Score 9-10 requires: Quantitative grades (g/t), thickness/continuity, deposit type classification, genetic model, maps/sections, best intercepts
   Score 7-8 requires: Deposit type mentioned, some grades/intercepts, geological description
   Score 5-6 requires: Multiple zones identified, geological sections present
   Score 3-4 requires: Basic geology described, zones listed
   Score 0-2: Minimal geological information

2. RESOURCE POTENTIAL (20%)
   Score 9-10 requires: Resource statement (tonnes, grade, oz by category), classification details, model validation, sensitivity analysis
   Score 7-8 requires: Resource estimate present, domains defined, some validation
   Score 5-6 requires: Resource modeling discussed, no detailed numbers
   Score 3-4 requires: Mention of resource work, no estimates
   Score 0-2: No resource information

3. ECONOMICS (15%)
   Score 9-10 requires: CAPEX, OPEX, unit costs, NPV, IRR, payback, sensitivity
   Score 7-8 requires: Capital/operating costs present, some financial metrics
   Score 5-6 requires: Economic sections exist, minimal numbers
   Score 3-4 requires: Economics mentioned, no detail
   Score 0-2: No economic information

4. LEGAL & TITLE (10%)
   Score 9-10 requires: Tenure IDs, expiry dates, ownership %, royalty terms, no disputes
   Score 7-8 requires: Tenures mapped, ownership clear, agreements described
   Score 5-6 requires: Property description, some tenure info
   Score 3-4 requires: Basic location info, minimal title detail
   Score 0-2: No title information

5. PERMITTING & ESG (10%)
   Score 9-10 requires: Permit list with status/expiry, baseline studies, community agreements, closure plans
   Score 7-8 requires: Key permits identified, environmental/social sections present
   Score 5-6 requires: Permitting discussed, some environmental info
   Score 3-4 requires: Permits mentioned, minimal detail
   Score 0-2: No permitting information

6. DATA QUALITY & QAQC (10%)
   Score 9-10 requires: QA/QC performance metrics (CRM pass rates, duplicate precision), certified labs, data audit
   Score 7-8 requires: QA/QC procedures described, reputable labs, verification done
   Score 5-6 requires: Sampling methods described, labs identified
   Score 3-4 requires: Some mention of QA/QC
   Score 0-2: No QA/QC information

For each category, provide:
- A score from 0-10 using the EXACT thresholds above
- List ALL specific facts found (be thorough - minimum 5 items for scores 7+)
- List ALL missing critical information items
- Brief rationale citing the threshold criteria

Return JSON:
{{
  "project_name": "extracted project name or 'Unknown Project'",
  "categories": {{
    "geology_prospectivity": {{
      "score": <0-10>,
      "facts_found": ["fact1", "fact2", ...],
      "missing_info": ["missing1", "missing2", ...],
      "rationale": "brief explanation citing threshold"
    }},
    "resource_potential": {{ ... }},
    "economics": {{ ... }},
    "legal_title": {{ ... }},
    "permitting_esg": {{ ... }},
    "data_quality": {{ ... }}
  }},
  "overall_observations": "general notes about document quality"
}}

CRITICAL: Match your score to the threshold criteria. If critical info is missing, you CANNOT give a high score."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-5.1",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_completion_tokens=8192,
                reasoning_effort="high"
            )
            
            analysis = json.loads(response.choices[0].message.content or "{}")
            return analysis
        except Exception as e:
            return {
                "error": f"AI analysis failed: {str(e)}. Please try again or contact support if the issue persists.",
                "categories": {}
            }
    
    @staticmethod
    def generate_recommendations(analysis: Dict[str, Any], score: float) -> List[str]:
        recommendations = []
        
        if score >= 70:
            recommendations.append("✓ Strong project - recommend proceeding to term sheet negotiation")
            recommendations.append("✓ Consider fast-track due diligence process")
        elif score >= 50:
            recommendations.append("→ Moderate potential - proceed to deeper due diligence")
            recommendations.append("→ Recommend drill program or PEA to strengthen confidence")
            recommendations.append("→ Focus on filling critical data gaps identified below")
        else:
            recommendations.append("⚠ High risk - recommend restructuring deal terms")
            recommendations.append("⚠ Consider farm-out, lower valuation, or request more data")
            recommendations.append("⚠ Address major gaps before proceeding")
        
        categories = analysis.get('categories', {})
        for cat_key, cat_data in categories.items():
            if cat_data.get('score', 0) < 5:
                cat_name = MiningProjectAnalyzer.SCORING_CATEGORIES[cat_key]['name']
                recommendations.append(f"⚠ Critical gap in {cat_name} - score {cat_data.get('score', 0)}/10")
        
        return recommendations
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=64),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    def generate_executive_narrative(
        documents_text: List[Dict[str, str]],
        analysis: Dict[str, Any],
        score: float
    ) -> Dict[str, Any]:
        combined_text = "\n\n".join([
            f"=== Document: {doc['file_name']} ===\n{doc['text']}"
            for doc in documents_text if doc.get('success', False)
        ])[:20000]
        
        project_name = analysis.get('project_name', 'Unknown Project')
        
        prompt = f"""You are a senior mining investment analyst creating an executive summary narrative for: {project_name}

Based on the technical analysis (score: {score}/100) and document excerpts below, generate a strategic context narrative.

DOCUMENTS:
{combined_text}

TECHNICAL SCORES:
{json.dumps({k: v.get('score', 0) for k, v in analysis.get('categories', {}).items()}, indent=2)}

Generate a comprehensive executive narrative with:

1. PROJECT TIMELINE & HISTORY (2-3 sentences)
   - Key milestones (discovery, drilling campaigns, resource updates)
   - Ownership evolution and transaction history
   - Development stage progression

2. JURISDICTIONAL CONTEXT (2-3 sentences)
   - Country/region mining jurisdiction analysis
   - Political stability and mining policy
   - Infrastructure access and logistics
   - Permitting regime (timeline, complexity)

3. STRATEGIC SIGNALS (bullet list)
   - Government funding or strategic support
   - Critical minerals designation or defense interest
   - Major partnerships or offtake agreements
   - Proximity to infrastructure or producing mines
   - Brownfield vs greenfield advantages

4. STRATEGIC RECOMMENDATIONS (3-5 items)
   - Investment timing considerations
   - Deal structure guidance (JV, earn-in, outright acquisition)
   - Ownership clarity actions needed
   - Policy alignment opportunities
   - Risk mitigation priorities

Return JSON:
{{
  "executive_summary": "2-3 paragraph narrative tying together timeline, context, and positioning",
  "project_timeline": "concise timeline text",
  "jurisdictional_context": "jurisdiction analysis text",
  "strategic_signals": ["signal1", "signal2", ...],
  "strategic_recommendations": ["rec1", "rec2", "rec3", "rec4", "rec5"]
}}

Be specific. Use evidence from documents. If information is missing, note it explicitly."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-5.1",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_completion_tokens=4096,
                reasoning_effort="high",
                temperature=0
            )
            
            narrative = json.loads(response.choices[0].message.content or "{}")
            return narrative
        except Exception as e:
            return {
                "executive_summary": f"Project: {project_name}. Investment score: {score}/100. Narrative generation failed.",
                "project_timeline": "Timeline information not available.",
                "jurisdictional_context": "Jurisdictional analysis not available.",
                "strategic_signals": [],
                "strategic_recommendations": [
                    "Review technical due diligence findings",
                    "Conduct site visit for verification",
                    "Engage with management for missing data"
                ]
            }
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(7),
        wait=wait_exponential(multiplier=1, min=2, max=128),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    def analyze_sustainability(documents_text: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze documents for sustainability performance across ESG categories.
        Based on industry standards: ICMM, GRI, SASB, TSM frameworks.
        """
        combined_text = "\n\n".join([
            f"=== Document: {doc['file_name']} ===\n{doc['text']}"
            for doc in documents_text if doc.get('success', False)
        ])
        
        if not combined_text.strip():
            return {
                "error": "No valid text extracted for sustainability analysis",
                "sustainability_categories": {}
            }
        
        prompt = f"""You are a sustainability expert conducting ESG due diligence on a mining project. Analyze the following documents for sustainability performance.

DOCUMENTS:
{combined_text[:30000]}

SUSTAINABILITY CATEGORIES (based on ICMM, GRI, SASB standards):

1. ENVIRONMENTAL PERFORMANCE (Weight: 35%)
   - Water management (consumption, recycling, discharge quality)
   - Biodiversity protection (baseline studies, impact mitigation, rehabilitation plans)
   - Tailings & waste management (storage facility design, monitoring, closure plans)
   - Air quality & emissions control (dust, particulates, SO2/NOx)
   - Land use & rehabilitation commitments

2. SOCIAL PERFORMANCE (Weight: 30%)
   - Community relations & consultation programs
   - Indigenous peoples rights & engagement (if applicable)
   - Worker health & safety (fatality rates, LTIFR, safety protocols)
   - Local employment & skills development
   - Social impact assessments & mitigation plans
   - Resettlement procedures (if applicable)

3. GOVERNANCE (Weight: 20%)
   - Corporate ethics & anti-corruption policies
   - Board oversight of sustainability
   - Stakeholder engagement & transparency
   - Compliance & regulatory adherence
   - Grievance mechanisms
   - Public disclosure of sustainability data

4. CLIMATE & ENERGY (Weight: 15%)
   - GHG emissions baseline & reduction targets
   - Energy consumption & renewable energy use
   - Climate risk assessment & adaptation plans
   - Scope 1, 2, 3 emissions disclosure
   - Net-zero commitments or transition plans

For each category, provide:
- A score from 0-10 (0=poor/no evidence, 10=industry-leading)
- Key facts found supporting the score
- Missing critical information
- Brief rationale based on industry best practices

Return JSON:
{{
  "sustainability_categories": {{
    "environmental": {{
      "score": <0-10>,
      "facts_found": ["fact1", "fact2", ...],
      "missing_info": ["missing1", "missing2", ...],
      "rationale": "brief explanation"
    }},
    "social": {{ ... }},
    "governance": {{ ... }},
    "climate": {{ ... }}
  }},
  "overall_sustainability_notes": "general assessment of sustainability maturity"
}}

If information is sparse, give conservative scores (1-3) and list what's missing. Use evidence from documents."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-5.1",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_completion_tokens=8192,
                reasoning_effort="high"
            )
            
            sustainability_analysis = json.loads(response.choices[0].message.content or "{}")
            return sustainability_analysis
        except Exception as e:
            return {
                "error": f"Sustainability analysis failed: {str(e)}",
                "sustainability_categories": {}
            }
