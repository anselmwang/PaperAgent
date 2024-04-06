import os
from datetime import datetime, timedelta
from paper import get_papers, DATA_FOLDER

def download_data(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        file_path = os.path.join(DATA_FOLDER, f"{date_str}.jsonl")
        if not os.path.exists(file_path):
            print(f"Downloading data for {date_str}")
            get_papers(date_str)
        else:
            print(f"Data for {date_str} already exists, skipping.")
        current_date += timedelta(days=1)

if __name__ == "__main__":
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now() - timedelta(days=3)
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    download_data(start_date, end_date)
