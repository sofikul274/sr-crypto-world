from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# 1. Single coin analysis (Support/Resistance)
@app.route('/get_price/<coin>')
def get_price(coin):
    try:
        symbol = f"{coin.upper()}USDT"
        
        url_24h = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        res_24h = requests.get(url_24h).json()
        current_price = float(res_24h['lastPrice'])
        price_change_pct = float(res_24h['priceChangePercent'])
        high_24h = float(res_24h['highPrice'])
        low_24h = float(res_24h['lowPrice'])

        url_klines = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=4h&limit=20"
        res_klines = requests.get(url_klines).json()
        
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
        return jsonify({"error": "Coin paowa jayni."})

# 2. Market List API (Top 50, Gainers, Losers)
@app.route('/get_market')
def get_market():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = requests.get(url).json()
        
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

# 3. NOTUN API: CoinGecko theke ATH, ATL, Market Cap anar jonno
@app.route('/coin_details/<symbol>')
def coin_details(symbol):
    try:
        # Binance theke current price
        binance_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        binance_res = requests.get(binance_url)
        if binance_res.status_code != 200:
            return jsonify({"error": "Coin Binance-e nei ba vul nam."})
        current_price = float(binance_res.json()['price'])

        # CoinGecko theke Details
        cg_search = requests.get(f"https://api.coingecko.com/api/v3/search?query={symbol}").json()
        coin_id = None
        for coin in cg_search.get('coins', []):
            if coin['symbol'].lower() == symbol.lower():
                coin_id = coin['id']
                break
        
        if not coin_id:
            return jsonify({"symbol": symbol.upper(), "price": current_price, "ath": "N/A", "atl": "N/A", "market_cap": "N/A", "total_supply": "N/A", "image": ""})

        # Fetch actual details
        cg_details = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false").json()
        
        market_data = cg_details.get('market_data', {})
        
        return jsonify({
            "symbol": symbol.upper(),
            "price": current_price,
            "ath": market_data.get('ath', {}).get('usd', 'N/A'),
            "atl": market_data.get('atl', {}).get('usd', 'N/A'),
            "market_cap": market_data.get('market_cap', {}).get('usd', 'N/A'),
            "total_supply": market_data.get('total_supply', 'N/A'),
            "circulating_supply": market_data.get('circulating_supply', 'N/A'),
            "image": cg_details.get('image', {}).get('small', '')
        })

    except Exception as e:
        return jsonify({"error": "Details an te shomossha hoyeche."})

if __name__ == '__main__':
    app.run(debug=True)