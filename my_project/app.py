from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# Browser-er moto behavior korar jonno Header
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_price/<coin>')
def get_price(coin):
    try:
        symbol = f"{coin.upper()}USDT"
        
        # 24h Data with Headers
        url_24h = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        res_24h = requests.get(url_24h, headers=HEADERS).json()
        
        current_price = float(res_24h['lastPrice'])
        price_change_pct = float(res_24h['priceChangePercent'])
        high_24h = float(res_24h['highPrice'])
        low_24h = float(res_24h['lowPrice'])

        # K-Lines Data with Headers
        url_klines = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=4h&limit=20"
        res_klines = requests.get(url_klines, headers=HEADERS).json()
        
        highs = [float(candle[2]) for candle in res_klines]
        lows = [float(candle[3]) for candle in res_klines]

        support = min(lows)
        resistance = max(highs)
        
        dist_to_support = current_price - support
        dist_to_resistance = resistance - current_price

        if dist_to_support <= dist_to_resistance:
            trend = "Buy at Support 🟢 (Long Setup)"
            entry = support * 1.002
            tp = resistance * 0.99
            sl = support * 0.98
        else:
            trend = "Sell at Resistance 🔴 (Short Setup)"
            entry = resistance * 0.998
            tp = support * 1.01
            sl = resistance * 1.02

        return jsonify({
            "symbol": coin.upper(), "price": current_price, "change": price_change_pct,
            "trend": trend, "entry": round(entry, 4), "tp": round(tp, 4), "sl": round(sl, 4),
            "high": round(high_24h, 4), "low": round(low_24h, 4),
            "support": round(support, 4), "resistance": round(resistance, 4)
        })
    except Exception as e:
        return jsonify({"error": "Coin paowa jayni. (Binance API Limit)"})

@app.route('/get_market')
def get_market():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        # Market list anar somoy-o Headers lagbe
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        
        usdt_pairs = [item for item in data if str(item.get('symbol', '')).endswith('USDT')]
        sorted_by_pct = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
        gainers = sorted_by_pct[:20]
        losers = sorted_by_pct[-20:]
        
        sorted_by_vol = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        top_50 = sorted_by_vol[:50]
        
        def format_coin(c):
            return {"symbol": c['symbol'].replace('USDT', ''), "price": round(float(c['lastPrice']), 4), "change": round(float(c['priceChangePercent']), 2)}
            
        return jsonify({"top_50": [format_coin(c) for c in top_50], "gainers": [format_coin(c) for c in gainers], "losers": [format_coin(c) for c in reversed(losers)]})
    except Exception as e:
        return jsonify({"error": "Market data load hoyni."})

# ... Baki coin_details API-tao same vabe requests.get(url, headers=HEADERS) kore nio ...

if __name__ == '__main__':
    app.run(debug=True)