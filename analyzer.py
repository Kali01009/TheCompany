import pandas as pd
from notifier import send_telegram_message


def identify_levels(data):
    data['Support'] = data['Low'].rolling(window=10).min()
    data['Resistance'] = data['High'].rolling(window=10).max()
    return data


def is_consolidating(data, window=10, threshold=0.02):
    recent = data.tail(window)
    max_close = recent['Close'].max()
    min_close = recent['Close'].min()
    return (max_close - min_close) / min_close < threshold


def analyze_selected_indices(selected_indices, data):
    data = identify_levels(data)
    trades = []

    for i in range(20, len(data)):
        if not is_consolidating(data.iloc[i - 10:i]):
            continue

        current = data.iloc[i]
        previous = data.iloc[i - 1]

        breakout_up = current['Close'] > previous['Resistance']
        breakout_down = current['Close'] < previous['Support']

        if breakout_up:
            entry = current['Close']
            stop_loss = entry - (previous['Resistance'] -
                                 previous['Support']) * 0.5
            take_profit = entry + (entry - stop_loss) * 1.5
            trades.append({
                'Time': current.name,
                'Direction': 'BUY',
                'Entry': round(entry, 2),
                'StopLoss': round(stop_loss, 2),
                'TakeProfit': round(take_profit, 2)
            })

        elif breakout_down:
            entry = current['Close']
            stop_loss = entry + (previous['Resistance'] -
                                 previous['Support']) * 0.5
            take_profit = entry - (stop_loss - entry) * 1.5
            trades.append({
                'Time': current.name,
                'Direction': 'SELL',
                'Entry': round(entry, 2),
                'StopLoss': round(stop_loss, 2),
                'TakeProfit': round(take_profit, 2)
            })

    for index in selected_indices:
        for trade in trades:
            msg = (f"🚨 *Breakout Detected* for *{index}* @ {trade['Time']}\n"
                   f"Direction: *{trade['Direction']}*\n"
                   f"Entry Price: `{trade['Entry']}`\n"
                   f"Stop Loss: `{trade['StopLoss']}`\n"
                   f"Take Profit: `{trade['TakeProfit']}`")
            send_telegram_message(msg)
