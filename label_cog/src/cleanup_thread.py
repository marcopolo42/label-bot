import os
import time
from datetime import datetime, timedelta
import threading
from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)

def delete_old_files(folder_path, minutes_old):
    #Deletes files in the specified folder that are older than a given number of days.
    cutoff_time = datetime.now() - timedelta(minutes=minutes_old)
    if not os.path.exists(folder_path):
        return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_modification_time < cutoff_time:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")


#Runs the delete_old_files function at specified intervals in a background thread.
def background_cleanup(folder_paths, minutes_old, minutes_interval):
    while True:
        for folder_path in folder_paths:
            delete_old_files(folder_path, minutes_old)
            time.sleep(minutes_interval * 60)


def start_cleanup(folder_paths, minutes_old, interval_minutes):
    # Setup and start the cleanup thread
    cleanup_thread = threading.Thread(target=background_cleanup, args=(folder_paths, minutes_old, interval_minutes))
    cleanup_thread.daemon = True
    cleanup_thread.start()
