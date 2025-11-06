import asyncio
import threading
import time
import schedule
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def start_nightly_reset_scheduler(user_manager, reset_time: str = "00:00") -> threading.Thread:
    """Запускает планировщик сброса лимитов"""
    def scheduler_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        def reset_job():
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{current_time}] Автоматический сброс лимитов")
            loop.run_until_complete(user_manager.reset_all_limits())

        schedule.every().day.at(reset_time).do(reset_job)
        logger.info(f"🔄 Планировщик сброса лимитов запущен (время: {reset_time})")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    return scheduler_thread