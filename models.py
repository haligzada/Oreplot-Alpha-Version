from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    
    full_name = Column(String)
    company = Column(String)
    role = Column(String)
    phone = Column(String)
    avatar_url = Column(String)
    
    api_key = Column(String, unique=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String)
    
    theme = Column(String, default='light')
    notifications_enabled = Column(Boolean, default=True)
    ai_behavior_settings = Column(JSON)
    
    plan_type = Column(String, default='free')
    usage_count = Column(Integer, default=0)
    usage_limit = Column(Integer, default=10)
    billing_status = Column(String, default='active')
    
    ai_tier_access = Column(String, default='light_ai')  # 'light_ai', 'advanced_ai', 'both'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    scoring_templates = relationship("ScoringTemplate", back_populates="user", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    owned_teams = relationship("Team", back_populates="owner", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    commodity = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    financial_models = relationship("FinancialModel", back_populates="project", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    scoring_template_id = Column(Integer, ForeignKey('scoring_templates.id'), nullable=True)
    
    analysis_type = Column(String, default='light_ai')  # 'light_ai' or 'advanced_ai'
    
    total_score = Column(Float, nullable=False)
    risk_category = Column(String, nullable=False)
    probability_of_success = Column(Float, nullable=False)
    
    geology_score = Column(Float)
    geology_weight = Column(Float)
    geology_contribution = Column(Float)
    geology_findings = Column(Text)
    
    resource_score = Column(Float)
    resource_weight = Column(Float)
    resource_contribution = Column(Float)
    resource_findings = Column(Text)
    
    economics_score = Column(Float)
    economics_weight = Column(Float)
    economics_contribution = Column(Float)
    economics_findings = Column(Text)
    
    legal_score = Column(Float)
    legal_weight = Column(Float)
    legal_contribution = Column(Float)
    legal_findings = Column(Text)
    
    permitting_score = Column(Float)
    permitting_weight = Column(Float)
    permitting_contribution = Column(Float)
    permitting_findings = Column(Text)
    
    data_quality_score = Column(Float)
    data_quality_weight = Column(Float)
    data_quality_contribution = Column(Float)
    data_quality_findings = Column(Text)
    
    recommendations = Column(JSON)
    ai_analysis_raw = Column(JSON)
    
    executive_summary = Column(Text)
    strategic_recommendations = Column(JSON)
    project_timeline = Column(Text)
    jurisdictional_context = Column(Text)
    strategic_signals = Column(JSON)
    
    sustainability_score = Column(Float)
    environmental_score = Column(Float)
    environmental_weight = Column(Float)
    environmental_contribution = Column(Float)
    environmental_findings = Column(Text)
    
    social_score = Column(Float)
    social_weight = Column(Float)
    social_contribution = Column(Float)
    social_findings = Column(Text)
    
    governance_score = Column(Float)
    governance_weight = Column(Float)
    governance_contribution = Column(Float)
    governance_findings = Column(Text)
    
    climate_score = Column(Float)
    climate_weight = Column(Float)
    climate_contribution = Column(Float)
    climate_findings = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="analyses")
    scoring_template = relationship("ScoringTemplate")
    comparable_matches = relationship("ComparableMatch", back_populates="analysis", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer)
    file_path = Column(String)
    
    extracted_text = Column(Text)
    extraction_success = Column(Boolean, default=True)
    extraction_error = Column(Text)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="documents")

class ScoringTemplate(Base):
    __tablename__ = 'scoring_templates'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    
    geology_weight = Column(Float, default=0.20)
    resource_weight = Column(Float, default=0.25)
    economics_weight = Column(Float, default=0.25)
    legal_weight = Column(Float, default=0.10)
    permitting_weight = Column(Float, default=0.10)
    data_quality_weight = Column(Float, default=0.10)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="scoring_templates")

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = 'team_members'
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String, default='member')
    
    invited_at = Column(DateTime, default=datetime.utcnow)
    joined_at = Column(DateTime)
    status = Column(String, default='active')
    
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

class ComparableProject(Base):
    """Reference database of real mining projects for benchmarking"""
    __tablename__ = 'comparable_projects'
    __table_args__ = (
        Index('idx_comparable_commodity_group', 'commodity_group'),
        Index('idx_comparable_deposit_style', 'deposit_style'),
        Index('idx_comparable_jurisdiction_risk', 'jurisdiction_risk_band'),
        Index('idx_comparable_dev_stage', 'development_stage_detail'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name = Column(String, nullable=False, index=True)
    company = Column(String)
    location = Column(String, index=True)
    country = Column(String, index=True)
    commodity = Column(String, index=True)
    
    # Project Status & Stage
    project_stage = Column(String, index=True)  # exploration, development, production, closed
    status = Column(String)  # active, suspended, completed
    
    # Geological Data
    geology_type = Column(String)  # deposit type (e.g., porphyry copper, epithermal gold)
    total_resource_mt = Column(Float)  # Total resource in million tonnes
    grade = Column(Float)  # Average grade
    grade_unit = Column(String)  # g/t, %, ppm
    
    # Economic Metrics
    capex_millions_usd = Column(Float)  # Capital expenditure
    opex_per_tonne_usd = Column(Float)  # Operating cost
    npv_millions_usd = Column(Float)  # Net present value
    irr_percent = Column(Float)  # Internal rate of return
    payback_years = Column(Float)
    
    # Production Data
    annual_production = Column(Float)
    production_unit = Column(String)  # tonnes, ounces, etc.
    mine_life_years = Column(Float)
    
    # Deal/Transaction Data
    acquisition_value_millions_usd = Column(Float)
    acquisition_date = Column(DateTime)
    transaction_type = Column(String)  # acquisition, merger, JV, etc.
    
    # Risk Factors
    permitting_duration_months = Column(Float)
    esg_rating = Column(String)  # A, B, C, D rating
    political_risk_score = Column(Float)  # 0-10
    
    # Benchmarking Scores (if available)
    geology_score = Column(Float)
    resource_score = Column(Float)
    economics_score = Column(Float)
    legal_score = Column(Float)
    permitting_score = Column(Float)
    data_quality_score = Column(Float)
    overall_score = Column(Float)
    
    # Source & Metadata
    data_source = Column(String)  # e.g., "NI 43-101 Report", "SEDAR+", "Company Website"
    source_url = Column(String)
    data_quality = Column(String)  # high, medium, low
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Additional Information
    notes = Column(Text)
    tags = Column(JSON)  # Searchable tags
    
    development_stage_detail = Column(String)
    jurisdiction_risk_band = Column(String)
    commodity_group = Column(String)
    deposit_style = Column(String)
    approved_for_display = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ingestion_logs = relationship("ComparableIngestion", back_populates="comparable", cascade="all, delete-orphan")

class FinancialModel(Base):
    """Financial model for NPV/IRR calculations and valuations"""
    __tablename__ = 'financial_models'
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    model_type = Column(String, default='dcf')
    
    base_commodity_price = Column(Float)
    commodity_price_unit = Column(String)
    production_profile = Column(JSON)
    
    initial_capex_millions = Column(Float)
    sustaining_capex_millions = Column(Float)
    opex_per_unit = Column(Float)
    opex_unit = Column(String)
    
    discount_rate = Column(Float, default=10.0)
    mine_life_years = Column(Integer)
    ramp_up_years = Column(Integer, default=1)
    
    revenue_assumptions = Column(JSON)
    cost_assumptions = Column(JSON)
    tax_assumptions = Column(JSON)
    
    calculated_npv = Column(Float)
    calculated_irr = Column(Float)
    calculated_payback_years = Column(Float)
    calculated_metrics = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="financial_models")
    scenarios = relationship("FinancialScenario", back_populates="financial_model", cascade="all, delete-orphan")

class FinancialScenario(Base):
    """Different scenarios for sensitivity analysis"""
    __tablename__ = 'financial_scenarios'
    
    id = Column(Integer, primary_key=True, index=True)
    financial_model_id = Column(Integer, ForeignKey('financial_models.id'), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(Text)
    scenario_type = Column(String)
    
    variable_name = Column(String)
    variable_value = Column(Float)
    variable_change_percent = Column(Float)
    
    assumptions_override = Column(JSON)
    cashflow_data = Column(JSON)
    
    npv_result = Column(Float)
    irr_result = Column(Float)
    sensitivity_impact = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    financial_model = relationship("FinancialModel", back_populates="scenarios")

class CommodityPriceSnapshot(Base):
    """Cached commodity price data from external APIs"""
    __tablename__ = 'commodity_prices'
    
    id = Column(Integer, primary_key=True, index=True)
    
    commodity = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String, default='USD')
    unit = Column(String)
    
    price_change_24h = Column(Float)
    price_change_percent_24h = Column(Float)
    
    high_52w = Column(Float)
    low_52w = Column(Float)
    
    source = Column(String)
    source_url = Column(String)
    
    historical_data = Column(JSON)
    
    fetched_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ComparableMatch(Base):
    """Tracks matched comparable projects for analyses"""
    __tablename__ = 'comparable_matches'
    __table_args__ = (
        UniqueConstraint('analysis_id', 'comparable_id', name='uq_analysis_comparable'),
        Index('idx_comparable_match_analysis', 'analysis_id'),
        Index('idx_comparable_match_comparable', 'comparable_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    comparable_id = Column(Integer, ForeignKey('comparable_projects.id'), nullable=False)
    
    similarity_score = Column(Float, nullable=False)
    match_criteria = Column(JSON)
    rank = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analysis = relationship("Analysis", back_populates="comparable_matches")
    comparable = relationship("ComparableProject")

class IngestionJob(Base):
    """Scheduled jobs for auto-updating comparables database"""
    __tablename__ = 'ingestion_jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    
    status = Column(String, default='pending')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    total_records = Column(Integer)
    successful_records = Column(Integer)
    failed_records = Column(Integer)
    error_log = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ingestions = relationship("ComparableIngestion", back_populates="job", cascade="all, delete-orphan")

class ComparableIngestion(Base):
    """Log of ingested comparable project data"""
    __tablename__ = 'comparable_ingestions'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('ingestion_jobs.id'), nullable=False)
    comparable_id = Column(Integer, ForeignKey('comparable_projects.id'), nullable=True)
    
    project_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("IngestionJob", back_populates="ingestions")
    comparable = relationship("ComparableProject", back_populates="ingestion_logs")


class TrainingCollection(Base):
    """Collection of training documents for AI reference/few-shot learning"""
    __tablename__ = 'training_collections'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, index=True)  # resource_statements, financial_tables, drill_data, etc.
    commodity = Column(String, index=True)  # gold, copper, lithium, etc.
    
    total_documents = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    processing_status = Column(String, default='pending')  # pending, processing, completed, error
    processing_progress = Column(Float, default=0.0)
    processing_error = Column(Text)
    
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = relationship("TrainingDocument", back_populates="collection", cascade="all, delete-orphan")
    examples = relationship("TrainingExample", back_populates="collection", cascade="all, delete-orphan")


class TrainingDocument(Base):
    """Individual training document uploaded by admin"""
    __tablename__ = 'training_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('training_collections.id'), nullable=False)
    
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, xlsx
    file_size = Column(Integer)
    file_path = Column(String)  # Path in storage
    
    extracted_text = Column(Text)
    extraction_status = Column(String, default='pending')  # pending, processing, completed, error
    extraction_error = Column(Text)
    page_count = Column(Integer)
    char_count = Column(Integer)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    collection = relationship("TrainingCollection", back_populates="documents")
    chunks = relationship("TrainingChunk", back_populates="document", cascade="all, delete-orphan")


class TrainingChunk(Base):
    """Chunked segments from training documents for retrieval"""
    __tablename__ = 'training_chunks'
    __table_args__ = (
        Index('idx_training_chunk_category', 'category'),
        Index('idx_training_chunk_doc', 'document_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('training_documents.id'), nullable=False)
    
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_type = Column(String)  # text, table, header
    category = Column(String, index=True)  # resource_statement, financial_table, drill_data, etc.
    
    start_page = Column(Integer)
    end_page = Column(Integer)
    token_count = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("TrainingDocument", back_populates="chunks")


class TrainingExample(Base):
    """Curated gold-standard examples extracted from training documents"""
    __tablename__ = 'training_examples'
    __table_args__ = (
        Index('idx_training_example_category', 'category'),
        Index('idx_training_example_approved', 'is_approved'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('training_collections.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('training_documents.id'), nullable=True)
    
    category = Column(String, nullable=False, index=True)  # resource_statement, financial_table, etc.
    subcategory = Column(String)  # measured_indicated, proven_probable, npv_irr, etc.
    
    example_name = Column(String, nullable=False)
    example_description = Column(Text)
    
    source_text = Column(Text, nullable=False)  # Original text from document
    extracted_data = Column(JSON)  # Structured JSON extraction
    extraction_notes = Column(Text)  # Notes on how this was extracted
    
    quality_score = Column(Float)  # 0-10 rating of example quality
    is_approved = Column(Boolean, default=False)  # Admin approval for use
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime)
    
    usage_count = Column(Integer, default=0)  # How many times used in prompts
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    collection = relationship("TrainingCollection", back_populates="examples")


class TrainingCategory(Base):
    """Categories/taxonomies for organizing training data"""
    __tablename__ = 'training_categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    description = Column(Text)
    parent_category = Column(String)
    
    extraction_prompt = Column(Text)  # Custom prompt for this category
    validation_rules = Column(JSON)  # Rules for validating extractions
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdvancedValuation(Base):
    """Advanced AI valuation results including market multiples, Kilburn method, and Monte Carlo analysis"""
    __tablename__ = 'advanced_valuations'
    __table_args__ = (
        Index('idx_advanced_valuation_project', 'project_id'),
        Index('idx_advanced_valuation_analysis', 'analysis_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    valuation_type = Column(String, default='comprehensive')
    
    market_multiples_ev_per_oz = Column(Float)
    market_multiples_peer_median = Column(Float)
    market_multiples_implied_value = Column(Float)
    market_multiples_upside_percent = Column(Float)
    market_multiples_comparable_count = Column(Integer)
    market_multiples_data = Column(JSON)
    
    kilburn_base_acquisition_cost = Column(Float)
    kilburn_regional_prospectivity_score = Column(Float)
    kilburn_project_maturity_score = Column(Float)
    kilburn_local_geology_score = Column(Float)
    kilburn_analytical_data_score = Column(Float)
    kilburn_total_rating = Column(Float)
    kilburn_pem_multiplier = Column(Float)
    kilburn_appraised_value = Column(Float)
    kilburn_data = Column(JSON)
    
    historical_exploration_spend = Column(Float)
    mee_multiplier = Column(Float)
    mee_appraised_value = Column(Float)
    
    monte_carlo_simulations = Column(Integer, default=10000)
    monte_carlo_commodity_volatility = Column(Float)
    monte_carlo_npv_p10 = Column(Float)
    monte_carlo_npv_p50 = Column(Float)
    monte_carlo_npv_p90 = Column(Float)
    monte_carlo_probability_profit = Column(Float)
    monte_carlo_var_5_percent = Column(Float)
    monte_carlo_data = Column(JSON)
    
    resource_total_oz = Column(Float)
    resource_category = Column(String)
    commodity = Column(String)
    project_stage = Column(String)
    
    valuation_summary = Column(Text)
    valuation_recommendation = Column(String)
    confidence_level = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project")
    analysis = relationship("Analysis")


class TrainingEmbedding(Base):
    """Vector embeddings for enhanced RAG training system"""
    __tablename__ = 'training_embeddings'
    __table_args__ = (
        Index('idx_training_embedding_category', 'category'),
        Index('idx_training_embedding_commodity', 'commodity'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer)
    
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_tokens = Column(Integer)
    
    category = Column(String, index=True)
    commodity = Column(String, index=True)
    
    embedding = Column(JSON)
    embedding_model = Column(String, default='text-embedding-3-small')
    
    chunk_metadata = Column(JSON)
    
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingStats(Base):
    """Statistics and settings for the training system"""
    __tablename__ = 'training_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    
    total_documents = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    
    categories_count = Column(JSON)
    commodities_count = Column(JSON)
    
    last_upload_at = Column(DateTime)
    last_training_used_at = Column(DateTime)
    
    settings = Column(JSON)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
