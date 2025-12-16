from datetime import datetime
from typing import Dict, Any, List
from format_utils import format_currency
from fpdf import FPDF


def sanitize_for_pdf(text: str) -> str:
    """Replace Unicode characters that FPDF can't handle with ASCII equivalents."""
    if not text:
        return ""
    
    replacements = {
        '✓': '[+]',
        '✗': '[x]',
        '→': '->',
        '⚠': '[!]',
        '💎': '',
        '⛰️': '',
        '💰': '',
        '⚖️': '',
        '🌿': '',
        '📊': '',
        '−': '-',
        '–': '-',
        '—': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        'Σ': 'Sum',
        '×': 'x',
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    
    try:
        text = text.encode('latin-1', errors='ignore').decode('latin-1')
    except:
        pass
    
    if len(text) > 500:
        text = text[:497] + "..."
    
    return text


class MiningDueDiligenceReport(FPDF):
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Mining Due Diligence Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title: str):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, sanitize_for_pdf(title), 0, 1, 'L', True)
        self.ln(4)
    
    def section_title(self, title: str):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, sanitize_for_pdf(title), 0, 1, 'L')
        self.ln(2)
    
    def body_text(self, text: str):
        self.set_font('Arial', '', 11)
        try:
            self.multi_cell(190, 6, sanitize_for_pdf(text))
        except:
            self.multi_cell(190, 6, "Error rendering text")
        self.ln(2)
    
    def add_bullet_list(self, items: List[str]):
        self.set_font('Arial', '', 10)
        for item in items:
            try:
                self.multi_cell(190, 6, sanitize_for_pdf(f'  - {item}'))
            except:
                continue


class ReportGenerator:
    
    @staticmethod
    def generate_pdf_report(
        project_name: str,
        analysis: Dict[str, Any],
        scoring_result: Dict[str, Any],
        uploaded_files: List[str],
        recommendations: List[str],
        narrative: Dict[str, Any] = None,
        comparables: List[Dict[str, Any]] = None,
        sustainability_analysis: Dict[str, Any] = None,
        sustainability_scoring: Dict[str, Any] = None,
        advanced_valuation: Dict[str, Any] = None,
        analysis_type: str = 'light_ai'
    ) -> bytes:
        try:
            pdf = MiningDueDiligenceReport()
            pdf.add_page()
        except Exception as e:
            print(f"Error initializing PDF: {e}")
            raise
        
        # Add AI type indicator at the top
        ai_type_display = "Oreplot Advanced Analysis" if analysis_type == 'advanced_ai' else "Oreplot Light Analysis"
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f'Analysis Type: {ai_type_display}', 0, 1, 'R')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.chapter_title('Executive Summary')
        pdf.section_title(f'Project: {sanitize_for_pdf(project_name)}')
        pdf.body_text(f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        pdf.ln(5)
        
        if narrative and narrative.get('executive_summary'):
            pdf.section_title('Strategic Overview')
            pdf.body_text(sanitize_for_pdf(narrative['executive_summary']))
            pdf.ln(5)
        
        pdf.chapter_title('Dual Scoring System')
        
        pdf.section_title('Investment Score')
        pdf.set_font('Arial', 'B', 24)
        score_color = (0, 150, 0) if scoring_result['total_score'] >= 70 else (255, 140, 0) if scoring_result['total_score'] >= 50 else (200, 0, 0)
        pdf.set_text_color(*score_color)
        pdf.cell(0, 15, f"{scoring_result['total_score']} / 100", 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Risk Band: {scoring_result['risk_band']}", 0, 1, 'C')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f"Probability of Success: {scoring_result['probability_of_success']*100:.2f}%", 0, 1, 'C')
        pdf.ln(8)
        
        if sustainability_scoring:
            pdf.section_title('Sustainability Score')
            pdf.set_font('Arial', 'B', 24)
            sust_score = sustainability_scoring['sustainability_score']
            sust_color = (0, 150, 0) if sust_score >= 80 else (100, 180, 150) if sust_score >= 65 else (255, 140, 0) if sust_score >= 50 else (200, 0, 0)
            pdf.set_text_color(*sust_color)
            pdf.cell(0, 15, f"{sust_score} / 100", 0, 1, 'C')
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f"Rating: {sustainability_scoring['rating']}", 0, 1, 'C')
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, sanitize_for_pdf(sustainability_scoring['description']), 0, 1, 'C')
        
        pdf.ln(5)
        
        pdf.chapter_title('Score Breakdown by Category')
        
        category_names = {
            "geology_prospectivity": "Geology / Prospectivity",
            "resource_potential": "Resource Potential / Model Confidence",
            "economics": "Economics / Unit-Cost & Upside",
            "legal_title": "Legal & Title Risk",
            "permitting_esg": "Permitting & ESG / Community",
            "data_quality": "Data Quality & QAQC"
        }
        
        for cat_key, cat_contrib in scoring_result['category_contributions'].items():
            cat_name = category_names.get(cat_key, cat_key)
            pdf.section_title(f"{cat_name}")
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, f"Raw Score: {cat_contrib['raw_score']}/10  |  Weight: {cat_contrib['weight']}%  |  Contribution: {cat_contrib['contribution']}", 0, 1)
            
            cat_data = analysis.get('categories', {}).get(cat_key, {})
            
            if cat_data.get('rationale'):
                pdf.set_font('Arial', 'I', 10)
                try:
                    pdf.multi_cell(190, 5, sanitize_for_pdf(f"Rationale: {cat_data['rationale']}"))
                except:
                    pass
            
            if cat_data.get('facts_found'):
                pdf.set_font('Arial', '', 9)
                pdf.cell(0, 5, "Evidence Found:", 0, 1)
                for fact in cat_data['facts_found'][:5]:
                    try:
                        sanitized_fact = sanitize_for_pdf(str(fact))
                        pdf.multi_cell(190, 5, f'  [+] {sanitized_fact}')
                    except:
                        continue
            
            if cat_data.get('missing_info'):
                pdf.set_font('Arial', 'B', 9)
                pdf.set_text_color(200, 0, 0)
                pdf.cell(0, 5, "Missing Information:", 0, 1)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Arial', '', 9)
                for missing in cat_data['missing_info'][:5]:
                    try:
                        sanitized_missing = sanitize_for_pdf(str(missing))
                        pdf.multi_cell(190, 5, f'  [x] {sanitized_missing}')
                    except:
                        continue
            
            pdf.ln(3)
        
        if sustainability_scoring and sustainability_analysis:
            pdf.add_page()
            pdf.chapter_title('Sustainability Category Breakdown')
            
            sustainability_category_names = {
                "environmental": "Environmental Performance",
                "social": "Social Performance",
                "governance": "Governance",
                "climate": "Climate & Energy"
            }
            
            sust_categories = sustainability_analysis.get('sustainability_categories', {})
            sust_contributions = sustainability_scoring.get('category_contributions', {})
            
            for cat_key, cat_contrib in sust_contributions.items():
                cat_name = sustainability_category_names.get(cat_key, cat_key)
                pdf.section_title(f"{cat_name}")
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"Raw Score: {cat_contrib['raw_score']}/10  |  Weight: {cat_contrib['weight']}%  |  Contribution: {cat_contrib['contribution']}", 0, 1)
                
                cat_data = sust_categories.get(cat_key, {})
                
                if cat_data.get('rationale'):
                    pdf.set_font('Arial', 'I', 10)
                    try:
                        pdf.multi_cell(190, 5, sanitize_for_pdf(f"Rationale: {cat_data['rationale']}"))
                    except:
                        pass
                
                if cat_data.get('facts_found'):
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(0, 5, "Evidence Found:", 0, 1)
                    for fact in cat_data['facts_found'][:5]:
                        try:
                            sanitized_fact = sanitize_for_pdf(str(fact))
                            pdf.multi_cell(190, 5, f'  [+] {sanitized_fact}')
                        except:
                            continue
                
                if cat_data.get('missing_info'):
                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_text_color(200, 0, 0)
                    pdf.cell(0, 5, "Missing Information:", 0, 1)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font('Arial', '', 9)
                    for missing in cat_data['missing_info'][:5]:
                        try:
                            sanitized_missing = sanitize_for_pdf(str(missing))
                            pdf.multi_cell(190, 5, f'  [x] {sanitized_missing}')
                        except:
                            continue
                
                pdf.ln(3)
            
            if sustainability_analysis.get('overall_sustainability_notes'):
                pdf.section_title('Overall Sustainability Assessment')
                pdf.body_text(sanitize_for_pdf(sustainability_analysis['overall_sustainability_notes']))
                pdf.ln(5)
        
        pdf.add_page()
        
        if narrative and narrative.get('strategic_signals'):
            pdf.chapter_title('Strategic Signals & Context')
            if narrative.get('project_timeline'):
                pdf.section_title('Project Timeline')
                pdf.body_text(sanitize_for_pdf(narrative['project_timeline']))
                pdf.ln(3)
            
            if narrative.get('jurisdictional_context'):
                pdf.section_title('Jurisdictional Context')
                pdf.body_text(sanitize_for_pdf(narrative['jurisdictional_context']))
                pdf.ln(3)
            
            pdf.section_title('Key Strategic Signals')
            pdf.add_bullet_list(narrative['strategic_signals'])
            pdf.ln(5)
        
        if narrative and narrative.get('strategic_recommendations'):
            pdf.chapter_title('Strategic Recommendations')
            pdf.add_bullet_list(narrative['strategic_recommendations'])
            pdf.ln(5)
        
        pdf.chapter_title('Technical Recommendations & Next Steps')
        pdf.add_bullet_list(recommendations)
        pdf.ln(5)
        
        if comparables and len(comparables) > 0:
            pdf.add_page()
            pdf.chapter_title('Comparable Projects Benchmarking')
            pdf.body_text(f"This project has been benchmarked against {len(comparables)} similar mining projects:")
            pdf.ln(3)
            
            for idx, comp in enumerate(comparables, 1):
                pdf.section_title(f"{idx}. {sanitize_for_pdf(comp.get('name', 'Unknown'))}")
                pdf.set_font('Arial', '', 10)
                
                details = []
                if comp.get('company'):
                    details.append(f"Company: {comp['company']}")
                if comp.get('location'):
                    details.append(f"Location: {comp['location']}")
                if comp.get('commodity'):
                    details.append(f"Commodity: {comp['commodity']}")
                if comp.get('project_stage'):
                    details.append(f"Stage: {comp['project_stage']}")
                if comp.get('geology_type'):
                    details.append(f"Deposit Type: {comp['geology_type']}")
                
                pdf.multi_cell(190, 5, sanitize_for_pdf(' | '.join(details)))
                pdf.ln(2)
                
                metrics = []
                if comp.get('total_resource_mt'):
                    metrics.append(f"Resource: {comp['total_resource_mt']:.1f} Mt")
                if comp.get('grade') and comp.get('grade_unit'):
                    metrics.append(f"Grade: {comp['grade']:.2f} {comp['grade_unit']}")
                if comp.get('npv_millions_usd'):
                    metrics.append(f"NPV: ${comp['npv_millions_usd']:.0f}M")
                if comp.get('irr_percent'):
                    metrics.append(f"IRR: {comp['irr_percent']:.1f}%")
                if comp.get('capex_millions_usd'):
                    metrics.append(f"CAPEX: ${comp['capex_millions_usd']:.0f}M")
                
                if metrics:
                    pdf.set_font('Arial', 'I', 9)
                    pdf.multi_cell(190, 5, sanitize_for_pdf('  ' + ' | '.join(metrics)))
                
                if comp.get('similarity_score'):
                    pdf.set_font('Arial', 'B', 9)
                    pdf.cell(0, 5, f"  Similarity Score: {comp['similarity_score']*100:.0f}%", 0, 1)
                
                pdf.ln(3)

        if advanced_valuation:
            pdf.add_page()
            pdf.chapter_title('Advanced AI Valuation Analysis')
            pdf.body_text("PwC-style mining valuation using multiple methodologies:")
            pdf.ln(3)
            
            if advanced_valuation.get('market_multiples'):
                mm = advanced_valuation['market_multiples']
                pdf.section_title('Market Multiples (EV/Resource)')
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"Commodity: {mm.get('commodity', 'N/A')} | Category: {mm.get('resource_category', 'N/A')}", 0, 1)
                pdf.cell(0, 6, f"Resource Estimate: {mm.get('resource_estimate', 0):,.0f}", 0, 1)
                pdf.cell(0, 6, f"Base Multiple: ${mm.get('base_multiple', 0):.2f}/unit | Adjusted Multiple: ${mm.get('final_multiple', 0):.2f}/unit", 0, 1)
                
                if mm.get('value_range'):
                    vr = mm['value_range']
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 8, f"Implied Value: {format_currency(vr.get('mid', 0)/1e6, decimals=1)} (Range: {format_currency(vr.get('low', 0)/1e6, decimals=1)} - {format_currency(vr.get('high', 0)/1e6, decimals=1)})", 0, 1)
                pdf.ln(3)
            
            if advanced_valuation.get('kilburn'):
                kb = advanced_valuation['kilburn']
                pdf.section_title('Kilburn Method (Cost Approach)')
                pdf.set_font('Arial', '', 10)
                
                gr = kb.get('geoscientific_rating', {})
                pdf.cell(0, 6, f"Geoscientific Rating: {gr.get('composite_rating', 0):.2f}/4.0 ({gr.get('category', 'N/A').replace('_', ' ').title()})", 0, 1)
                pdf.cell(0, 6, f"PEM Multiplier: {kb.get('pem', 0):.2f}x", 0, 1)
                
                if kb.get('mee_valuation'):
                    mee = kb['mee_valuation']
                    pdf.cell(0, 6, f"MEE Appraised Value: ${mee.get('appraised_value', 0):,.0f}", 0, 1)
                
                if kb.get('bac_valuation'):
                    bac = kb['bac_valuation']
                    pdf.cell(0, 6, f"BAC Appraised Value: ${bac.get('appraised_value', 0):,.0f}", 0, 1)
                
                if kb.get('preferred_valuation'):
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 8, f"Preferred Valuation: ${kb['preferred_valuation']:,.0f} ({kb.get('preferred_methodology', 'N/A')})", 0, 1)
                pdf.ln(3)
            
            if advanced_valuation.get('monte_carlo'):
                mc = advanced_valuation['monte_carlo']
                pdf.section_title('Monte Carlo Risk Modeling')
                pdf.set_font('Arial', '', 10)
                
                inputs = mc.get('input_parameters', {})
                pdf.cell(0, 6, f"Commodity: {mc.get('commodity', 'N/A')} | Project Life: {inputs.get('project_life', 0)} years", 0, 1)
                pdf.cell(0, 6, f"Simulations: {inputs.get('num_simulations', 0):,} | Discount Rate: {inputs.get('discount_rate', 0)*100:.1f}%", 0, 1)
                
                npv = mc.get('npv_statistics', {})
                pdf.ln(2)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 6, "NPV Distribution:", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 6, f"  Mean NPV: {format_currency(npv.get('mean', 0)/1e6, decimals=1)} | Median NPV: {format_currency(npv.get('median', 0)/1e6, decimals=1)}", 0, 1)
                pdf.cell(0, 6, f"  P10: {format_currency(npv.get('p10', 0)/1e6, decimals=1)} | P90: {format_currency(npv.get('p90', 0)/1e6, decimals=1)}", 0, 1)
                pdf.cell(0, 6, f"  Probability of Positive NPV: {npv.get('prob_positive', 0)*100:.1f}%", 0, 1)
                pdf.cell(0, 6, f"  Value at Risk (5%): {format_currency(npv.get('var_5', 0)/1e6, decimals=1)}", 0, 1)
                
                if mc.get('real_options_value'):
                    pdf.ln(2)
                    pdf.set_font('Arial', 'B', 11)
                    pdf.cell(0, 8, f"Real Options Value: {format_currency(mc['real_options_value']/1e6, decimals=1)} (+{mc.get('option_premium_pct', 0):.0f}% vs static NPV)", 0, 1)
                pdf.ln(3)
            
            if advanced_valuation.get('valuation_summary'):
                pdf.section_title('Valuation Summary')
                summary = advanced_valuation['valuation_summary']
                pdf.set_font('Arial', 'B', 12)
                if summary.get('recommended_value'):
                    pdf.cell(0, 10, f"Recommended Fair Value: {format_currency(summary['recommended_value']/1e6, decimals=1)}", 0, 1)
                if summary.get('value_range'):
                    pdf.set_font('Arial', '', 10)
                    vr = summary['value_range']
                    pdf.cell(0, 6, f"Range: {format_currency(vr.get('low', 0)/1e6, decimals=1)} to {format_currency(vr.get('high', 0)/1e6, decimals=1)}", 0, 1)
                if summary.get('methodology_note'):
                    pdf.set_font('Arial', 'I', 9)
                    pdf.multi_cell(190, 5, sanitize_for_pdf(summary['methodology_note']))
                pdf.ln(3)
        
        pdf.chapter_title('Documents Analyzed')
        pdf.set_font('Arial', '', 10)
        for i, file_name in enumerate(uploaded_files, 1):
            pdf.cell(0, 6, sanitize_for_pdf(f"{i}. {file_name}"), 0, 1)
        pdf.ln(5)
        
        if analysis.get('overall_observations'):
            pdf.chapter_title('Overall Observations')
            pdf.body_text(sanitize_for_pdf(analysis['overall_observations']))
        
        pdf.add_page()
        pdf.chapter_title('Assessment Methodology')
        pdf.body_text("This report uses a weighted scoring methodology with the following categories:")
        pdf.ln(2)
        
        methodology_items = [
            "Geology / Prospectivity (35% weight) - Geological favorability and ore body characteristics",
            "Resource Potential / Model Confidence (20% weight) - Resource estimates and modeling quality",
            "Economics / Unit-Cost & Upside (15% weight) - Financial projections and unit costs",
            "Legal & Title Risk (10% weight) - Ownership clarity and concession validity",
            "Permitting & ESG / Community (10% weight) - Permits status and community relations",
            "Data Quality & QAQC (10% weight) - Sampling protocols and data integrity"
        ]
        pdf.add_bullet_list(methodology_items)
        pdf.ln(5)
        
        pdf.body_text("Formula: Investment Score = Sum(Score_i / 10 x Weight_i)")
        pdf.body_text("Probability of Success = Investment Score / 100")
        pdf.ln(5)
        
        pdf.section_title("Score Interpretation:")
        pdf.body_text("> 70: Favourable - Fast-track or term sheet")
        pdf.body_text("50-70: Moderate - Proceed to deeper due diligence")
        pdf.body_text("< 50: High Risk - Reject or restructure")
        
        try:
            # Use dest='S' to return as string instead of printing to stdout
            pdf_output = pdf.output(dest='S').encode('latin-1')
            return pdf_output
        except Exception as e:
            print(f"Error generating PDF output: {e}")
            import traceback
            traceback.print_exc()
            raise
