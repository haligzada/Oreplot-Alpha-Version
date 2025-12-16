"""Utility functions for formatting financial numbers."""

def format_currency(value: float, decimals: int = 1) -> str:
    """
    Format a financial value as currency with appropriate B/M suffix.
    
    Args:
        value: Numeric value (typically in millions or billions)
        decimals: Number of decimal places (default: 1)
    
    Returns:
        Formatted string like "$1.79B", "$45.2M"
    
    Examples:
        format_currency(1792.6) → "$1.79B"
        format_currency(45.2) → "$45.2M"
        format_currency(850000) → "$850.0B"
    """
    if value is None or value == 0:
        return "$0M"
    
    # Handle very large numbers (assumed to be in millions already, convert to billions)
    if abs(value) >= 1000:
        billions = value / 1000
        return f"${billions:.{decimals}f}B"
    else:
        # Already in millions
        return f"${value:.{decimals}f}M"


def format_currency_detailed(value: float, original_unit: str = 'M', decimals: int = 1) -> str:
    """
    Format currency with knowledge of original unit.
    
    Args:
        value: Numeric value
        original_unit: 'M' for millions or 'B' for billions (default: 'M')
        decimals: Number of decimal places
    
    Returns:
        Formatted string like "$1.79B", "$45.2M"
    """
    if value is None or value == 0:
        return f"$0{original_unit}"
    
    if original_unit == 'M':
        # Converting from millions
        if abs(value) >= 1000:
            return format_currency(value, decimals)
        else:
            return f"${value:.{decimals}f}M"
    elif original_unit == 'B':
        # Already in billions
        return f"${value:.{decimals}f}B"
    else:
        return f"${value:.{decimals}f}{original_unit}"
