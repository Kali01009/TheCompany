import logging
import random
from datetime import datetime
import pandas as pd
from analyzer import analyze_selected_indices


# Simulate sample OHLC data
def generate_sample_data():
    now = datetime.now()
    timestamps = pd.date_range(end=now, periods=100, freq='15T')
    data = pd.DataFrame(index=timestamps)
    data['Open'] = [random.uniform(100, 110) for _ in range(len(data))]
    data['High'] = data['Open'] + [
        random.uniform(0, 2) for _ in range(len(data))
    ]
    data['Low'] = data['Open'] - [
        random.uniform(0, 2) for _ in range(len(data))
    ]
    data['Close'] = [
        random.uniform(l, h) for l, h in zip(data['Low'], data['High'])
    ]
    return data


# Enable logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    selected_indices = ["R_10", "R_25", "R_50"]
    data = generate_sample_data()
    analyze_selected_indices(selected_indices, data)
