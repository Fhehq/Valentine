import threading
import time, schedule
from datetime import datetime


def start_nightly_reset_scheduler(user_manager, reset_time: str = "00:00") -> threading.Thread:
    def scheduler_loop():
        def reset_job():
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{current_time}] Автоматический сброс лимитов...")
            user_manager.reset_all_limits()

        schedule.every().day.at(reset_time).do(reset_job)
        print(f"🔄 Планировщик сброса лимитов запущен (время: {reset_time})")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    return scheduler_thread