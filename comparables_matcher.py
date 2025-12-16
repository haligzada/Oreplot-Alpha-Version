from typing import List, Dict, Any, Optional
from database import get_db_session
from models import ComparableProject, ComparableMatch, Analysis
from sqlalchemy import and_, or_


class ComparablesMatchingService:
    """Service for matching projects to comparable mining projects from the database"""
    
    MATCHING_WEIGHTS = {
        'commodity': 0.35,
        'deposit_style': 0.25,
        'development_stage': 0.20,
        'jurisdiction': 0.10,
        'scale': 0.10
    }
    
    @staticmethod
    def _normalize_commodity(commodity: str) -> str:
        """Normalize commodity names for matching"""
        if not commodity:
            return ''
        commodity = commodity.lower().strip()
        
        commodity_groups = {
            'gold': ['au', 'gold'],
            'copper': ['cu', 'copper'],
            'silver': ['ag', 'silver'],
            'lithium': ['li', 'lithium', 'spodumene', 'pegmatite'],
            'zinc': ['zn', 'zinc'],
            'nickel': ['ni', 'nickel'],
            'lead': ['pb', 'lead'],
            'iron': ['fe', 'iron', 'iron ore'],
            'platinum': ['pt', 'platinum', 'pgm', 'pge'],
            'rare earth': ['ree', 'rare earth', 'neodymium', 'praseodymium'],
            'uranium': ['u', 'uranium', 'u3o8'],
        }
        
        for group, variants in commodity_groups.items():
            if any(var in commodity for var in variants):
                return group
        
        return commodity
    
    @staticmethod
    def _extract_project_attributes(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract matching attributes from analysis data"""
        attributes = {
            'commodity': '',
            'deposit_style': '',
            'development_stage': 'exploration',
            'country': '',
            'resource_size': None
        }
        
        categories = analysis_data.get('categories', {})
        
        all_facts = []
        for cat_key, cat_data in categories.items():
            if isinstance(cat_data, dict):
                all_facts.extend(cat_data.get('facts_found', []))
        
        facts_text = ' '.join(all_facts).lower()
        
        for commodity_type in ['gold', 'copper', 'silver', 'lithium', 'zinc', 'nickel', 'iron', 'platinum', 'uranium']:
            if commodity_type in facts_text:
                attributes['commodity'] = commodity_type
                break
        
        deposit_keywords = {
            'porphyry': ['porphyry'],
            'epithermal': ['epithermal'],
            'orogenic': ['orogenic', 'orogenic gold'],
            'vms': ['vms', 'volcanogenic', 'massive sulfide'],
            'skarn': ['skarn'],
            'irgs': ['irgs', 'intrusion-related'],
            'sedex': ['sedex', 'sedimentary exhalative']
        }
        
        for deposit_type, keywords in deposit_keywords.items():
            if any(kw in facts_text for kw in keywords):
                attributes['deposit_style'] = deposit_type
                break
        
        if 'production' in facts_text or 'operating' in facts_text or 'producing' in facts_text:
            attributes['development_stage'] = 'production'
        elif 'feasibility' in facts_text or 'pfs' in facts_text or 'dfs' in facts_text:
            attributes['development_stage'] = 'development'
        elif 'resource' in facts_text or 'mre' in facts_text or 'indicated' in facts_text or 'inferred' in facts_text:
            attributes['development_stage'] = 'resource'
        else:
            attributes['development_stage'] = 'exploration'
        
        for country in ['canada', 'usa', 'australia', 'chile', 'peru', 'mexico', 'brazil', 'south africa']:
            if country in facts_text:
                attributes['country'] = country
                break
        
        import re
        tonnage_patterns = [
            r'(\d+\.?\d*)\s*(?:million|m)\s*(?:tonnes?|tons?|mt)',
            r'(\d+\.?\d*)\s*moz',
            r'(\d+\.?\d*)\s*(?:billion|b)\s*(?:tonnes?|tons?)',
        ]
        for pattern in tonnage_patterns:
            match = re.search(pattern, facts_text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    if 'billion' in facts_text[match.start():match.end()].lower():
                        value *= 1000
                    if 'moz' in facts_text[match.start():match.end()].lower():
                        value *= 0.031
                    attributes['resource_size'] = value
                    break
                except:
                    pass
        
        return attributes
    
    @staticmethod
    def _calculate_similarity(project_attrs: Dict[str, Any], comparable: ComparableProject) -> float:
        """Calculate similarity score between project and comparable"""
        score = 0.0
        
        if project_attrs['commodity'] and comparable.commodity:
            proj_commodity = ComparablesMatchingService._normalize_commodity(project_attrs['commodity'])
            comp_commodity = ComparablesMatchingService._normalize_commodity(comparable.commodity)
            if proj_commodity == comp_commodity:
                score += ComparablesMatchingService.MATCHING_WEIGHTS['commodity']
            elif proj_commodity in comp_commodity or comp_commodity in proj_commodity:
                score += ComparablesMatchingService.MATCHING_WEIGHTS['commodity'] * 0.5
        
        if project_attrs['deposit_style'] and comparable.deposit_style:
            if project_attrs['deposit_style'].lower() in comparable.deposit_style.lower():
                score += ComparablesMatchingService.MATCHING_WEIGHTS['deposit_style']
        elif project_attrs['deposit_style'] and comparable.geology_type:
            if project_attrs['deposit_style'].lower() in comparable.geology_type.lower():
                score += ComparablesMatchingService.MATCHING_WEIGHTS['deposit_style'] * 0.7
        
        stage_mapping = {
            'exploration': 1,
            'resource': 2,
            'development': 3,
            'production': 4
        }
        proj_stage = stage_mapping.get(project_attrs['development_stage'], 1)
        comp_stage = stage_mapping.get(comparable.project_stage, 1) if comparable.project_stage else 1
        
        stage_diff = abs(proj_stage - comp_stage)
        if stage_diff == 0:
            score += ComparablesMatchingService.MATCHING_WEIGHTS['development_stage']
        elif stage_diff == 1:
            score += ComparablesMatchingService.MATCHING_WEIGHTS['development_stage'] * 0.6
        elif stage_diff == 2:
            score += ComparablesMatchingService.MATCHING_WEIGHTS['development_stage'] * 0.3
        
        if project_attrs['country'] and comparable.country:
            if project_attrs['country'].lower() in comparable.country.lower():
                score += ComparablesMatchingService.MATCHING_WEIGHTS['jurisdiction']
            elif comparable.country.lower() in ['canada', 'australia', 'usa']:
                score += ComparablesMatchingService.MATCHING_WEIGHTS['jurisdiction'] * 0.5
        
        if project_attrs['resource_size'] and comparable.total_resource_mt:
            proj_size = project_attrs['resource_size']
            comp_size = comparable.total_resource_mt
            ratio = min(proj_size, comp_size) / max(proj_size, comp_size)
            if ratio >= 0.5:
                score += ComparablesMatchingService.MATCHING_WEIGHTS['scale'] * ratio
        elif comparable.total_resource_mt and comparable.total_resource_mt > 0:
            score += ComparablesMatchingService.MATCHING_WEIGHTS['scale'] * 0.3
        
        return min(score, 1.0)
    
    @staticmethod
    def find_top_comparables(
        analysis_id: int,
        analysis_data: Dict[str, Any],
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """Find top N most similar comparable projects"""
        project_attrs = ComparablesMatchingService._extract_project_attributes(analysis_data)
        
        with get_db_session() as session:
            query = session.query(ComparableProject).filter(
                ComparableProject.approved_for_display == True
            )
            
            if project_attrs['commodity']:
                normalized_commodity = ComparablesMatchingService._normalize_commodity(project_attrs['commodity'])
                query = query.filter(
                    or_(
                        ComparableProject.commodity.ilike(f'%{normalized_commodity}%'),
                        ComparableProject.commodity.ilike(f'%{project_attrs["commodity"]}%'),
                        ComparableProject.commodity_group.ilike(f'%{normalized_commodity}%')
                    )
                )
            
            comparables = query.all()
            
            scored_comparables = []
            for comp in comparables:
                similarity_score = ComparablesMatchingService._calculate_similarity(project_attrs, comp)
                
                if similarity_score > 0.2:
                    scored_comparables.append({
                        'comparable': comp,
                        'similarity_score': similarity_score,
                        'match_criteria': {
                            'commodity_match': project_attrs['commodity'],
                            'deposit_style_match': project_attrs['deposit_style'],
                            'stage_match': project_attrs['development_stage']
                        }
                    })
            
            scored_comparables.sort(key=lambda x: x['similarity_score'], reverse=True)
            top_comparables = scored_comparables[:top_n]
            
            session.query(ComparableMatch).filter(
                ComparableMatch.analysis_id == analysis_id
            ).delete()
            
            for idx, match_data in enumerate(top_comparables, 1):
                comparable_match = ComparableMatch(
                    analysis_id=analysis_id,
                    comparable_id=match_data['comparable'].id,
                    similarity_score=match_data['similarity_score'],
                    match_criteria=match_data['match_criteria'],
                    rank=idx
                )
                session.add(comparable_match)
            
            session.commit()
            
            return [
                {
                    'id': match['comparable'].id,
                    'name': match['comparable'].name,
                    'company': match['comparable'].company,
                    'location': match['comparable'].location,
                    'country': match['comparable'].country,
                    'commodity': match['comparable'].commodity,
                    'project_stage': match['comparable'].project_stage,
                    'geology_type': match['comparable'].geology_type,
                    'total_resource_mt': match['comparable'].total_resource_mt,
                    'grade': match['comparable'].grade,
                    'grade_unit': match['comparable'].grade_unit,
                    'npv_millions_usd': match['comparable'].npv_millions_usd,
                    'irr_percent': match['comparable'].irr_percent,
                    'capex_millions_usd': match['comparable'].capex_millions_usd,
                    'similarity_score': match['similarity_score'],
                    'match_criteria': match['match_criteria']
                }
                for match in top_comparables
            ]
    
    @staticmethod
    def get_comparables_for_analysis(analysis_id: int) -> List[Dict[str, Any]]:
        """Retrieve previously matched comparables for an analysis"""
        with get_db_session() as session:
            matches = session.query(ComparableMatch, ComparableProject).join(
                ComparableProject,
                ComparableMatch.comparable_id == ComparableProject.id
            ).filter(
                ComparableMatch.analysis_id == analysis_id
            ).order_by(
                ComparableMatch.rank
            ).all()
            
            return [
                {
                    'id': comp.id,
                    'name': comp.name,
                    'company': comp.company,
                    'location': comp.location,
                    'country': comp.country,
                    'commodity': comp.commodity,
                    'project_stage': comp.project_stage,
                    'geology_type': comp.geology_type,
                    'total_resource_mt': comp.total_resource_mt,
                    'grade': comp.grade,
                    'grade_unit': comp.grade_unit,
                    'npv_millions_usd': comp.npv_millions_usd,
                    'irr_percent': comp.irr_percent,
                    'capex_millions_usd': comp.capex_millions_usd,
                    'similarity_score': match.similarity_score,
                    'match_criteria': match.match_criteria
                }
                for match, comp in matches
            ]
