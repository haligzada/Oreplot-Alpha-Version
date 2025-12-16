"""
AI Access Control Utilities
Manages access control for Light AI and Advanced AI tiers
"""

from database import get_db_session
from models import User

AI_TIER_LIGHT = 'light_ai'
AI_TIER_ADVANCED = 'advanced_ai'
AI_TIER_BOTH = 'both'

VALID_TIERS = [AI_TIER_LIGHT, AI_TIER_ADVANCED, AI_TIER_BOTH]


def get_user_ai_tier(user_id: int) -> str:
    """Get the AI tier access for a user"""
    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            tier = getattr(user, 'ai_tier_access', AI_TIER_LIGHT)
            return tier if tier in VALID_TIERS else AI_TIER_LIGHT
        return AI_TIER_LIGHT


def _is_admin_strict(user_data: dict) -> bool:
    """Strictly check if user is admin (handles string/bool serialization)"""
    is_admin = user_data.get('is_admin')
    if is_admin is True:
        return True
    if isinstance(is_admin, str) and is_admin.lower() == 'true':
        return True
    return False


def has_light_ai_access(user_data: dict) -> bool:
    """Check if user has access to Light AI features"""
    if _is_admin_strict(user_data):
        return True
    
    tier = user_data.get('ai_tier_access', AI_TIER_LIGHT)
    return tier in [AI_TIER_LIGHT, AI_TIER_BOTH]


def has_advanced_ai_access(user_data: dict) -> bool:
    """Check if user has access to Advanced AI features"""
    if _is_admin_strict(user_data):
        return True
    
    tier = user_data.get('ai_tier_access', AI_TIER_LIGHT)
    return tier in [AI_TIER_ADVANCED, AI_TIER_BOTH]


def has_both_access(user_data: dict) -> bool:
    """Check if user has access to both Light and Advanced AI"""
    if _is_admin_strict(user_data):
        return True
    
    tier = user_data.get('ai_tier_access', AI_TIER_LIGHT)
    return tier == AI_TIER_BOTH


def get_user_ai_features(user_data: dict) -> dict:
    """Get detailed AI feature access for a user"""
    is_admin = _is_admin_strict(user_data)
    tier = user_data.get('ai_tier_access', AI_TIER_LIGHT)
    
    if is_admin:
        tier = AI_TIER_BOTH
    
    light_access = tier in [AI_TIER_LIGHT, AI_TIER_BOTH] or is_admin
    advanced_access = tier in [AI_TIER_ADVANCED, AI_TIER_BOTH] or is_admin
    
    return {
        'tier': tier,
        'is_admin': is_admin,
        'light_ai': {
            'enabled': light_access,
            'features': {
                'document_analysis': light_access,
                'investment_scoring': light_access,
                'sustainability_scoring': light_access,
                'pdf_report_generation': light_access,
                'comparables_matching': light_access,
                'template_management': light_access,
                'project_management': light_access,
            }
        },
        'advanced_ai': {
            'enabled': advanced_access,
            'features': {
                'market_multiples_analysis': advanced_access,
                'ev_resource_benchmarking': advanced_access,
                'kilburn_method': advanced_access,
                'pwc_cost_approach': advanced_access,
                'monte_carlo_simulation': advanced_access,
                'advanced_valuation_report': advanced_access,
                'risk_modeling': advanced_access,
                'financial_valuation': advanced_access,
            }
        }
    }


def get_tier_display_name(tier: str) -> str:
    """Get human-readable name for AI tier"""
    tier_names = {
        AI_TIER_LIGHT: '🔵 Light AI',
        AI_TIER_ADVANCED: '🟣 Advanced AI',
        AI_TIER_BOTH: '🟢 Full Access (Light + Advanced)'
    }
    return tier_names.get(tier, '🔵 Light AI')


def get_tier_description(tier: str) -> str:
    """Get description for AI tier"""
    descriptions = {
        AI_TIER_LIGHT: 'Standard document analysis, dual scoring (Investment + Sustainability), PDF reports, comparables matching, and template management.',
        AI_TIER_ADVANCED: 'PwC-style valuation methods including Market Multiples Analysis, Kilburn Method (Cost Approach), and Monte Carlo Risk Modeling.',
        AI_TIER_BOTH: 'Complete access to all Light AI and Advanced AI features for comprehensive mining due diligence analysis.'
    }
    return descriptions.get(tier, descriptions[AI_TIER_LIGHT])


def update_user_ai_tier(user_id: int, new_tier: str) -> bool:
    """Update user's AI tier access"""
    if new_tier not in VALID_TIERS:
        return False
    
    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.ai_tier_access = new_tier
            db.commit()
            return True
    return False


def get_upgrade_message(current_tier: str) -> str:
    """Get upgrade message based on current tier"""
    if current_tier == AI_TIER_LIGHT:
        return "Upgrade to Advanced AI to access PwC-style valuation methods, Monte Carlo simulations, and market multiples analysis."
    elif current_tier == AI_TIER_ADVANCED:
        return "Your plan includes Advanced AI features. Contact admin to add Light AI access for standard analysis features."
    return ""


LIGHT_AI_FEATURES = [
    {
        'name': 'Document Analysis',
        'description': 'GPT-5.1 powered document extraction and analysis',
        'icon': '📄'
    },
    {
        'name': 'Investment Scoring',
        'description': 'Dual 0-100 scoring across 6 weighted categories',
        'icon': '📊'
    },
    {
        'name': 'Sustainability Scoring',
        'description': 'ESG analysis across Environmental, Social, Governance, Climate',
        'icon': '🌱'
    },
    {
        'name': 'PDF Reports',
        'description': 'Professional due diligence report generation',
        'icon': '📑'
    },
    {
        'name': 'Comparables Matching',
        'description': 'Intelligent project benchmarking from global database',
        'icon': '🔍'
    },
    {
        'name': 'Template Management',
        'description': 'Custom scoring templates with adjustable weights',
        'icon': '⚙️'
    }
]

ADVANCED_AI_FEATURES = [
    {
        'name': 'Market Multiples Analysis',
        'description': 'EV/Resource calculations, peer benchmarking, implied valuations',
        'icon': '📈'
    },
    {
        'name': 'PwC Cost Approach (Kilburn Method)',
        'description': 'Geoscientific rating, PEM multipliers, appraised value calculation',
        'icon': '🏛️'
    },
    {
        'name': 'Monte Carlo Risk Modeling',
        'description': 'Commodity price simulation, NPV distribution, VaR metrics',
        'icon': '🎲'
    },
    {
        'name': 'EV/Resource Benchmarking',
        'description': 'Enterprise value per resource ounce comparison vs peers',
        'icon': '⚖️'
    },
    {
        'name': 'Financial Valuation Reports',
        'description': 'Comprehensive valuation reports with multiple methodologies',
        'icon': '💰'
    },
    {
        'name': 'Risk-Adjusted NPV',
        'description': 'P10/P50/P90 NPV scenarios with probability analysis',
        'icon': '📉'
    }
]
