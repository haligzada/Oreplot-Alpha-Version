import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from project_manager import ProjectManager
from financial_engine import FinancialEngine
from market_data import get_market_data_provider
from comparables_manager import ComparablesManager
from financial_exports import create_financial_exporter
from database import get_db_session
from models import FinancialModel, FinancialScenario
import json

def render_financials_page(current_user):
    """Render the Financial Analysis & Valuation page"""
    
    st.markdown("## 💰 Financial Analysis & Valuation")
    st.markdown("Comprehensive NPV/IRR modeling, sensitivity analysis, and project valuations")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 NPV/IRR Calculator",
        "📈 Sensitivity Analysis",
        "💎 Valuation Module",
        "🌐 Market Data"
    ])
    
    with tab1:
        render_npv_irr_calculator(current_user)
    
    with tab2:
        render_sensitivity_analysis(current_user)
    
    with tab3:
        render_valuation_module(current_user)
    
    with tab4:
        render_market_data(current_user)


def render_npv_irr_calculator(current_user):
    """NPV/IRR Calculator tab with interactive DCF model"""
    
    st.markdown("### 📊 NPV/IRR Calculator")
    st.markdown("Build discounted cash flow models and calculate project economics")
    
    projects = ProjectManager.get_user_projects(current_user['id'])
    
    if not projects:
        st.info("👉 No projects found. Create a project in the Projects page first.")
        return
    
    col_select1, col_select2 = st.columns([2, 1])
    
    with col_select1:
        project_names = [p['name'] for p in projects]
        selected_project_name = st.selectbox(
            "Select Project",
            project_names,
            key="npv_project_select"
        )
    
    with col_select2:
        model_name = st.text_input("Model Name", value="Base Case Model", key="npv_model_name")
    
    selected_project = next((p for p in projects if p['name'] == selected_project_name), None)
    
    if selected_project:
        st.markdown("---")
        st.markdown("#### Production & Pricing Assumptions")
        
        col_prod1, col_prod2, col_prod3 = st.columns(3)
        
        with col_prod1:
            mine_life_years = st.number_input(
                "Mine Life (years)",
                min_value=1,
                max_value=50,
                value=15,
                key="npv_mine_life"
            )
            
            annual_production = st.number_input(
                "Annual Production (tonnes)",
                min_value=1000.0,
                value=500000.0,
                step=10000.0,
                format="%.0f",
                key="npv_annual_prod"
            )
        
        with col_prod2:
            commodity_price = st.number_input(
                f"Commodity Price (USD per unit)",
                min_value=0.01,
                value=50.0,
                step=1.0,
                format="%.2f",
                key="npv_commodity_price"
            )
            
            recovery_rate = st.slider(
                "Metallurgical Recovery Rate (%)",
                min_value=0,
                max_value=100,
                value=85,
                key="npv_recovery"
            ) / 100
        
        with col_prod3:
            ramp_up_years = st.number_input(
                "Ramp-up Period (years)",
                min_value=0,
                max_value=5,
                value=1,
                key="npv_ramp_up"
            )
            
            total_resource = st.number_input(
                "Total Resource (million tonnes)",
                min_value=0.1,
                value=10.0,
                step=0.5,
                format="%.2f",
                key="npv_resource"
            )
        
        st.markdown("#### Cost Assumptions")
        
        col_cost1, col_cost2, col_cost3 = st.columns(3)
        
        with col_cost1:
            initial_capex = st.number_input(
                "Initial CAPEX (USD millions)",
                min_value=1.0,
                value=150.0,
                step=10.0,
                format="%.2f",
                key="npv_capex"
            )
            
            opex_per_unit = st.number_input(
                "Operating Cost (USD per tonne)",
                min_value=0.01,
                value=25.0,
                step=1.0,
                format="%.2f",
                key="npv_opex"
            )
        
        with col_cost2:
            sustaining_capex = st.number_input(
                "Sustaining CAPEX (USD millions/year)",
                min_value=0.0,
                value=5.0,
                step=1.0,
                format="%.2f",
                key="npv_sustaining_capex"
            )
            
            royalty_rate = st.slider(
                "Royalty Rate (%)",
                min_value=0,
                max_value=20,
                value=3,
                key="npv_royalty"
            ) / 100
        
        with col_cost3:
            discount_rate = st.slider(
                "Discount Rate (%)",
                min_value=1,
                max_value=25,
                value=10,
                key="npv_discount"
            ) / 100
            
            tax_rate = st.slider(
                "Corporate Tax Rate (%)",
                min_value=0,
                max_value=50,
                value=30,
                key="npv_tax"
            ) / 100
        
        st.markdown("---")
        
        if st.button("🧮 Calculate NPV / IRR", type="primary", use_container_width=True):
            
            with st.spinner("Calculating financial metrics..."):
                engine = FinancialEngine()
                
                production_profile = engine.generate_production_profile(
                    mine_life_years=mine_life_years,
                    annual_production_target=annual_production,
                    ramp_up_years=ramp_up_years
                )
                
                cashflow_model = engine.generate_cashflow_model(
                    mine_life_years=mine_life_years,
                    production_profile=production_profile,
                    commodity_price=commodity_price,
                    opex_per_unit=opex_per_unit,
                    initial_capex=initial_capex,
                    sustaining_capex_annual=sustaining_capex,
                    royalty_rate=royalty_rate,
                    tax_rate=tax_rate,
                    recovery_rate=recovery_rate
                )
                
                npv = engine.calculate_npv(cashflow_model['net_cashflow'], discount_rate)
                irr = engine.calculate_irr(cashflow_model['net_cashflow'])
                payback = engine.calculate_payback_period(cashflow_model['net_cashflow'])
                
                st.success("✅ Calculation complete!")
                
                st.markdown("### 📊 Results")
                
                col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
                
                with col_metric1:
                    st.metric(
                        label="Net Present Value",
                        value=f"${npv:,.2f}M",
                        delta="After-tax, discounted"
                    )
                
                with col_metric2:
                    st.metric(
                        label="Internal Rate of Return",
                        value=f"{irr:.2f}%" if irr else "N/A",
                        delta="Annual return"
                    )
                
                with col_metric3:
                    st.metric(
                        label="Payback Period",
                        value=f"{payback:.1f} years" if payback else "Never",
                        delta="Time to recover CAPEX"
                    )
                
                with col_metric4:
                    st.metric(
                        label="Total Production",
                        value=f"{sum(production_profile)/1000000:.2f}Mt",
                        delta=f"{mine_life_years} year mine life"
                    )
                
                st.markdown("---")
                
                st.markdown("### 💵 Cash Flow Table")
                
                df_cashflow = pd.DataFrame({
                    'Year': cashflow_model['years'],
                    'Production (t)': [f"{p:,.0f}" for p in cashflow_model['production']],
                    'Revenue ($M)': [f"{r:,.2f}" for r in cashflow_model['revenue']],
                    'OPEX ($M)': [f"{c:,.2f}" for c in cashflow_model['operating_costs']],
                    'CAPEX ($M)': [f"{c:,.2f}" for c in cashflow_model['capex']],
                    'EBITDA ($M)': [f"{e:,.2f}" for e in cashflow_model['ebitda']],
                    'Taxes ($M)': [f"{t:,.2f}" for t in cashflow_model['taxes']],
                    'Net CF ($M)': [f"{n:,.2f}" for n in cashflow_model['net_cashflow']]
                })
                
                st.dataframe(df_cashflow, use_container_width=True, height=400)
                
                st.markdown("---")
                
                st.markdown("### 📈 Cash Flow Chart")
                
                chart_df = pd.DataFrame({
                    'Year': cashflow_model['years'],
                    'Net Cash Flow': cashflow_model['net_cashflow'],
                    'Cumulative Cash Flow': np.cumsum(cashflow_model['net_cashflow'])
                })
                
                st.line_chart(chart_df.set_index('Year'), use_container_width=True)
                
                st.markdown("---")
                
                col_export1, col_export2 = st.columns([1, 1])
                
                with col_export1:
                    exporter = create_financial_exporter()
                    excel_data = exporter.export_cashflow_model(
                        project_name=selected_project['name'],
                        model_name=model_name,
                        cashflow_data=cashflow_model,
                        metrics={'npv': npv, 'irr': irr, 'payback': payback},
                        assumptions={
                            'mine_life': mine_life_years,
                            'commodity_price': commodity_price,
                            'initial_capex': initial_capex,
                            'opex_per_unit': opex_per_unit,
                            'discount_rate': discount_rate * 100,
                            'tax_rate': tax_rate * 100,
                            'total_production': sum(production_profile)
                        }
                    )
                    
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"{selected_project['name']}_{model_name}_Financial_Model.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_export2:
                    save_model = st.checkbox("💾 Save to database", value=True)
                
                if save_model:
                    try:
                        with get_db_session() as db:
                            financial_model = FinancialModel(
                                project_id=selected_project['id'],
                                user_id=current_user['id'],
                                name=model_name,
                                description=f"Financial model for {selected_project['name']}",
                                model_type='dcf',
                                base_commodity_price=commodity_price,
                                commodity_price_unit='USD',
                                production_profile=json.dumps(production_profile),
                                initial_capex_millions=initial_capex,
                                sustaining_capex_millions=sustaining_capex,
                                opex_per_unit=opex_per_unit,
                                opex_unit='USD/tonne',
                                discount_rate=discount_rate * 100,
                                mine_life_years=mine_life_years,
                                ramp_up_years=ramp_up_years,
                                revenue_assumptions=json.dumps({
                                    'recovery_rate': recovery_rate,
                                    'royalty_rate': royalty_rate
                                }),
                                cost_assumptions=json.dumps(cashflow_model),
                                tax_assumptions=json.dumps({'tax_rate': tax_rate}),
                                calculated_npv=npv,
                                calculated_irr=irr,
                                calculated_payback_years=payback,
                                calculated_metrics=json.dumps({
                                    'total_production': sum(production_profile),
                                    'total_revenue': sum(cashflow_model['revenue']),
                                    'total_opex': sum(cashflow_model['operating_costs'])
                                })
                            )
                            
                            db.add(financial_model)
                            db.commit()
                            
                            st.success(f"✅ Financial model '{model_name}' saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving financial model: {e}")


def render_sensitivity_analysis(current_user):
    """Sensitivity Analysis tab with tornado charts"""
    
    st.markdown("### 📈 Sensitivity Analysis")
    st.markdown("Analyze how changes in key variables impact NPV and IRR")
    
    projects = ProjectManager.get_user_projects(current_user['id'])
    
    if not projects:
        st.info("👉 No projects found. Create a project in the Projects page first.")
        return
    
    project_names = [p['name'] for p in projects]
    selected_project_name = st.selectbox(
        "Select Project",
        project_names,
        key="sensitivity_project_select"
    )
    
    selected_project = next((p for p in projects if p['name'] == selected_project_name), None)
    
    if selected_project:
        st.markdown("---")
        st.markdown("#### Base Case Assumptions")
        
        col_base1, col_base2 = st.columns(2)
        
        with col_base1:
            base_commodity_price = st.number_input("Commodity Price (USD)", value=50.0, key="sens_price")
            base_opex = st.number_input("OPEX per unit (USD)", value=25.0, key="sens_opex")
            base_capex = st.number_input("Initial CAPEX (USD millions)", value=150.0, key="sens_capex")
        
        with col_base2:
            base_production = st.number_input("Annual Production (tonnes)", value=500000.0, key="sens_prod")
            base_discount = st.slider("Discount Rate (%)", 1, 25, 10, key="sens_discount") / 100
            mine_life = st.number_input("Mine Life (years)", value=15, key="sens_mine_life")
        
        st.markdown("#### Sensitivity Range")
        
        col_range1, col_range2 = st.columns(2)
        
        with col_range1:
            variation_low = st.number_input("Low Variation (%)", value=-20, key="sens_low")
        
        with col_range2:
            variation_high = st.number_input("High Variation (%)", value=20, key="sens_high")
        
        st.markdown("---")
        
        if st.button("🔄 Run Sensitivity Analysis", type="primary", use_container_width=True):
            
            with st.spinner("Running sensitivity analysis..."):
                engine = FinancialEngine()
                
                base_params = {
                    'mine_life_years': mine_life,
                    'production_profile': engine.generate_production_profile(mine_life, base_production),
                    'commodity_price': base_commodity_price,
                    'opex_per_unit': base_opex,
                    'initial_capex': base_capex,
                    'sustaining_capex_annual': 5.0,
                    'royalty_rate': 0.03,
                    'tax_rate': 0.30,
                    'recovery_rate': 0.85
                }
                
                variables = ['commodity_price', 'opex_per_unit', 'initial_capex']
                variation_range = [variation_low, variation_high]
                
                sensitivity_df = engine.calculate_multi_variable_sensitivity(
                    base_params,
                    variables,
                    variation_range,
                    base_discount
                )
                
                st.success("✅ Sensitivity analysis complete!")
                
                st.markdown("### 📊 Tornado Chart (NPV Sensitivity)")
                
                st.markdown("**NPV Impact by Variable**")
                
                tornado_data = []
                for var in sensitivity_df.index:
                    low_npv = sensitivity_df.loc[var, variation_low]
                    high_npv = sensitivity_df.loc[var, variation_high]
                    range_val = abs(high_npv - low_npv)
                    
                    tornado_data.append({
                        'Variable': var.replace('_', ' ').title(),
                        'Low NPV': low_npv,
                        'High NPV': high_npv,
                        'Range': range_val
                    })
                
                tornado_df = pd.DataFrame(tornado_data).sort_values('Range', ascending=False)
                
                st.dataframe(tornado_df, use_container_width=True)
                
                st.markdown("---")
                
                st.markdown("### 📉 Detailed Sensitivity Tables")
                
                for variable in variables:
                    st.markdown(f"#### {variable.replace('_', ' ').title()}")
                    
                    results = engine.calculate_sensitivity_analysis(
                        base_params,
                        variable,
                        list(range(variation_low, variation_high + 1, 5)),
                        base_discount
                    )
                    
                    results_df = pd.DataFrame(results)
                    results_df['variation_pct'] = results_df['variation_pct'].apply(lambda x: f"{x:+.0f}%")
                    results_df['value'] = results_df['value'].apply(lambda x: f"{x:,.2f}")
                    results_df['npv'] = results_df['npv'].apply(lambda x: f"${x:,.2f}M")
                    results_df['irr'] = results_df['irr'].apply(lambda x: f"{x:.2f}%" if x else "N/A")
                    
                    st.dataframe(
                        results_df[['variation_pct', 'value', 'npv', 'irr']],
                        column_config={
                            'variation_pct': 'Change',
                            'value': 'Value',
                            'npv': 'NPV',
                            'irr': 'IRR'
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.markdown("---")


def render_valuation_module(current_user):
    """Valuation Module tab with comparables analysis"""
    
    st.markdown("### 💎 Valuation Module")
    st.markdown("Project valuation using DCF and comparable company analysis")
    
    projects = ProjectManager.get_user_projects(current_user['id'])
    
    if not projects:
        st.info("👉 No projects found. Create a project in the Projects page first.")
        return
    
    project_names = [p['name'] for p in projects]
    selected_project_name = st.selectbox(
        "Select Project",
        project_names,
        key="valuation_project_select"
    )
    
    selected_project = next((p for p in projects if p['name'] == selected_project_name), None)
    
    if selected_project:
        st.markdown("---")
        st.markdown("#### Project Parameters")
        
        col_val1, col_val2, col_val3 = st.columns(3)
        
        with col_val1:
            npv = st.number_input("NPV (USD millions)", value=250.0, key="val_npv")
            resource_tonnes = st.number_input("Total Resource (million tonnes)", value=10.0, key="val_resource")
        
        with col_val2:
            annual_production = st.number_input("Annual Production (tonnes)", value=500000.0, key="val_production")
            commodity = st.selectbox("Commodity", ["Gold", "Silver", "Copper", "Lithium", "Iron Ore"], key="val_commodity")
        
        with col_val3:
            project_stage = st.selectbox("Project Stage", ["Exploration", "Development", "Production"], key="val_stage")
            region = st.selectbox("Region", ["North America", "South America", "Africa", "Asia", "Australia"], key="val_region")
        
        st.markdown("---")
        
        if st.button("📊 Calculate Valuation", type="primary", use_container_width=True):
            
            with st.spinner("Calculating valuation..."):
                engine = FinancialEngine()
                comparables_mgr = ComparablesManager()
                
                comparable_multiples = {
                    'ev_per_resource': 25.0,
                    'ev_per_production': 500.0
                }
                
                valuation = engine.calculate_project_valuation(
                    npv=npv,
                    resource_tonnes=resource_tonnes * 1000000,
                    annual_production=annual_production,
                    comparable_multiples=comparable_multiples
                )
                
                st.success("✅ Valuation complete!")
                
                st.markdown("### 💰 Valuation Results")
                
                col_result1, col_result2, col_result3 = st.columns(3)
                
                with col_result1:
                    st.metric(
                        label="DCF Valuation",
                        value=f"${valuation['dcf_valuation']:,.2f}M",
                        delta="Net Present Value"
                    )
                
                with col_result2:
                    st.metric(
                        label="Value per Tonne Resource",
                        value=f"${valuation['resource_value_per_tonne']:.2f}",
                        delta="Resource Multiple"
                    )
                
                with col_result3:
                    st.metric(
                        label="Production Multiple",
                        value=f"${valuation['production_multiple']:,.2f}",
                        delta="Per tonne annual production"
                    )
                
                st.markdown("---")
                
                st.markdown("### 🌍 Comparable Valuations")
                
                if 'comp_valuation_resource' in valuation:
                    col_comp1, col_comp2 = st.columns(2)
                    
                    with col_comp1:
                        st.metric(
                            label="Comparable Valuation (Resource)",
                            value=f"${valuation.get('comp_valuation_resource', 0):,.2f}M",
                            delta=f"Based on industry multiples"
                        )
                    
                    with col_comp2:
                        st.metric(
                            label="Comparable Valuation (Production)",
                            value=f"${valuation.get('comp_valuation_production', 0):,.2f}M",
                            delta=f"Based on production metrics"
                        )
                
                st.markdown("---")
                
                st.markdown("### 📋 Valuation Summary")
                
                avg_valuation = (
                    valuation['dcf_valuation'] + 
                    valuation.get('comp_valuation_resource', valuation['dcf_valuation']) + 
                    valuation.get('comp_valuation_production', valuation['dcf_valuation'])
                ) / 3
                
                st.info(f"""
                **Average Valuation:** ${avg_valuation:,.2f}M
                
                **Valuation Range:** ${min(valuation['dcf_valuation'], valuation.get('comp_valuation_resource', valuation['dcf_valuation'])):,.2f}M - ${max(valuation['dcf_valuation'], valuation.get('comp_valuation_resource', valuation['dcf_valuation'])):,.2f}M
                
                **Methodology:** DCF analysis combined with comparable company multiples
                """)


def render_market_data(current_user):
    """Market Data tab with real-time commodity prices"""
    
    st.markdown("### 🌐 Market Data - Real-Time Commodity Prices")
    st.markdown("Live commodity pricing from Metals-API with 1-hour caching")
    
    market_data = get_market_data_provider()
    
    col_refresh1, col_refresh2 = st.columns([1, 3])
    
    with col_refresh1:
        use_cache = st.checkbox("Use Cached Data", value=True, key="market_use_cache")
    
    with col_refresh2:
        if st.button("🔄 Refresh Prices", type="primary"):
            use_cache = False
    
    st.markdown("---")
    
    with st.spinner("Fetching commodity prices..."):
        commodities_data = market_data.get_all_mining_commodities(use_cache=use_cache)
    
    if commodities_data:
        st.markdown("### 💵 Current Commodity Prices")
        
        price_data = []
        for commodity, data in commodities_data.items():
            price_data.append({
                'Commodity': commodity.title(),
                'Price': f"${data['price']:,.2f}",
                'Unit': data['unit'],
                'Source': data['source'],
                '24h Change': f"{data.get('change_pct_24h', 0):.2f}%" if data.get('change_pct_24h') else "N/A",
                'Last Updated': data.get('fetched_at', 'N/A')[:19],
                'Cached': '✅' if data.get('from_cache') else '🔴'
            })
        
        price_df = pd.DataFrame(price_data)
        
        st.dataframe(
            price_df,
            use_container_width=True,
            height=400,
            column_config={
                'Commodity': st.column_config.TextColumn('Commodity', width='medium'),
                'Price': st.column_config.TextColumn('Price', width='medium'),
                'Unit': st.column_config.TextColumn('Unit', width='medium'),
                '24h Change': st.column_config.TextColumn('24h Change', width='small'),
                'Source': st.column_config.TextColumn('Source', width='medium'),
                'Cached': st.column_config.TextColumn('Cache', width='small')
            }
        )
        
        st.markdown("---")
        
        st.markdown("### 🔍 Individual Commodity Lookup")
        
        col_lookup1, col_lookup2 = st.columns([2, 1])
        
        with col_lookup1:
            lookup_commodity = st.selectbox(
                "Select Commodity",
                ["gold", "silver", "copper", "lithium", "platinum", "palladium", "zinc", "nickel"],
                key="market_lookup"
            )
        
        with col_lookup2:
            if st.button("🔎 Get Price", use_container_width=True):
                commodity_data = market_data.get_commodity_price(lookup_commodity, use_cache=use_cache)
                
                if commodity_data:
                    col_price1, col_price2, col_price3 = st.columns(3)
                    
                    with col_price1:
                        st.metric(
                            label=f"{lookup_commodity.title()} Price",
                            value=f"${commodity_data['price']:,.2f}",
                            delta=commodity_data['unit']
                        )
                    
                    with col_price2:
                        st.metric(
                            label="24h Change",
                            value=f"{commodity_data.get('change_pct_24h', 0):.2f}%" if commodity_data.get('change_pct_24h') else "N/A",
                            delta="Percentage change"
                        )
                    
                    with col_price3:
                        st.metric(
                            label="Data Source",
                            value=commodity_data['source'],
                            delta="From cache" if commodity_data.get('from_cache') else "Live API"
                        )
        
        st.markdown("---")
        
        st.info("""
        **💡 Data Source Information:**
        
        - **Free Tier:** 100 API calls per month via Metals-API
        - **Cache Duration:** 1 hour (to minimize API usage)
        - **Mock Data:** Displayed when API key is not configured
        - **To enable live data:** Add your Metals-API key as `METALS_API_KEY` in secrets
        
        Get your free API key at: https://metals-api.com
        """)
    else:
        st.warning("⚠️ Unable to fetch commodity prices. Please check your API configuration.")
