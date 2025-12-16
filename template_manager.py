from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from database import get_db_session
from models import ScoringTemplate


class TemplateManager:
    """Manages CRUD operations for scoring templates"""
    
    DEFAULT_WEIGHTS = {
        'geology_prospectivity': 35,
        'resource_potential': 20,
        'economics': 15,
        'legal_title': 10,
        'permitting_esg': 10,
        'data_quality': 10
    }
    
    @staticmethod
    def create_template(
        user_id: int,
        name: str,
        description: str = "",
        weights: Optional[Dict[str, float]] = None,
        is_default: bool = False
    ) -> Dict[str, Any]:
        """Create a new scoring template"""
        if weights is None:
            weights = TemplateManager.DEFAULT_WEIGHTS.copy()
        
        # Validate weights sum to 100
        total_weight = sum(weights.values())
        if abs(total_weight - 100) > 0.01:
            raise ValueError(f"Weights must sum to 100. Current sum: {total_weight}")
        
        with get_db_session() as db:
            # If setting as default, unset other defaults for this user
            if is_default:
                db.query(ScoringTemplate).filter(
                    ScoringTemplate.user_id == user_id,
                    ScoringTemplate.is_default == True
                ).update({'is_default': False})
            
            template = ScoringTemplate(
                user_id=user_id,
                name=name,
                description=description,
                is_default=is_default,
                geology_weight=weights.get('geology_prospectivity', 35) / 100,
                resource_weight=weights.get('resource_potential', 20) / 100,
                economics_weight=weights.get('economics', 15) / 100,
                legal_weight=weights.get('legal_title', 10) / 100,
                permitting_weight=weights.get('permitting_esg', 10) / 100,
                data_quality_weight=weights.get('data_quality', 10) / 100
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            return TemplateManager._to_dict(template)
    
    @staticmethod
    def get_template(template_id: int) -> Optional[Dict[str, Any]]:
        """Get a template by ID"""
        with get_db_session() as db:
            template = db.query(ScoringTemplate).filter(
                ScoringTemplate.id == template_id
            ).first()
            
            if template:
                return TemplateManager._to_dict(template)
            return None
    
    @staticmethod
    def get_user_templates(user_id: int) -> List[Dict[str, Any]]:
        """Get all templates for a user"""
        with get_db_session() as db:
            templates = db.query(ScoringTemplate).filter(
                ScoringTemplate.user_id == user_id
            ).order_by(ScoringTemplate.is_default.desc(), ScoringTemplate.created_at.desc()).all()
            
            return [TemplateManager._to_dict(t) for t in templates]
    
    @staticmethod
    def get_default_template(user_id: int) -> Optional[Dict[str, Any]]:
        """Get the user's default template"""
        with get_db_session() as db:
            template = db.query(ScoringTemplate).filter(
                ScoringTemplate.user_id == user_id,
                ScoringTemplate.is_default == True
            ).first()
            
            if template:
                return TemplateManager._to_dict(template)
            return None
    
    @staticmethod
    def update_template(
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        is_default: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update an existing template"""
        with get_db_session() as db:
            template = db.query(ScoringTemplate).filter(
                ScoringTemplate.id == template_id
            ).first()
            
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            if name is not None:
                template.name = name
            
            if description is not None:
                template.description = description
            
            if weights is not None:
                # Validate weights sum to 100
                total_weight = sum(weights.values())
                if abs(total_weight - 100) > 0.01:
                    raise ValueError(f"Weights must sum to 100. Current sum: {total_weight}")
                
                template.geology_weight = weights.get('geology_prospectivity', 35) / 100
                template.resource_weight = weights.get('resource_potential', 20) / 100
                template.economics_weight = weights.get('economics', 15) / 100
                template.legal_weight = weights.get('legal_title', 10) / 100
                template.permitting_weight = weights.get('permitting_esg', 10) / 100
                template.data_quality_weight = weights.get('data_quality', 10) / 100
            
            if is_default is not None and is_default:
                # Unset other defaults for this user
                db.query(ScoringTemplate).filter(
                    ScoringTemplate.user_id == template.user_id,
                    ScoringTemplate.id != template_id,
                    ScoringTemplate.is_default == True
                ).update({'is_default': False})
                template.is_default = True
            elif is_default is not None and not is_default:
                template.is_default = False
            
            db.commit()
            db.refresh(template)
            
            return TemplateManager._to_dict(template)
    
    @staticmethod
    def delete_template(template_id: int) -> Dict[str, Any]:
        """
        Delete a template. Returns dict with 'success' and 'message' keys.
        Prevents deletion if template is in use by analyses.
        """
        from models import Analysis
        
        with get_db_session() as db:
            template = db.query(ScoringTemplate).filter(
                ScoringTemplate.id == template_id
            ).first()
            
            if not template:
                return {'success': False, 'message': 'Template not found'}
            
            # Check if template is in use
            analyses_count = db.query(Analysis).filter(
                Analysis.scoring_template_id == template_id
            ).count()
            
            if analyses_count > 0:
                return {
                    'success': False, 
                    'message': f'Cannot delete template in use by {analyses_count} analysis(es). Remove references first.'
                }
            
            db.delete(template)
            db.commit()
            return {'success': True, 'message': 'Template deleted successfully'}
    
    @staticmethod
    def _to_dict(template: ScoringTemplate) -> Dict[str, Any]:
        """Convert template to dictionary with weights as percentages"""
        return {
            'id': template.id,
            'user_id': template.user_id,
            'name': template.name,
            'description': template.description,
            'is_default': template.is_default,
            'weights': {
                'geology_prospectivity': round(template.geology_weight * 100, 1),
                'resource_potential': round(template.resource_weight * 100, 1),
                'economics': round(template.economics_weight * 100, 1),
                'legal_title': round(template.legal_weight * 100, 1),
                'permitting_esg': round(template.permitting_weight * 100, 1),
                'data_quality': round(template.data_quality_weight * 100, 1)
            },
            'created_at': template.created_at,
            'updated_at': template.updated_at
        }
    
    @staticmethod
    def get_weights_dict(template: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Get weights dictionary from template or return defaults"""
        if template and 'weights' in template:
            return template['weights']
        return TemplateManager.DEFAULT_WEIGHTS.copy()
