from database import get_db_session
from models import Project, Analysis, Document
from datetime import datetime
from typing import List, Dict, Any

class ProjectManager:
    
    @staticmethod
    def create_project(user_id: int, name: str, description: str = None, location: str = None, commodity: str = None):
        """Create a new mining project. Returns a dict representation."""
        with get_db_session() as session:
            project = Project(
                user_id=user_id,
                name=name,
                description=description,
                location=location,
                commodity=commodity,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(project)
            session.flush()
            session.refresh(project)
            return {
                'id': project.id,
                'user_id': project.user_id,
                'name': project.name,
                'description': project.description,
                'location': project.location,
                'commodity': project.commodity,
                'created_at': project.created_at,
                'updated_at': project.updated_at
            }
    
    @staticmethod
    def _format_findings(category_data: Dict[str, Any]) -> str:
        """Format category findings from AI analysis into readable text"""
        if not category_data:
            return ''
        
        findings_parts = []
        
        # Add rationale
        if category_data.get('rationale'):
            findings_parts.append(f"**Rationale:** {category_data['rationale']}")
        
        # Add facts found
        facts = category_data.get('facts_found', [])
        if facts:
            findings_parts.append("\n**Key Facts Found:**")
            for fact in facts:
                findings_parts.append(f"• {fact}")
        
        # Add missing information
        missing = category_data.get('missing_info', [])
        if missing:
            findings_parts.append("\n**Missing Information:**")
            for item in missing:
                findings_parts.append(f"• {item}")
        
        return '\n'.join(findings_parts) if findings_parts else category_data.get('findings', '')
    
    @staticmethod
    def save_analysis(project_id: int, analysis_data: Dict[str, Any], scoring_data: Dict[str, Any], 
                     recommendations: List[str], scoring_template_id: int = None, narrative_data: Dict[str, Any] = None,
                     sustainability_data: Dict[str, Any] = None, sustainability_scoring: Dict[str, Any] = None,
                     analysis_type: str = 'light_ai'):
        """Save an analysis result to the database. Returns a dict representation.
        
        Args:
            analysis_type: 'light_ai' or 'advanced_ai' to identify the analysis source
        """
        with get_db_session() as session:
            categories = analysis_data.get('categories', {})
            contributions = scoring_data.get('category_contributions', {})
            
            narrative_data = narrative_data or {}
            sustainability_data = sustainability_data or {}
            sustainability_scoring = sustainability_scoring or {}
            
            sust_categories = sustainability_data.get('sustainability_categories', {})
            sust_contributions = sustainability_scoring.get('category_contributions', {})
            
            analysis = Analysis(
                project_id=project_id,
                scoring_template_id=scoring_template_id,
                analysis_type=analysis_type,
                total_score=scoring_data['total_score'],
                risk_category=scoring_data.get('risk_band', scoring_data.get('risk_category', 'UNKNOWN')),
                probability_of_success=scoring_data['probability_of_success'],
                
                geology_score=categories.get('geology_prospectivity', {}).get('score', 0),
                geology_weight=contributions.get('geology_prospectivity', {}).get('weight', 0),
                geology_contribution=contributions.get('geology_prospectivity', {}).get('contribution', 0),
                geology_findings=ProjectManager._format_findings(categories.get('geology_prospectivity', {})),
                
                resource_score=categories.get('resource_potential', {}).get('score', 0),
                resource_weight=contributions.get('resource_potential', {}).get('weight', 0),
                resource_contribution=contributions.get('resource_potential', {}).get('contribution', 0),
                resource_findings=ProjectManager._format_findings(categories.get('resource_potential', {})),
                
                economics_score=categories.get('economics', {}).get('score', 0),
                economics_weight=contributions.get('economics', {}).get('weight', 0),
                economics_contribution=contributions.get('economics', {}).get('contribution', 0),
                economics_findings=ProjectManager._format_findings(categories.get('economics', {})),
                
                legal_score=categories.get('legal_title', {}).get('score', 0),
                legal_weight=contributions.get('legal_title', {}).get('weight', 0),
                legal_contribution=contributions.get('legal_title', {}).get('contribution', 0),
                legal_findings=ProjectManager._format_findings(categories.get('legal_title', {})),
                
                permitting_score=categories.get('permitting_esg', {}).get('score', 0),
                permitting_weight=contributions.get('permitting_esg', {}).get('weight', 0),
                permitting_contribution=contributions.get('permitting_esg', {}).get('contribution', 0),
                permitting_findings=ProjectManager._format_findings(categories.get('permitting_esg', {})),
                
                data_quality_score=categories.get('data_quality', {}).get('score', 0),
                data_quality_weight=contributions.get('data_quality', {}).get('weight', 0),
                data_quality_contribution=contributions.get('data_quality', {}).get('contribution', 0),
                data_quality_findings=ProjectManager._format_findings(categories.get('data_quality', {})),
                
                recommendations=recommendations,
                ai_analysis_raw=analysis_data,
                
                executive_summary=narrative_data.get('executive_summary'),
                strategic_recommendations=narrative_data.get('strategic_recommendations'),
                project_timeline=narrative_data.get('project_timeline'),
                jurisdictional_context=narrative_data.get('jurisdictional_context'),
                strategic_signals=narrative_data.get('strategic_signals'),
                
                sustainability_score=sustainability_scoring.get('sustainability_score'),
                environmental_score=sust_categories.get('environmental', {}).get('score'),
                environmental_weight=sust_contributions.get('environmental', {}).get('weight'),
                environmental_contribution=sust_contributions.get('environmental', {}).get('contribution'),
                environmental_findings=ProjectManager._format_findings(sust_categories.get('environmental', {})),
                
                social_score=sust_categories.get('social', {}).get('score'),
                social_weight=sust_contributions.get('social', {}).get('weight'),
                social_contribution=sust_contributions.get('social', {}).get('contribution'),
                social_findings=ProjectManager._format_findings(sust_categories.get('social', {})),
                
                governance_score=sust_categories.get('governance', {}).get('score'),
                governance_weight=sust_contributions.get('governance', {}).get('weight'),
                governance_contribution=sust_contributions.get('governance', {}).get('contribution'),
                governance_findings=ProjectManager._format_findings(sust_categories.get('governance', {})),
                
                climate_score=sust_categories.get('climate', {}).get('score'),
                climate_weight=sust_contributions.get('climate', {}).get('weight'),
                climate_contribution=sust_contributions.get('climate', {}).get('contribution'),
                climate_findings=ProjectManager._format_findings(sust_categories.get('climate', {})),
                
                created_at=datetime.utcnow()
            )
            session.add(analysis)
            session.flush()
            session.refresh(analysis)
            return {
                'id': analysis.id,
                'project_id': analysis.project_id,
                'total_score': analysis.total_score,
                'risk_category': analysis.risk_category,
                'analysis_type': analysis.analysis_type,
                'created_at': analysis.created_at
            }
    
    @staticmethod
    def save_documents(project_id: int, documents_data: List[Dict[str, Any]]):
        """Save uploaded documents metadata to the database."""
        with get_db_session() as session:
            for doc_data in documents_data:
                document = Document(
                    project_id=project_id,
                    file_name=doc_data.get('file_name', ''),
                    file_type=doc_data.get('file_type', ''),
                    file_size=doc_data.get('size', 0),
                    extracted_text=doc_data.get('text', ''),
                    extraction_success=doc_data.get('success', False),
                    extraction_error=doc_data.get('error', ''),
                    uploaded_at=datetime.utcnow()
                )
                session.add(document)
            session.flush()
    
    @staticmethod
    def get_user_projects(user_id: int, limit: int = 50):
        """Get all projects for a user."""
        with get_db_session() as session:
            projects = session.query(Project).filter(
                Project.user_id == user_id
            ).order_by(Project.updated_at.desc()).limit(limit).all()
            
            result = []
            for project in projects:
                result.append({
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'location': project.location,
                    'commodity': project.commodity,
                    'created_at': project.created_at,
                    'updated_at': project.updated_at,
                    'analysis_count': len(project.analyses)
                })
            return result
    
    @staticmethod
    def get_project_analyses(project_id: int):
        """Get all analyses for a project with full details for reports."""
        with get_db_session() as session:
            analyses = session.query(Analysis).filter(
                Analysis.project_id == project_id
            ).order_by(Analysis.created_at.desc()).all()
            
            result = []
            for analysis in analyses:
                result.append({
                    'id': analysis.id,
                    'total_score': analysis.total_score,
                    'risk_category': analysis.risk_category,
                    'probability_of_success': analysis.probability_of_success,
                    'analysis_type': analysis.analysis_type or 'light_ai',
                    'created_at': analysis.created_at,
                    'recommendations': analysis.recommendations,
                    # Include all category details for reports
                    'geology_score': analysis.geology_score,
                    'geology_weight': analysis.geology_weight,
                    'geology_contribution': analysis.geology_contribution,
                    'geology_findings': analysis.geology_findings,
                    'resource_score': analysis.resource_score,
                    'resource_weight': analysis.resource_weight,
                    'resource_contribution': analysis.resource_contribution,
                    'resource_findings': analysis.resource_findings,
                    'economics_score': analysis.economics_score,
                    'economics_weight': analysis.economics_weight,
                    'economics_contribution': analysis.economics_contribution,
                    'economics_findings': analysis.economics_findings,
                    'legal_score': analysis.legal_score,
                    'legal_weight': analysis.legal_weight,
                    'legal_contribution': analysis.legal_contribution,
                    'legal_findings': analysis.legal_findings,
                    'permitting_score': analysis.permitting_score,
                    'permitting_weight': analysis.permitting_weight,
                    'permitting_contribution': analysis.permitting_contribution,
                    'permitting_findings': analysis.permitting_findings,
                    'data_quality_score': analysis.data_quality_score,
                    'data_quality_weight': analysis.data_quality_weight,
                    'data_quality_contribution': analysis.data_quality_contribution,
                    'data_quality_findings': analysis.data_quality_findings,
                    # Include raw AI analysis for structured category data
                    'ai_analysis_raw': analysis.ai_analysis_raw,
                    # Sustainability scores
                    'sustainability_score': analysis.sustainability_score,
                    'environmental_score': analysis.environmental_score,
                    'environmental_weight': analysis.environmental_weight,
                    'environmental_contribution': analysis.environmental_contribution,
                    'social_score': analysis.social_score,
                    'social_weight': analysis.social_weight,
                    'social_contribution': analysis.social_contribution,
                    'governance_score': analysis.governance_score,
                    'governance_weight': analysis.governance_weight,
                    'governance_contribution': analysis.governance_contribution,
                    'climate_score': analysis.climate_score,
                    'climate_weight': analysis.climate_weight,
                    'climate_contribution': analysis.climate_contribution
                })
            return result
    
    @staticmethod
    def get_analysis_details(analysis_id: int):
        """Get complete details of a specific analysis."""
        with get_db_session() as session:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            
            if not analysis:
                return None
            
            # Build base categories with scores and weights
            categories = {
                'geology_prospectivity': {
                    'score': analysis.geology_score,
                    'weight': analysis.geology_weight,
                    'contribution': analysis.geology_contribution,
                    'findings': analysis.geology_findings
                },
                'resource_potential': {
                    'score': analysis.resource_score,
                    'weight': analysis.resource_weight,
                    'contribution': analysis.resource_contribution,
                    'findings': analysis.resource_findings
                },
                'economics': {
                    'score': analysis.economics_score,
                    'weight': analysis.economics_weight,
                    'contribution': analysis.economics_contribution,
                    'findings': analysis.economics_findings
                },
                'legal_title': {
                    'score': analysis.legal_score,
                    'weight': analysis.legal_weight,
                    'contribution': analysis.legal_contribution,
                    'findings': analysis.legal_findings
                },
                'permitting_esg': {
                    'score': analysis.permitting_score,
                    'weight': analysis.permitting_weight,
                    'contribution': analysis.permitting_contribution,
                    'findings': analysis.permitting_findings
                },
                'data_quality': {
                    'score': analysis.data_quality_score,
                    'weight': analysis.data_quality_weight,
                    'contribution': analysis.data_quality_contribution,
                    'findings': analysis.data_quality_findings
                }
            }
            
            # Merge detailed category data from ai_analysis_raw if available
            if analysis.ai_analysis_raw and isinstance(analysis.ai_analysis_raw, dict):
                raw_categories = analysis.ai_analysis_raw.get('categories', {})
                for cat_key in categories.keys():
                    if cat_key in raw_categories:
                        raw_cat_data = raw_categories[cat_key]
                        # Add rationale, facts_found, and missing_info from raw data
                        if raw_cat_data.get('rationale'):
                            categories[cat_key]['rationale'] = raw_cat_data['rationale']
                        if raw_cat_data.get('facts_found'):
                            categories[cat_key]['facts_found'] = raw_cat_data['facts_found']
                        if raw_cat_data.get('missing_info'):
                            categories[cat_key]['missing_info'] = raw_cat_data['missing_info']
            
            # Build sustainability categories if data exists
            sustainability_scoring = None
            sustainability_analysis = None
            
            if analysis.sustainability_score is not None:
                sustainability_categories = {
                    'environmental': {
                        'score': analysis.environmental_score,
                        'weight': analysis.environmental_weight,
                        'contribution': analysis.environmental_contribution,
                        'findings': analysis.environmental_findings
                    },
                    'social': {
                        'score': analysis.social_score,
                        'weight': analysis.social_weight,
                        'contribution': analysis.social_contribution,
                        'findings': analysis.social_findings
                    },
                    'governance': {
                        'score': analysis.governance_score,
                        'weight': analysis.governance_weight,
                        'contribution': analysis.governance_contribution,
                        'findings': analysis.governance_findings
                    },
                    'climate': {
                        'score': analysis.climate_score,
                        'weight': analysis.climate_weight,
                        'contribution': analysis.climate_contribution,
                        'findings': analysis.climate_findings
                    }
                }
                
                from scoring_engine import ScoringEngine
                sustainability_scoring = ScoringEngine.calculate_sustainability_score(sustainability_categories)
                sustainability_analysis = {'sustainability_categories': sustainability_categories}
            
            return {
                'id': analysis.id,
                'project_id': analysis.project_id,
                'total_score': analysis.total_score,
                'risk_category': analysis.risk_category,
                'probability_of_success': analysis.probability_of_success,
                'analysis_type': analysis.analysis_type or 'light_ai',
                'categories': categories,
                'recommendations': analysis.recommendations,
                'ai_analysis_raw': analysis.ai_analysis_raw,
                'sustainability_scoring': sustainability_scoring,
                'sustainability_analysis': sustainability_analysis,
                'created_at': analysis.created_at
            }
    
    @staticmethod
    def get_project_documents(project_id: int):
        """Get all documents for a project."""
        with get_db_session() as session:
            documents = session.query(Document).filter(
                Document.project_id == project_id
            ).order_by(Document.uploaded_at.desc()).all()
            
            result = []
            for doc in documents:
                result.append({
                    'id': doc.id,
                    'file_name': doc.file_name,
                    'file_type': doc.file_type,
                    'file_size': doc.file_size,
                    'extraction_success': doc.extraction_success,
                    'uploaded_at': doc.uploaded_at
                })
            return result
