"""
Comparables Database Ingestion Service
Fetches mining project data from external sources and ingests into database
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import SessionLocal
from models import ComparableProject, IngestionJob, ComparableIngestion
import os
from openai import OpenAI

class ComparablesIngestionService:
    """Service for ingesting comparable mining projects into the database"""
    
    @staticmethod
    def create_ingestion_job() -> int:
        """Create a new ingestion job and return its ID"""
        db = SessionLocal()
        try:
            job = IngestionJob(
                status='in_progress',
                started_at=datetime.utcnow(),
                total_records=0,
                successful_records=0,
                failed_records=0
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job.id
        finally:
            db.close()
    
    @staticmethod
    def update_job_status(job_id: int, status: str, total: int = None, 
                         successful: int = None, failed: int = None, error_log: str = None):
        """Update ingestion job status"""
        db = SessionLocal()
        try:
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.status = status
                if status == 'completed' or status == 'failed':
                    job.completed_at = datetime.utcnow()
                if total is not None:
                    job.total_records = total
                if successful is not None:
                    job.successful_records = successful
                if failed is not None:
                    job.failed_records = failed
                if error_log:
                    job.error_log = error_log
                db.commit()
        finally:
            db.close()
    
    @staticmethod
    def ingest_from_ai_research(job_id: int, research_query: str = "recent mining project developments") -> Dict[str, Any]:
        """
        Use AI to research and generate comparable project data
        This is a placeholder that uses GPT to generate realistic mining project data
        In production, this would connect to real data sources like SEDAR+, S&P Capital IQ, etc.
        """
        db = SessionLocal()
        try:
            # Get OpenAI client
            api_key = os.getenv('AI_INTEGRATIONS_OPENAI_API_KEY')
            base_url = os.getenv('AI_INTEGRATIONS_OPENAI_BASE_URL')
            
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            
            # Research prompt to generate mining project data
            research_prompt = f"""Generate a list of 5 real or realistic mining projects for a comparables database.
For each project, provide:
- name: Project name
- company: Operating company
- location: Geographic location
- country: Country
- commodity: Primary commodity (Gold, Copper, Lithium, Nickel, etc.)
- commodity_group: Precious Metals, Base Metals, Battery Metals, Industrial Minerals
- project_stage: exploration, development, production, closed
- development_stage_detail: Early-Stage Exploration, Advanced Exploration, Pre-Feasibility, Feasibility, Construction, Operating, Care & Maintenance
- deposit_style: Porphyry, Epithermal, VMS, Sediment-Hosted, Pegmatite, etc.
- geology_type: Detailed deposit type
- total_resource_mt: Total resource in million tonnes (realistic number)
- grade: Average grade (realistic for commodity)
- grade_unit: g/t, %, ppm
- capex_millions_usd: Capital expenditure estimate
- opex_per_tonne_usd: Operating cost per tonne
- npv_millions_usd: Net present value
- irr_percent: Internal rate of return
- payback_years: Payback period
- annual_production: Annual production estimate
- production_unit: tonnes, oz, kg
- mine_life_years: Mine life
- jurisdiction_risk_band: Low Risk, Moderate Risk, High Risk, Very High Risk
- political_risk_score: 0-10 (0=lowest risk)
- data_source: Source of information
- overall_score: Overall project quality score 0-100

Return ONLY valid JSON array with exactly 5 projects. No markdown, no explanations."""

            response = client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {"role": "system", "content": "You are a mining industry data expert. Generate realistic mining project data in JSON format."},
                    {"role": "user", "content": research_prompt}
                ],
                temperature=0.7,
                reasoning_effort="high"
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            projects_data = json.loads(content)
            
            total_projects = len(projects_data)
            successful = 0
            failed = 0
            
            for project_data in projects_data:
                try:
                    # Create comparables ingestion record
                    ingestion_record = ComparableIngestion(
                        job_id=job_id,
                        project_name=project_data.get('name', 'Unknown Project'),
                        status='pending'
                    )
                    db.add(ingestion_record)
                    db.flush()
                    
                    # Create comparable project (pending approval)
                    comparable = ComparableProject(
                        name=project_data.get('name'),
                        company=project_data.get('company'),
                        location=project_data.get('location'),
                        country=project_data.get('country'),
                        commodity=project_data.get('commodity'),
                        commodity_group=project_data.get('commodity_group'),
                        project_stage=project_data.get('project_stage'),
                        development_stage_detail=project_data.get('development_stage_detail'),
                        deposit_style=project_data.get('deposit_style'),
                        geology_type=project_data.get('geology_type'),
                        total_resource_mt=project_data.get('total_resource_mt'),
                        grade=project_data.get('grade'),
                        grade_unit=project_data.get('grade_unit'),
                        capex_millions_usd=project_data.get('capex_millions_usd'),
                        opex_per_tonne_usd=project_data.get('opex_per_tonne_usd'),
                        npv_millions_usd=project_data.get('npv_millions_usd'),
                        irr_percent=project_data.get('irr_percent'),
                        payback_years=project_data.get('payback_years'),
                        annual_production=project_data.get('annual_production'),
                        production_unit=project_data.get('production_unit'),
                        mine_life_years=project_data.get('mine_life_years'),
                        jurisdiction_risk_band=project_data.get('jurisdiction_risk_band'),
                        political_risk_score=project_data.get('political_risk_score'),
                        overall_score=project_data.get('overall_score'),
                        data_source=project_data.get('data_source', 'AI Research'),
                        data_quality='medium',
                        approved_for_display=False,  # Pending admin approval
                        status='pending_approval'
                    )
                    
                    db.add(comparable)
                    db.flush()
                    
                    # Update ingestion record
                    ingestion_record.status = 'success'
                    successful += 1
                    
                except Exception as e:
                    failed += 1
                    if ingestion_record:
                        ingestion_record.status = 'failed'
                        ingestion_record.error_message = str(e)
            
            db.commit()
            
            # Update job status
            ComparablesIngestionService.update_job_status(
                job_id=job_id,
                status='completed',
                total=total_projects,
                successful=successful,
                failed=failed
            )
            
            return {
                'success': True,
                'total': total_projects,
                'successful': successful,
                'failed': failed,
                'job_id': job_id
            }
            
        except Exception as e:
            ComparablesIngestionService.update_job_status(
                job_id=job_id,
                status='failed',
                error_log=str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'job_id': job_id
            }
        finally:
            db.close()
    
    @staticmethod
    def run_weekly_ingestion() -> Dict[str, Any]:
        """
        Main entry point for weekly ingestion job
        This would be called by the scheduler
        """
        job_id = ComparablesIngestionService.create_ingestion_job()
        result = ComparablesIngestionService.ingest_from_ai_research(job_id)
        return result
    
    @staticmethod
    def get_pending_projects(limit: int = 50) -> List[ComparableProject]:
        """Get all projects pending approval"""
        db = SessionLocal()
        try:
            return db.query(ComparableProject).filter(
                ComparableProject.approved_for_display == False,
                ComparableProject.status == 'pending_approval'
            ).order_by(ComparableProject.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def approve_project(project_id: int) -> bool:
        """Approve a project for display"""
        db = SessionLocal()
        try:
            project = db.query(ComparableProject).filter(
                ComparableProject.id == project_id
            ).first()
            
            if project:
                project.approved_for_display = True
                project.status = 'active'
                project.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def reject_project(project_id: int) -> bool:
        """Reject and delete a project"""
        db = SessionLocal()
        try:
            project = db.query(ComparableProject).filter(
                ComparableProject.id == project_id
            ).first()
            
            if project:
                db.delete(project)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_ingestion_history(limit: int = 10) -> List[IngestionJob]:
        """Get recent ingestion jobs"""
        db = SessionLocal()
        try:
            return db.query(IngestionJob).order_by(
                IngestionJob.started_at.desc()
            ).limit(limit).all()
        finally:
            db.close()
