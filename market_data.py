import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import get_db_session
from models import CommodityPriceSnapshot

class MarketDataProvider:
    """
    Fetches and caches real-time commodity prices from Metals-API
    Free tier: 100 API calls/month
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('METALS_API_KEY', '')
        self.base_url = 'https://metals-api.com/api'
        self.cache_ttl_hours = 1
        
        self.commodity_symbols = {
            'gold': 'XAU',
            'silver': 'XAG',
            'copper': 'XCU',
            'lithium': 'LITHIUM',
            'platinum': 'XPT',
            'palladium': 'XPD',
            'aluminum': 'ALU',
            'zinc': 'ZINC',
            'nickel': 'NI',
            'lead': 'LEAD',
            'tin': 'TIN',
            'iron_ore': 'IRON'
        }
        
        self.commodity_units = {
            'gold': 'USD/troy oz',
            'silver': 'USD/troy oz',
            'copper': 'USD/lb',
            'lithium': 'USD/kg',
            'platinum': 'USD/troy oz',
            'palladium': 'USD/troy oz',
            'aluminum': 'USD/lb',
            'zinc': 'USD/lb',
            'nickel': 'USD/lb',
            'lead': 'USD/lb',
            'tin': 'USD/lb',
            'iron_ore': 'USD/tonne'
        }
    
    def get_commodity_price(self, commodity: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get current price for a commodity
        
        Args:
            commodity: Commodity name (e.g., 'gold', 'copper', 'lithium')
            use_cache: Whether to use cached data (default True)
        
        Returns:
            Dictionary with price data or None if unavailable
        """
        commodity = commodity.lower()
        
        if use_cache:
            cached_price = self._get_cached_price(commodity)
            if cached_price:
                return cached_price
        
        if self.api_key:
            live_price = self._fetch_live_price(commodity)
            if live_price:
                self._cache_price(commodity, live_price)
                return live_price
        
        return self._get_mock_price(commodity)
    
    def get_multiple_commodities(self, commodities: List[str], use_cache: bool = True) -> Dict[str, Dict]:
        """
        Get prices for multiple commodities
        
        Args:
            commodities: List of commodity names
            use_cache: Whether to use cached data
        
        Returns:
            Dictionary mapping commodity names to price data
        """
        results = {}
        for commodity in commodities:
            price_data = self.get_commodity_price(commodity, use_cache)
            if price_data:
                results[commodity] = price_data
        
        return results
    
    def _get_cached_price(self, commodity: str) -> Optional[Dict]:
        """Retrieve cached price if still valid"""
        try:
            with get_db_session() as db:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_ttl_hours)
                
                snapshot = db.query(CommodityPriceSnapshot).filter(
                    CommodityPriceSnapshot.commodity == commodity,
                    CommodityPriceSnapshot.fetched_at >= cutoff_time
                ).order_by(CommodityPriceSnapshot.fetched_at.desc()).first()
                
                if snapshot:
                    return {
                        'commodity': snapshot.commodity,
                        'price': snapshot.price,
                        'currency': snapshot.currency,
                        'unit': snapshot.unit,
                        'change_24h': snapshot.price_change_24h,
                        'change_pct_24h': snapshot.price_change_percent_24h,
                        'high_52w': snapshot.high_52w,
                        'low_52w': snapshot.low_52w,
                        'source': snapshot.source,
                        'fetched_at': snapshot.fetched_at.isoformat(),
                        'from_cache': True
                    }
        except Exception as e:
            print(f"Error retrieving cached price: {e}")
        
        return None
    
    def _fetch_live_price(self, commodity: str) -> Optional[Dict]:
        """Fetch live price from Metals-API"""
        try:
            symbol = self.commodity_symbols.get(commodity)
            if not symbol:
                return None
            
            url = f"{self.base_url}/latest"
            params = {
                'access_key': self.api_key,
                'base': 'USD',
                'symbols': symbol
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and symbol in data.get('rates', {}):
                    rate = data['rates'][symbol]
                    
                    price = 1 / rate if rate > 0 else 0
                    
                    if commodity in ['copper', 'aluminum', 'zinc', 'nickel', 'lead', 'tin']:
                        price = price / 14.5833
                    elif commodity == 'lithium':
                        price = price * 31.1035
                    elif commodity == 'iron_ore':
                        price = price * 907.185
                    
                    return {
                        'commodity': commodity,
                        'price': round(price, 2),
                        'currency': 'USD',
                        'unit': self.commodity_units.get(commodity, 'USD'),
                        'change_24h': None,
                        'change_pct_24h': None,
                        'high_52w': None,
                        'low_52w': None,
                        'source': 'Metals-API',
                        'fetched_at': datetime.utcnow().isoformat(),
                        'from_cache': False
                    }
        except Exception as e:
            print(f"Error fetching live price for {commodity}: {e}")
        
        return None
    
    def _cache_price(self, commodity: str, price_data: Dict):
        """Cache price data to database"""
        try:
            with get_db_session() as db:
                expires_at = datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)
                
                snapshot = CommodityPriceSnapshot(
                    commodity=commodity,
                    price=price_data['price'],
                    currency=price_data['currency'],
                    unit=price_data['unit'],
                    price_change_24h=price_data.get('change_24h'),
                    price_change_percent_24h=price_data.get('change_pct_24h'),
                    high_52w=price_data.get('high_52w'),
                    low_52w=price_data.get('low_52w'),
                    source=price_data['source'],
                    source_url='https://metals-api.com',
                    fetched_at=datetime.utcnow(),
                    expires_at=expires_at
                )
                
                db.add(snapshot)
                db.commit()
        except Exception as e:
            print(f"Error caching price data: {e}")
    
    def _get_mock_price(self, commodity: str) -> Dict:
        """
        Return mock/fallback prices for development and testing
        Based on approximate market prices as of 2025
        """
        mock_prices = {
            'gold': 3980.00,
            'silver': 48.50,
            'copper': 0.31,
            'lithium': 22000.00,
            'platinum': 1850.00,
            'palladium': 1450.00,
            'aluminum': 0.09,
            'zinc': 0.12,
            'nickel': 0.72,
            'lead': 0.08,
            'tin': 1.20,
            'iron_ore': 105.00
        }
        
        price = mock_prices.get(commodity, 0)
        
        return {
            'commodity': commodity,
            'price': price,
            'currency': 'USD',
            'unit': self.commodity_units.get(commodity, 'USD'),
            'change_24h': None,
            'change_pct_24h': None,
            'high_52w': None,
            'low_52w': None,
            'source': 'Mock Data (Development)',
            'fetched_at': datetime.utcnow().isoformat(),
            'from_cache': False
        }
    
    def get_historical_data(self, commodity: str, days: int = 30) -> List[Dict]:
        """
        Get historical price data (if API key supports it)
        
        Args:
            commodity: Commodity name
            days: Number of days of historical data
        
        Returns:
            List of price data points
        """
        if not self.api_key:
            return []
        
        try:
            symbol = self.commodity_symbols.get(commodity.lower())
            if not symbol:
                return []
            
            url = f"{self.base_url}/timeseries"
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            params = {
                'access_key': self.api_key,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'symbols': symbol
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'rates' in data:
                    historical = []
                    for date_str, rates in data['rates'].items():
                        if symbol in rates:
                            rate = rates[symbol]
                            price = 1 / rate if rate > 0 else 0
                            
                            historical.append({
                                'date': date_str,
                                'price': round(price, 2)
                            })
                    
                    return sorted(historical, key=lambda x: x['date'])
        except Exception as e:
            print(f"Error fetching historical data: {e}")
        
        return []
    
    def get_all_mining_commodities(self, use_cache: bool = True) -> Dict[str, Dict]:
        """Get prices for all common mining commodities"""
        mining_commodities = ['gold', 'silver', 'copper', 'lithium', 'zinc', 'nickel', 'iron_ore']
        return self.get_multiple_commodities(mining_commodities, use_cache)


def get_market_data_provider() -> MarketDataProvider:
    """Factory function to create MarketDataProvider instance"""
    return MarketDataProvider()
