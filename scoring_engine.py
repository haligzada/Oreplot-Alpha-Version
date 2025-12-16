from typing import Dict, Any, List


class ScoringEngine:
    
    CATEGORY_WEIGHTS = {
        "geology_prospectivity": 35,
        "resource_potential": 20,
        "economics": 15,
        "legal_title": 10,
        "permitting_esg": 10,
        "data_quality": 10
    }
    
    SUSTAINABILITY_CATEGORY_WEIGHTS = {
        "environmental": 35,
        "social": 30,
        "governance": 20,
        "climate": 15
    }
    
    # Severity-based penalty system: distinguish CRITICAL gaps vs MINOR refinements
    # CRITICAL items (missing resource estimates, no grades, no drill data) get harsh penalties
    # MINOR items (no consolidated table, no explicit 3D dims when implied, formatting) get light penalties
    CRITICAL_MISSING_KEYWORDS = [
        'resource estimate', 'tonnage', 'grade', 'ounces', 'mineral resource',
        'capex', 'opex', 'cash flow', 'npv', 'irr', 'economic',
        'title', 'ownership', 'royalty', 'permit', 'license',
        'drilling', 'intercepts', 'assay', 'qaqc'
    ]
    
    SCORE_CAP_RULES_BY_SEVERITY = {
        'critical': {7: 5, 6: 6, 5: 6, 4: 7, 3: 7, 2: 8, 1: 9},  # Harsh: 7+ critical → max 5
        'minor': {7: 9, 6: 9, 5: 8, 4: 8, 3: 8, 2: 8, 1: 9}      # Lenient: minor gaps don't reduce much
    }
    
    MIN_EVIDENCE_REQUIREMENTS = {
        10: 8,
        9: 7,
        8: 6,
        7: 5,
        6: 4
    }
    
    @staticmethod
    def classify_missing_item_severity(item: str) -> str:
        """Classify missing information as CRITICAL or MINOR based on content."""
        item_lower = item.lower()
        for critical_keyword in ScoringEngine.CRITICAL_MISSING_KEYWORDS:
            if critical_keyword in item_lower:
                return 'critical'
        return 'minor'
    
    @staticmethod
    def validate_and_adjust_score(raw_score: float, missing_info_count: int, evidence_count: int, missing_items: List[str] = None) -> Dict[str, Any]:
        """
        Validate and adjust scores using SEVERITY-BASED penalties:
        1. Classify missing items as CRITICAL vs MINOR
        2. Apply appropriate caps based on severity
        3. Enforce minimum evidence requirements
        
        Args:
            raw_score: The AI-generated raw score (0-10)
            missing_info_count: Number of missing items (kept for backward compatibility)
            evidence_count: Number of evidence items found
            missing_items: List of missing item descriptions for severity classification
        
        Returns:
            Dict with adjusted_score, penalty_applied, and reasoning
        """
        adjusted_score = raw_score
        penalties = []
        
        # Classify missing items by severity if provided
        critical_count = 0
        minor_count = 0
        
        if missing_items:
            for item in missing_items:
                severity = ScoringEngine.classify_missing_item_severity(item)
                if severity == 'critical':
                    critical_count += 1
                else:
                    minor_count += 1
        else:
            # Fallback: assume all missing items are critical if not specified
            critical_count = missing_info_count
        
        # Apply severity-based penalty
        if critical_count >= 7:
            cap = 5
            if adjusted_score > cap:
                penalties.append(f"Capped to {cap}/10 due to {critical_count} critical missing items")
                adjusted_score = cap
        elif critical_count >= 6:
            cap = 6
            if adjusted_score > cap:
                penalties.append(f"Capped to {cap}/10 due to {critical_count} critical missing items")
                adjusted_score = cap
        elif critical_count >= 5:
            cap = 6
            if adjusted_score > cap:
                penalties.append(f"Capped to {cap}/10 due to {critical_count} critical missing items")
                adjusted_score = cap
        elif critical_count >= 4:
            cap = 7
            if adjusted_score > cap:
                penalties.append(f"Capped to {cap}/10 due to {critical_count} critical missing items")
                adjusted_score = cap
        # For 3 or fewer critical items, minor gaps alone don't reduce score
        
        # Enforce minimum evidence requirements (slightly relaxed)
        max_iterations = 10
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            score_int = int(adjusted_score)
            
            if score_int < 6:
                break
            
            min_evidence = ScoringEngine.MIN_EVIDENCE_REQUIREMENTS.get(score_int, 0)
            
            if evidence_count >= min_evidence:
                break
            
            new_score = max(5, adjusted_score - 1)
            if iteration == 1:
                penalties.append(f"Insufficient evidence: need {min_evidence} items for score {score_int}/10, have only {evidence_count}")
            adjusted_score = new_score
            
            if adjusted_score <= 5:
                break
        
        return {
            'adjusted_score': round(adjusted_score, 1),
            'original_score': raw_score,
            'penalties_applied': penalties,
            'penalty_applied': len(penalties) > 0,
            'critical_missing': critical_count,
            'minor_missing': minor_count
        }
    
    @staticmethod
    def calculate_investment_score(categories: Dict[str, Any], custom_weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Calculate investment score using category scores and weights with SEVERITY-BASED penalties.
        
        Args:
            categories: Dictionary of category data with scores
            custom_weights: Optional custom weights dict. If None, uses CATEGORY_WEIGHTS
        
        Returns:
            Dictionary with total_score, risk_band, recommendation, and category_contributions
        """
        weights = custom_weights if custom_weights is not None else ScoringEngine.CATEGORY_WEIGHTS
        
        total_score = 0.0
        category_contributions = {}
        
        for category_key, weight in weights.items():
            category_data = categories.get(category_key, {})
            raw_score = category_data.get('score', 0)
            
            missing_info = category_data.get('missing_info', [])
            evidence = category_data.get('facts_found', [])
            missing_count = len(missing_info) if isinstance(missing_info, list) else 0
            evidence_count = len(evidence) if isinstance(evidence, list) else 0
            
            # Pass missing items for severity classification
            validation_result = ScoringEngine.validate_and_adjust_score(
                raw_score, 
                missing_count, 
                evidence_count,
                missing_items=missing_info if isinstance(missing_info, list) else []
            )
            
            adjusted_score = validation_result['adjusted_score']
            
            contribution = (adjusted_score / 10.0) * weight
            category_contributions[category_key] = {
                'raw_score': raw_score,
                'adjusted_score': adjusted_score,
                'weight': weight,
                'contribution': round(contribution, 2),
                'penalty_applied': validation_result['penalty_applied'],
                'penalties': validation_result['penalties_applied'],
                'missing_info_count': missing_count,
                'evidence_count': evidence_count,
                'critical_missing': validation_result.get('critical_missing', 0),
                'minor_missing': validation_result.get('minor_missing', 0)
            }
            total_score += contribution
        
        total_score = round(total_score, 2)
        
        if total_score >= 70:
            risk_band = "LOW RISK"
            recommendation = "Favourable - Fast-track or Term Sheet"
        elif total_score >= 50:
            risk_band = "MODERATE RISK"
            recommendation = "Proceed to Deeper DD (drill program, PEA, more testwork)"
        else:
            risk_band = "HIGH RISK"
            recommendation = "Reject or Restructure (farm-out, lower price, more data required)"
        
        probability_of_success = total_score / 100.0
        
        return {
            'total_score': total_score,
            'risk_band': risk_band,
            'recommendation': recommendation,
            'probability_of_success': round(probability_of_success, 4),
            'category_contributions': category_contributions
        }
    
    @staticmethod
    def calculate_sustainability_score(sustainability_categories: Dict[str, Any], custom_weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Calculate sustainability score using category scores and weights.
        
        Args:
            sustainability_categories: Dictionary of sustainability category data with scores
            custom_weights: Optional custom weights dict. If None, uses SUSTAINABILITY_CATEGORY_WEIGHTS
        
        Returns:
            Dictionary with sustainability_score, rating, and category_contributions
        """
        weights = custom_weights if custom_weights is not None else ScoringEngine.SUSTAINABILITY_CATEGORY_WEIGHTS
        
        sustainability_score = 0.0
        category_contributions = {}
        
        for category_key, weight in weights.items():
            category_data = sustainability_categories.get(category_key, {})
            raw_score = category_data.get('score', 0)
            
            contribution = (raw_score / 10.0) * weight
            category_contributions[category_key] = {
                'raw_score': raw_score,
                'weight': weight,
                'contribution': round(contribution, 2)
            }
            sustainability_score += contribution
        
        sustainability_score = round(sustainability_score, 2)
        
        if sustainability_score >= 80:
            rating = "EXCELLENT"
            description = "Industry-leading sustainability practices - ESG excellence"
        elif sustainability_score >= 65:
            rating = "GOOD"
            description = "Strong sustainability performance - above industry standards"
        elif sustainability_score >= 50:
            rating = "MODERATE"
            description = "Acceptable sustainability performance - meets basic standards"
        else:
            rating = "NEEDS IMPROVEMENT"
            description = "Sustainability concerns - requires significant improvements"
        
        return {
            'sustainability_score': sustainability_score,
            'rating': rating,
            'description': description,
            'category_contributions': category_contributions
        }
    
    @staticmethod
    def calculate_risk_adjusted_npv(total_score: float, unrisked_npv: float) -> Dict[str, Any]:
        probability_of_success = total_score / 100.0
        risk_adjusted_npv = unrisked_npv * probability_of_success
        
        return {
            'unrisked_npv': unrisked_npv,
            'probability_of_success': probability_of_success,
            'risk_adjusted_npv': round(risk_adjusted_npv, 2)
        }
