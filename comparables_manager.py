from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models import ComparableProject
from typing import List, Dict, Any, Optional
from datetime import datetime
from format_utils import format_currency

class ComparablesManager:
    """Manager for Global Comparables Database operations"""
    
    @staticmethod
    def get_all_comparables(db: Session, filters: Dict[str, Any] = None) -> List[ComparableProject]:
        """Get all comparable projects with optional filters"""
        query = db.query(ComparableProject)
        
        if filters:
            if filters.get('commodity'):
                query = query.filter(ComparableProject.commodity.ilike(f"%{filters['commodity']}%"))
            
            if filters.get('country'):
                query = query.filter(ComparableProject.country.ilike(f"%{filters['country']}%"))
            
            if filters.get('project_stage'):
                query = query.filter(ComparableProject.project_stage == filters['project_stage'])
            
            if filters.get('min_score') is not None:
                query = query.filter(ComparableProject.overall_score >= filters['min_score'])
            
            if filters.get('max_score') is not None:
                query = query.filter(ComparableProject.overall_score <= filters['max_score'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        ComparableProject.name.ilike(search_term),
                        ComparableProject.company.ilike(search_term),
                        ComparableProject.location.ilike(search_term)
                    )
                )
        
        return query.order_by(ComparableProject.overall_score.desc()).all()
    
    @staticmethod
    def get_comparable_by_id(db: Session, comparable_id: int) -> Optional[ComparableProject]:
        """Get a specific comparable project by ID"""
        return db.query(ComparableProject).filter(ComparableProject.id == comparable_id).first()
    
    @staticmethod
    def get_similar_comparables(db: Session, commodity: str, project_stage: str = None, limit: int = 5) -> List[ComparableProject]:
        """Find similar comparable projects based on commodity and stage"""
        query = db.query(ComparableProject).filter(
            ComparableProject.commodity.ilike(f"%{commodity}%")
        )
        
        if project_stage:
            query = query.filter(ComparableProject.project_stage == project_stage)
        
        return query.order_by(ComparableProject.overall_score.desc()).limit(limit).all()
    
    @staticmethod
    def get_benchmark_stats(db: Session, commodity: str = None) -> Dict[str, Any]:
        """Get statistical benchmarks for comparison"""
        query = db.query(ComparableProject)
        
        if commodity:
            query = query.filter(ComparableProject.commodity.ilike(f"%{commodity}%"))
        
        stats = {
            'total_projects': query.count(),
            'avg_overall_score': query.with_entities(func.avg(ComparableProject.overall_score)).scalar() or 0,
            'avg_geology_score': query.with_entities(func.avg(ComparableProject.geology_score)).scalar() or 0,
            'avg_resource_score': query.with_entities(func.avg(ComparableProject.resource_score)).scalar() or 0,
            'avg_economics_score': query.with_entities(func.avg(ComparableProject.economics_score)).scalar() or 0,
            'avg_legal_score': query.with_entities(func.avg(ComparableProject.legal_score)).scalar() or 0,
            'avg_permitting_score': query.with_entities(func.avg(ComparableProject.permitting_score)).scalar() or 0,
            'avg_data_quality_score': query.with_entities(func.avg(ComparableProject.data_quality_score)).scalar() or 0,
            'avg_capex_millions': query.with_entities(func.avg(ComparableProject.capex_millions_usd)).scalar() or 0,
            'avg_irr_percent': query.with_entities(func.avg(ComparableProject.irr_percent)).scalar() or 0,
            'avg_npv_millions': query.with_entities(func.avg(ComparableProject.npv_millions_usd)).scalar() or 0,
        }
        
        return stats
    
    @staticmethod
    def compare_project_to_benchmarks(current_analysis: Dict[str, Any], comparables: List[ComparableProject]) -> Dict[str, Any]:
        """Compare a project's scores against comparable projects"""
        if not comparables:
            return {
                'comparison_available': False,
                'message': 'No comparable projects found for benchmarking'
            }
        
        comparable_scores = {
            'overall': [c.overall_score for c in comparables if c.overall_score],
            'geology': [c.geology_score for c in comparables if c.geology_score],
            'resource': [c.resource_score for c in comparables if c.resource_score],
            'economics': [c.economics_score for c in comparables if c.economics_score],
            'legal': [c.legal_score for c in comparables if c.legal_score],
            'permitting': [c.permitting_score for c in comparables if c.permitting_score],
            'data_quality': [c.data_quality_score for c in comparables if c.data_quality_score],
        }
        
        def get_percentile(value, scores_list):
            if not scores_list or value is None:
                return None
            scores_list = sorted(scores_list)
            count_below = sum(1 for s in scores_list if s < value)
            return round((count_below / len(scores_list)) * 100, 1)
        
        comparison = {
            'comparison_available': True,
            'comparables_count': len(comparables),
            'current_scores': {
                'overall': current_analysis.get('total_score'),
                'geology': current_analysis.get('geology_score'),
                'resource': current_analysis.get('resource_score'),
                'economics': current_analysis.get('economics_score'),
                'legal': current_analysis.get('legal_score'),
                'permitting': current_analysis.get('permitting_score'),
                'data_quality': current_analysis.get('data_quality_score'),
            },
            'percentiles': {
                'overall': get_percentile(current_analysis.get('total_score'), comparable_scores['overall']),
                'geology': get_percentile(current_analysis.get('geology_score'), comparable_scores['geology']),
                'resource': get_percentile(current_analysis.get('resource_score'), comparable_scores['resource']),
                'economics': get_percentile(current_analysis.get('economics_score'), comparable_scores['economics']),
                'legal': get_percentile(current_analysis.get('legal_score'), comparable_scores['legal']),
                'permitting': get_percentile(current_analysis.get('permitting_score'), comparable_scores['permitting']),
                'data_quality': get_percentile(current_analysis.get('data_quality_score'), comparable_scores['data_quality']),
            },
            'benchmarks': {
                'overall_avg': sum(comparable_scores['overall']) / len(comparable_scores['overall']) if comparable_scores['overall'] else 0,
                'geology_avg': sum(comparable_scores['geology']) / len(comparable_scores['geology']) if comparable_scores['geology'] else 0,
                'resource_avg': sum(comparable_scores['resource']) / len(comparable_scores['resource']) if comparable_scores['resource'] else 0,
                'economics_avg': sum(comparable_scores['economics']) / len(comparable_scores['economics']) if comparable_scores['economics'] else 0,
                'legal_avg': sum(comparable_scores['legal']) / len(comparable_scores['legal']) if comparable_scores['legal'] else 0,
                'permitting_avg': sum(comparable_scores['permitting']) / len(comparable_scores['permitting']) if comparable_scores['permitting'] else 0,
                'data_quality_avg': sum(comparable_scores['data_quality']) / len(comparable_scores['data_quality']) if comparable_scores['data_quality'] else 0,
            }
        }
        
        return comparison
    
    @staticmethod
    def format_comparable_for_display(comparable: ComparableProject) -> Dict[str, Any]:
        """Format a comparable project for UI display"""
        return {
            'id': comparable.id,
            'name': comparable.name,
            'company': comparable.company,
            'location': f"{comparable.location}, {comparable.country}" if comparable.location and comparable.country else comparable.country or comparable.location or 'Unknown',
            'commodity': comparable.commodity or 'N/A',
            'stage': comparable.project_stage or 'N/A',
            'resource': f"{comparable.total_resource_mt:.1f} Mt @ {comparable.grade:.2f} {comparable.grade_unit}" if comparable.total_resource_mt and comparable.grade else 'N/A',
            'capex': format_currency(comparable.capex_millions_usd, decimals=0) if comparable.capex_millions_usd else 'N/A',
            'npv': format_currency(comparable.npv_millions_usd, decimals=0) if comparable.npv_millions_usd else 'N/A',
            'irr': f"{comparable.irr_percent:.1f}%" if comparable.irr_percent else 'N/A',
            'overall_score': comparable.overall_score or 0,
            'scores': {
                'geology': comparable.geology_score or 0,
                'resource': comparable.resource_score or 0,
                'economics': comparable.economics_score or 0,
                'legal': comparable.legal_score or 0,
                'permitting': comparable.permitting_score or 0,
                'data_quality': comparable.data_quality_score or 0,
            },
            'data_source': comparable.data_source,
            'notes': comparable.notes
        }
