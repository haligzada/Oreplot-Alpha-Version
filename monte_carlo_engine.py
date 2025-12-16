"""
Monte Carlo Risk Modeling Engine
Implements probabilistic NPV analysis with commodity price simulation
"""

import streamlit as st
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from format_utils import format_currency


# Default simulation parameters
DEFAULT_SIMULATIONS = 10000
DEFAULT_PROJECT_LIFE = 15  # years

# Commodity price volatility (annual standard deviation)
COMMODITY_VOLATILITY = {
    'gold': 0.15,      # 15% annual volatility
    'silver': 0.25,    # 25% annual volatility
    'copper': 0.20,    # 20% annual volatility
    'zinc': 0.22,      # 22% annual volatility
    'nickel': 0.28,    # 28% annual volatility
    'lithium': 0.35,   # 35% annual volatility (high volatility commodity)
    'uranium': 0.30,   # 30% annual volatility
}

# Current spot prices (USD) - would be fetched from API in production
DEFAULT_SPOT_PRICES = {
    'gold': 2000.0,     # $/oz
    'silver': 25.0,     # $/oz
    'copper': 4.00,     # $/lb
    'zinc': 1.20,       # $/lb
    'nickel': 8.50,     # $/lb
    'lithium': 25000,   # $/tonne (spodumene concentrate)
    'uranium': 65.0,    # $/lb U3O8
}


def simulate_price_paths(
    spot_price: float,
    volatility: float,
    years: int,
    num_simulations: int,
    drift: float = 0.0,
    mean_reversion: bool = True,
    reversion_speed: float = 0.15,
    seed: int = None
) -> np.ndarray:
    """
    Simulate commodity price paths using Geometric Brownian Motion
    with optional mean reversion (Ornstein-Uhlenbeck process)
    
    Args:
        spot_price: Current spot price
        volatility: Annual volatility (std dev)
        years: Project life in years
        num_simulations: Number of Monte Carlo simulations
        drift: Expected annual drift (default 0 for commodities)
        mean_reversion: Whether to apply mean reversion
        reversion_speed: Speed of mean reversion
        seed: Optional random seed for reproducibility (None for random)
    
    Returns:
        numpy array of simulated price paths (num_simulations x years)
    """
    dt = 1.0  # Annual time step
    
    # Initialize price array
    prices = np.zeros((num_simulations, years))
    prices[:, 0] = spot_price
    
    # Use a random state object instead of global seed for proper randomness
    rng = np.random.RandomState(seed)
    random_shocks = rng.normal(0, 1, (num_simulations, years - 1))
    
    for t in range(1, years):
        if mean_reversion:
            # Mean-reverting GBM (exponential form to ensure positive prices)
            # Log-Ornstein-Uhlenbeck: d(log S) = theta*(log(mu) - log(S))dt + sigma*dW
            log_mean = np.log(spot_price)
            log_prices = np.log(np.maximum(prices[:, t-1], spot_price * 0.01))
            log_prices_new = log_prices + reversion_speed * (log_mean - log_prices) * dt + \
                            volatility * np.sqrt(dt) * random_shocks[:, t-1]
            prices[:, t] = np.exp(log_prices_new)
        else:
            # Standard GBM (log-normal, always positive)
            prices[:, t] = prices[:, t-1] * np.exp(
                (drift - 0.5 * volatility**2) * dt + 
                volatility * np.sqrt(dt) * random_shocks[:, t-1]
            )
    
    # Floor at 10% of spot price to prevent extreme outliers
    prices = np.maximum(prices, spot_price * 0.1)
    
    return prices


def calculate_npv_distribution(
    annual_production: float,
    unit_cost: float,
    initial_capex: float,
    price_paths: np.ndarray,
    discount_rate: float = 0.08,
    royalty_rate: float = 0.03,
    tax_rate: float = 0.25
) -> Dict:
    """
    Calculate NPV distribution from simulated price paths
    
    Args:
        annual_production: Annual production (oz, lbs, tonnes)
        unit_cost: All-in sustaining cost per unit
        initial_capex: Initial capital expenditure
        price_paths: Simulated commodity price paths
        discount_rate: Project discount rate
        royalty_rate: Royalty rate on revenue
        tax_rate: Corporate tax rate
    
    Returns:
        Dictionary with NPV distribution statistics
    """
    num_simulations, years = price_paths.shape
    
    # Calculate annual cash flows for each simulation
    npvs = np.zeros(num_simulations)
    
    for sim in range(num_simulations):
        cash_flows = []
        cumulative_cf = -initial_capex
        
        for year in range(years):
            price = price_paths[sim, year]
            revenue = annual_production * price
            royalty = revenue * royalty_rate
            net_revenue = revenue - royalty
            operating_cost = annual_production * unit_cost
            ebitda = net_revenue - operating_cost
            
            # Apply tax if positive
            if ebitda > 0:
                tax = ebitda * tax_rate
                net_cash_flow = ebitda - tax
            else:
                net_cash_flow = ebitda
            
            cash_flows.append(net_cash_flow)
        
        # Calculate NPV
        discount_factors = [(1 + discount_rate) ** -(t+1) for t in range(years)]
        npv = -initial_capex + sum(cf * df for cf, df in zip(cash_flows, discount_factors))
        npvs[sim] = npv
    
    # Calculate statistics
    npv_mean = np.mean(npvs)
    npv_std = np.std(npvs)
    npv_median = np.median(npvs)
    npv_p10 = np.percentile(npvs, 10)
    npv_p25 = np.percentile(npvs, 25)
    npv_p75 = np.percentile(npvs, 75)
    npv_p90 = np.percentile(npvs, 90)
    
    # Value at Risk (VaR) - 5% worst case
    var_5 = np.percentile(npvs, 5)
    
    # Probability of positive NPV
    prob_positive = np.mean(npvs > 0)
    
    # Probability of exceeding 10% IRR threshold (simplified)
    breakeven_npv = initial_capex * 0.1
    prob_exceed_hurdle = np.mean(npvs > breakeven_npv)
    
    return {
        'mean': npv_mean,
        'std': npv_std,
        'median': npv_median,
        'p50': npv_median,
        'p10': npv_p10,
        'p25': npv_p25,
        'p75': npv_p75,
        'p90': npv_p90,
        'var_5': var_5,
        'prob_positive': prob_positive,
        'prob_exceed_hurdle': prob_exceed_hurdle,
        'npv_distribution': npvs.tolist(),
        'num_simulations': num_simulations
    }


def run_monte_carlo_simulation(
    commodity: str,
    spot_price: float,
    annual_production: float,
    unit_cost: float,
    initial_capex: float,
    project_life: int = DEFAULT_PROJECT_LIFE,
    num_simulations: int = DEFAULT_SIMULATIONS,
    discount_rate: float = 0.08,
    royalty_rate: float = 0.03,
    tax_rate: float = 0.25,
    custom_volatility: Optional[float] = None
) -> Dict:
    """
    Run full Monte Carlo simulation for project valuation
    """
    # Get volatility
    commodity_lower = commodity.lower()
    if custom_volatility:
        volatility = custom_volatility
    else:
        volatility = COMMODITY_VOLATILITY.get(commodity_lower, 0.20)
    
    # Simulate price paths
    price_paths = simulate_price_paths(
        spot_price=spot_price,
        volatility=volatility,
        years=project_life,
        num_simulations=num_simulations
    )
    
    # Calculate NPV distribution
    npv_stats = calculate_npv_distribution(
        annual_production=annual_production,
        unit_cost=unit_cost,
        initial_capex=initial_capex,
        price_paths=price_paths,
        discount_rate=discount_rate,
        royalty_rate=royalty_rate,
        tax_rate=tax_rate
    )
    
    # Calculate price statistics
    final_prices = price_paths[:, -1]
    price_stats = {
        'initial': spot_price,
        'mean_final': np.mean(final_prices),
        'std_final': np.std(final_prices),
        'p10_final': np.percentile(final_prices, 10),
        'p90_final': np.percentile(final_prices, 90),
    }
    
    # Real options value (simplified - premium over static NPV)
    # Real options typically add 30-50% value vs static DCF
    static_npv = npv_stats['mean']
    option_premium = abs(static_npv) * 0.35 if static_npv > 0 else abs(static_npv) * 0.20
    real_options_value = static_npv + option_premium
    
    npv_mean = npv_stats['mean']
    npv_p50 = npv_stats['p50']
    
    if npv_mean > 0 and npv_stats['prob_positive'] > 0.70:
        recommendation = "Favorable Risk Profile - High probability of positive returns"
        color = "green"
    elif npv_mean > 0 and npv_stats['prob_positive'] > 0.50:
        recommendation = "Moderate Risk - Positive expected value with significant downside"
        color = "blue"
    elif npv_stats['prob_positive'] > 0.30:
        recommendation = "High Risk - Substantial probability of loss"
        color = "orange"
    else:
        recommendation = "Very High Risk - Majority of scenarios show losses"
        color = "red"
    
    return {
        'commodity': commodity,
        'input_parameters': {
            'spot_price': spot_price,
            'annual_production': annual_production,
            'unit_cost': unit_cost,
            'initial_capex': initial_capex,
            'project_life': project_life,
            'discount_rate': discount_rate,
            'volatility': volatility,
            'num_simulations': num_simulations
        },
        'npv_statistics': npv_stats,
        'price_statistics': price_stats,
        'real_options_value': real_options_value,
        'option_premium_pct': (real_options_value / max(static_npv, 1) - 1) * 100 if static_npv > 0 else 0,
        'calculation_date': datetime.now().isoformat(),
        'recommendation': {
            'text': recommendation,
            'color': color
        }
    }


def run_full_monte_carlo_analysis(
    commodity: str,
    annual_production: float,
    unit_cost: float,
    initial_capex: float,
    spot_price: float = None,
    years: int = 15,
    discount_rate: float = 0.08,
    num_simulations: int = 10000
) -> Dict:
    """
    Run Monte Carlo analysis with automatic spot price detection
    Used by Advanced AI analyzer
    """
    commodity_lower = commodity.lower() if commodity else 'gold'
    
    if spot_price is None or spot_price <= 0:
        spot_price = DEFAULT_SPOT_PRICES.get(commodity_lower, 2000.0)
    
    return run_monte_carlo_simulation(
        commodity=commodity,
        spot_price=spot_price,
        annual_production=annual_production,
        unit_cost=unit_cost,
        initial_capex=initial_capex,
        project_life=years,
        num_simulations=num_simulations,
        discount_rate=discount_rate
    )


def calculate_sensitivity_tornado(
    base_params: Dict,
    variation_pct: float = 0.20
) -> Dict:
    """
    Calculate sensitivity analysis (tornado diagram data)
    """
    sensitivities = {}
    
    # Parameters to vary
    params_to_vary = [
        ('spot_price', 'Commodity Price'),
        ('unit_cost', 'Operating Cost'),
        ('initial_capex', 'Capital Cost'),
        ('annual_production', 'Production Rate'),
        ('discount_rate', 'Discount Rate')
    ]
    
    # Run base case
    base_result = run_monte_carlo_simulation(**base_params, num_simulations=1000)
    base_npv = base_result['npv_statistics']['mean']
    
    for param_key, param_name in params_to_vary:
        base_value = base_params[param_key]
        
        # Low case
        low_params = base_params.copy()
        if param_key in ['unit_cost', 'initial_capex', 'discount_rate']:
            low_params[param_key] = base_value * (1 + variation_pct)  # Higher is worse
        else:
            low_params[param_key] = base_value * (1 - variation_pct)
        
        low_result = run_monte_carlo_simulation(**low_params, num_simulations=1000)
        low_npv = low_result['npv_statistics']['mean']
        
        # High case
        high_params = base_params.copy()
        if param_key in ['unit_cost', 'initial_capex', 'discount_rate']:
            high_params[param_key] = base_value * (1 - variation_pct)  # Lower is better
        else:
            high_params[param_key] = base_value * (1 + variation_pct)
        
        high_result = run_monte_carlo_simulation(**high_params, num_simulations=1000)
        high_npv = high_result['npv_statistics']['mean']
        
        sensitivities[param_name] = {
            'low_npv': low_npv,
            'base_npv': base_npv,
            'high_npv': high_npv,
            'low_delta': low_npv - base_npv,
            'high_delta': high_npv - base_npv,
            'range': high_npv - low_npv
        }
    
    return {
        'base_npv': base_npv,
        'sensitivities': sensitivities,
        'variation_pct': variation_pct
    }


def render_monte_carlo_analysis():
    """Render the Monte Carlo Risk Modeling UI in Streamlit"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #b71c1c, #e53935); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: white; margin: 0;'>🎲 Monte Carlo Risk Modeling</h3>
        <p style='color: #ffcdd2; margin: 5px 0 0 0;'>Probabilistic NPV analysis with real options value</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Monte Carlo simulation models uncertainty in commodity prices and project economics 
    to generate a probability distribution of project NPV outcomes. This provides 
    a more realistic assessment of project risk than static DCF analysis.
    """)
    
    st.markdown("### Project Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        commodity = st.selectbox(
            "Primary Commodity",
            ["Gold", "Silver", "Copper", "Zinc", "Nickel", "Lithium", "Uranium"],
            help="Select commodity for volatility assumptions"
        )
        
        # Get default spot price
        commodity_lower = commodity.lower()
        default_price = DEFAULT_SPOT_PRICES.get(commodity_lower, 2000)
        
        spot_price = st.number_input(
            "Current Spot Price (USD)",
            min_value=0.1,
            value=float(default_price),
            step=float(default_price * 0.05),
            format="%.2f",
            help="Current commodity price"
        )
        
        annual_production = st.number_input(
            "Annual Production (units)",
            min_value=0.0,
            value=100000.0,
            step=10000.0,
            format="%.0f",
            help="Annual production in oz (precious) or lbs/tonnes (base metals)"
        )
        
        project_life = st.slider(
            "Project Life (years)",
            min_value=5,
            max_value=30,
            value=15,
            help="Expected mine life"
        )
    
    with col2:
        unit_cost = st.number_input(
            "All-in Sustaining Cost (USD/unit)",
            min_value=0.0,
            value=float(default_price * 0.6),
            step=float(default_price * 0.05),
            format="%.2f",
            help="Total operating cost per unit produced"
        )
        
        initial_capex = st.number_input(
            "Initial Capital (USD)",
            min_value=0.0,
            value=500000000.0,
            step=50000000.0,
            format="%.0f",
            help="Initial capital expenditure to build the mine"
        )
        
        discount_rate = st.slider(
            "Discount Rate (%)",
            min_value=5.0,
            max_value=15.0,
            value=8.0,
            step=0.5,
            help="Risk-adjusted discount rate"
        ) / 100
        
        num_simulations = st.select_slider(
            "Number of Simulations",
            options=[1000, 5000, 10000, 25000, 50000],
            value=10000,
            help="More simulations = more accurate but slower"
        )
    
    st.markdown("---")
    
    with st.expander("⚙️ Advanced Parameters"):
        col1, col2 = st.columns(2)
        
        with col1:
            royalty_rate = st.slider(
                "Royalty Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5
            ) / 100
            
            custom_volatility = st.checkbox("Use Custom Volatility")
            if custom_volatility:
                volatility = st.slider(
                    "Annual Price Volatility (%)",
                    min_value=5.0,
                    max_value=50.0,
                    value=COMMODITY_VOLATILITY.get(commodity_lower, 0.20) * 100,
                    step=1.0
                ) / 100
            else:
                volatility = None
        
        with col2:
            tax_rate = st.slider(
                "Corporate Tax Rate (%)",
                min_value=0.0,
                max_value=40.0,
                value=25.0,
                step=1.0
            ) / 100
    
    st.markdown("---")
    
    if st.button("🎲 Run Monte Carlo Simulation", type="primary", use_container_width=True):
        with st.spinner(f"Running {num_simulations:,} simulations..."):
            # Run simulation
            result = run_monte_carlo_simulation(
                commodity=commodity,
                spot_price=spot_price,
                annual_production=annual_production,
                unit_cost=unit_cost,
                initial_capex=initial_capex,
                project_life=project_life,
                num_simulations=num_simulations,
                discount_rate=discount_rate,
                royalty_rate=royalty_rate,
                tax_rate=tax_rate,
                custom_volatility=volatility
            )
            
            # Store in session state
            st.session_state['monte_carlo_result'] = result
            
            # Display results
            st.markdown("### 📊 Simulation Results")
            
            npv_stats = result['npv_statistics']
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Mean NPV",
                    format_currency(npv_stats['mean']/1e6, decimals=1),
                    help="Expected (average) NPV"
                )
            
            with col2:
                st.metric(
                    "Median NPV",
                    format_currency(npv_stats['median']/1e6, decimals=1),
                    help="50th percentile NPV"
                )
            
            with col3:
                prob_color = "normal" if npv_stats['prob_positive'] >= 0.7 else "off"
                st.metric(
                    "P(NPV > 0)",
                    f"{npv_stats['prob_positive']*100:.1f}%",
                    help="Probability of positive NPV"
                )
            
            with col4:
                st.metric(
                    "VaR (5%)",
                    format_currency(npv_stats['var_5']/1e6, decimals=1),
                    help="5th percentile - worst 5% of outcomes"
                )
            
            st.markdown("---")
            
            # NPV Distribution
            st.markdown("#### NPV Probability Distribution")
            
            # Create histogram data
            npv_values = np.array(npv_stats['npv_distribution'])
            
            # Display percentile table
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                | Percentile | NPV |
                |------------|-----|
                | P10 (Downside) | ${:,.0f}M |
                | P25 | ${:,.0f}M |
                | P50 (Median) | ${:,.0f}M |
                | P75 | ${:,.0f}M |
                | P90 (Upside) | ${:,.0f}M |
                """.format(
                    npv_stats['p10']/1e6,
                    npv_stats['p25']/1e6,
                    npv_stats['median']/1e6,
                    npv_stats['p75']/1e6,
                    npv_stats['p90']/1e6
                ))
            
            with col2:
                # Risk metrics
                st.markdown("#### Risk Metrics")
                
                st.markdown(f"**Standard Deviation:** {format_currency(npv_stats['std']/1e6, decimals=1)}")
                st.markdown(f"**Coefficient of Variation:** {npv_stats['std']/max(abs(npv_stats['mean']), 1):.2f}")
                st.markdown(f"**P90/P10 Range:** {format_currency((npv_stats['p90']-npv_stats['p10'])/1e6, decimals=1)}")
                st.markdown(f"**Probability > Hurdle:** {npv_stats['prob_exceed_hurdle']*100:.1f}%")
            
            st.markdown("---")
            
            # Real Options Value
            st.markdown("#### 💎 Real Options Value")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style='background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;'>
                    <div style='font-size: 14px; color: #666;'>Static DCF NPV</div>
                    <div style='font-size: 24px; font-weight: bold; color: #1565c0;'>{format_currency(npv_stats['mean']/1e6, decimals=1)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style='background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;'>
                    <div style='font-size: 14px; color: #666;'>Option Premium</div>
                    <div style='font-size: 24px; font-weight: bold; color: #e65100;'>+{result['option_premium_pct']:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style='background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;'>
                    <div style='font-size: 14px; color: #666;'>Real Options Value</div>
                    <div style='font-size: 24px; font-weight: bold; color: #2e7d32;'>{format_currency(result['real_options_value']/1e6, decimals=1)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.info("""
            **Real Options Premium:** Mining projects have embedded optionality (ability to defer, 
            expand, or abandon) that adds value beyond static NPV. The premium typically ranges 
            from 30-50% for development-stage projects with price volatility.
            """)
            
            # Price Statistics
            st.markdown("#### 📈 Price Path Statistics")
            
            price_stats = result['price_statistics']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Initial Price:** ${price_stats['initial']:,.2f}")
                st.markdown(f"**Mean Final Price:** ${price_stats['mean_final']:,.2f}")
            
            with col2:
                st.markdown(f"**P10 Final Price:** ${price_stats['p10_final']:,.2f}")
                st.markdown(f"**P90 Final Price:** ${price_stats['p90_final']:,.2f}")
            
            st.success(f"Monte Carlo simulation complete! ({num_simulations:,} iterations)")


def get_monte_carlo_for_report(
    commodity: str,
    spot_price: float,
    annual_production: float,
    unit_cost: float,
    initial_capex: float,
    project_life: int = 15
) -> Optional[Dict]:
    """
    Generate Monte Carlo results for PDF report
    """
    if not all([spot_price, annual_production, unit_cost, initial_capex]):
        return None
    
    return run_monte_carlo_simulation(
        commodity=commodity,
        spot_price=spot_price,
        annual_production=annual_production,
        unit_cost=unit_cost,
        initial_capex=initial_capex,
        project_life=project_life,
        num_simulations=5000  # Reduced for report generation speed
    )
