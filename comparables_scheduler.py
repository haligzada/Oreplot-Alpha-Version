"""
Scheduler for weekly comparables database updates
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from comparables_ingestion import ComparablesIngestionService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def run_weekly_update():
    """Execute weekly comparables database update"""
    try:
        logger.info("Starting weekly comparables database update...")
        result = ComparablesIngestionService.run_weekly_ingestion()
        
        if result.get('success'):
            logger.info(f"Weekly update completed successfully. Total: {result['total']}, Success: {result['successful']}, Failed: {result['failed']}")
        else:
            logger.error(f"Weekly update failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error during weekly update: {str(e)}")

def start_scheduler():
    """Start the background scheduler for weekly updates"""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # Schedule to run every Sunday at 2:00 AM
    scheduler.add_job(
        run_weekly_update,
        CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='weekly_comparables_update',
        name='Weekly Comparables Database Update',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Comparables update scheduler started. Next run: Sunday 2:00 AM")
    
    return scheduler

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Comparables update scheduler stopped")

def trigger_manual_update():
    """Manually trigger an update outside the schedule"""
    logger.info("Manual update triggered")
    return run_weekly_update()

def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    
    if scheduler is None:
        return {
            'running': False,
            'next_run': None
        }
    
    jobs = scheduler.get_jobs()
    if jobs:
        next_run = jobs[0].next_run_time
        return {
            'running': True,
            'next_run': next_run.isoformat() if next_run else None,
            'jobs': [{'id': j.id, 'name': j.name, 'next_run': j.next_run_time.isoformat() if j.next_run_time else None} for j in jobs]
        }
    
    return {
        'running': True,
        'next_run': None,
        'jobs': []
    }
