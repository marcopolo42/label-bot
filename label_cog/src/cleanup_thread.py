import os
import time
from datetime import datetime, timedelta
import threading


def delete_old_files(folder_path, days_old):
    #Deletes files in the specified folder that are older than a given number of days.
    cutoff_time = datetime.now() - timedelta(days=days_old)
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_modification_time < cutoff_time:
                try:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")


#Runs the delete_old_files function at specified intervals in a background thread.
def background_cleanup(folder_paths, days_old, interval_hours):
    while True:
        for folder_path in folder_paths:
            delete_old_files(folder_path, days_old)
        time.sleep(interval_hours * 3600)


def start_cleanup(folder_paths, days_old, interval_hours):
    # Setup and start the cleanup thread
    cleanup_thread = threading.Thread(target=background_cleanup, args=(folder_paths, days_old, interval_hours))
    cleanup_thread.daemon = True
    cleanup_thread.start()
