"""
Training Integration Module

Integrates approved training examples into AI extraction and analysis prompts
to improve accuracy through few-shot learning and retrieval-augmented generation.
"""

import json
from typing import List, Dict, Optional
from database import get_db_session
from models import TrainingExample, TrainingCategory

MAX_EXAMPLES_PER_PROMPT = 3
MIN_QUALITY_SCORE = 7.0


def get_approved_examples(category: str = None, subcategory: str = None, limit: int = MAX_EXAMPLES_PER_PROMPT) -> List[Dict]:
    """
    Retrieve approved training examples for use in prompts.
    
    Args:
        category: Filter by category (e.g., 'resource_statement', 'financial_table')
        subcategory: Filter by subcategory
        limit: Maximum number of examples to return
    
    Returns:
        List of example dictionaries with source_text and extracted_data
    """
    try:
        with get_db_session() as db:
            query = db.query(TrainingExample).filter(
                TrainingExample.is_approved == True,
                TrainingExample.quality_score >= MIN_QUALITY_SCORE
            )
            
            if category:
                query = query.filter(TrainingExample.category == category)
            
            if subcategory:
                query = query.filter(TrainingExample.subcategory == subcategory)
            
            examples = query.order_by(
                TrainingExample.quality_score.desc(),
                TrainingExample.usage_count.asc()
            ).limit(limit).all()
            
            result = []
            for ex in examples:
                result.append({
                    'id': ex.id,
                    'category': ex.category,
                    'subcategory': ex.subcategory,
                    'example_name': ex.example_name,
                    'source_text': ex.source_text,
                    'extracted_data': ex.extracted_data,
                    'quality_score': ex.quality_score
                })
                
                ex.usage_count = (ex.usage_count or 0) + 1
            
            db.commit()
            return result
            
    except Exception as e:
        return []


def format_examples_for_prompt(examples: List[Dict], format_type: str = 'extraction') -> str:
    """
    Format training examples for inclusion in prompts.
    
    Args:
        examples: List of example dictionaries
        format_type: Type of formatting ('extraction', 'validation', 'financial')
    
    Returns:
        Formatted string to include in prompts
    """
    if not examples:
        return ""
    
    formatted_parts = []
    
    for i, ex in enumerate(examples, 1):
        if format_type == 'extraction':
            formatted_parts.append(f"""
--- EXAMPLE {i}: {ex.get('example_name', 'Training Example')} ---
CATEGORY: {ex.get('category', 'unknown')}

SOURCE TEXT:
{ex.get('source_text', '')[:2000]}

CORRECT EXTRACTION:
{json.dumps(ex.get('extracted_data', {}), indent=2)}
---
""")
        elif format_type == 'validation':
            formatted_parts.append(f"""
REFERENCE EXAMPLE {i} ({ex.get('category', '')}):
- Source: {ex.get('source_text', '')[:500]}...
- Key values: {json.dumps(ex.get('extracted_data', {}), indent=2)}
""")
        elif format_type == 'financial':
            extracted = ex.get('extracted_data', {})
            formatted_parts.append(f"""
FINANCIAL EXAMPLE {i}:
Source: {ex.get('source_text', '')[:1000]}
Extracted values:
{json.dumps(extracted, indent=2)}
""")
    
    return "\n".join(formatted_parts)


def get_resource_statement_examples(limit: int = 3) -> str:
    """Get formatted examples for resource statement extraction"""
    examples = get_approved_examples(category='resource_statement', limit=limit)
    examples.extend(get_approved_examples(category='reserve_statement', limit=limit))
    return format_examples_for_prompt(examples[:limit], 'extraction')


def get_financial_table_examples(limit: int = 3) -> str:
    """Get formatted examples for financial table extraction"""
    examples = get_approved_examples(category='financial_table', limit=limit)
    return format_examples_for_prompt(examples, 'financial')


def get_production_schedule_examples(limit: int = 3) -> str:
    """Get formatted examples for production schedule extraction"""
    examples = get_approved_examples(category='production_schedule', limit=limit)
    return format_examples_for_prompt(examples, 'extraction')


def get_all_relevant_examples(commodity: str = None, limit_per_category: int = 2) -> str:
    """
    Get a diverse set of examples across all categories.
    
    Args:
        commodity: Optional commodity filter
        limit_per_category: Max examples per category
    
    Returns:
        Combined formatted examples string
    """
    categories = ['resource_statement', 'reserve_statement', 'financial_table', 
                  'production_schedule', 'cost_breakdown']
    
    all_examples = []
    for cat in categories:
        examples = get_approved_examples(category=cat, limit=limit_per_category)
        all_examples.extend(examples)
    
    if not all_examples:
        return ""
    
    header = """
=== TRAINING EXAMPLES ===
The following are verified examples of correct data extraction from mining technical documents.
Use these as reference patterns for accurate extraction:

"""
    return header + format_examples_for_prompt(all_examples[:6], 'extraction')


def build_enhanced_extraction_prompt(base_prompt: str, include_examples: bool = True) -> str:
    """
    Enhance an extraction prompt with training examples.
    
    Args:
        base_prompt: The original extraction prompt
        include_examples: Whether to include training examples
    
    Returns:
        Enhanced prompt with examples injected
    """
    if not include_examples:
        return base_prompt
    
    examples_section = get_all_relevant_examples(limit_per_category=1)
    
    if not examples_section:
        return base_prompt
    
    enhanced_prompt = f"""{examples_section}

=== YOUR TASK ===
{base_prompt}

IMPORTANT: Follow the extraction patterns shown in the examples above. Ensure numerical accuracy and proper categorization."""
    
    return enhanced_prompt


def get_training_stats() -> Dict:
    """Get statistics about available training data"""
    try:
        with get_db_session() as db:
            from sqlalchemy import func
            
            total_examples = db.query(func.count(TrainingExample.id)).scalar() or 0
            approved_examples = db.query(func.count(TrainingExample.id)).filter(
                TrainingExample.is_approved == True
            ).scalar() or 0
            high_quality = db.query(func.count(TrainingExample.id)).filter(
                TrainingExample.is_approved == True,
                TrainingExample.quality_score >= MIN_QUALITY_SCORE
            ).scalar() or 0
            
            categories = db.query(
                TrainingExample.category,
                func.count(TrainingExample.id)
            ).filter(TrainingExample.is_approved == True).group_by(TrainingExample.category).all()
            
            return {
                'total_examples': total_examples,
                'approved_examples': approved_examples,
                'high_quality_examples': high_quality,
                'categories': {cat: count for cat, count in categories}
            }
    except Exception:
        return {
            'total_examples': 0,
            'approved_examples': 0,
            'high_quality_examples': 0,
            'categories': {}
        }
