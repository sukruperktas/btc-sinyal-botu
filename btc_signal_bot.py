import pandas as pd
from binance.client import Client
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from config import *
from telegram import Bot
import asyncio
from datetime import datetime

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def get_data(symbol, interval, limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    return df

def calculate_indicators(df):
    df['ema'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
    bb = BollingerBands(close=df['close'])
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    if latest['macd'] > latest['macd_signal'] and latest['close'] > latest['ema'] and latest['rsi'] < 70:
        return "LONG"
    elif latest['macd'] < latest['macd_signal'] and latest['close'] < latest['ema'] and latest['rsi'] > 30:
        return "SHORT"
    else:
        return "NO_SIGNAL"

async def send_and_log(message):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    with open("trading_log.txt", "a", encoding="utf-8") as file:
        file.write(f"{datetime.now()} - {message}\n")

async def run_bot():
    while True:
        for tf in TIMEFRAMES:
            try:
                df = get_data(SYMBOL, tf)
                df = calculate_indicators(df)
                signal = generate_signal(df)
                msg = f"📊 {SYMBOL} | {tf} | Sinyal: {signal}"
                print(msg)
                await send_and_log(msg)
            except Exception as e:
                await send_and_log(f"❌ Hata (timeframe {tf}): {e}")
        print("🕒 Bekleniyor... 5 dakika...\n")
        await asyncio.sleep(300)

async def main():
    await run_bot()
