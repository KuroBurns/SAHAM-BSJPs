import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Daftar saham LQ45 atau saham liquid (bisa ditambah sesuai kebutuhan)
GORENGAN_STOCKS = [
    # Saham gorengan & second liner volatil
    "KOTA", "KIJA", "BAUT", "HOPE", "LUCY", "ATAP", "VICI", "FAPA", "WIFI", "KETR", 
    "DGNS", "UFOE", "EDGE", "BEBS", "SNLK", "ZYRX", "LFLO", "FIMP", "TAPG", "NPGF", 
    "ADCP", "MARI", "ABBA", "OASA", "BSBK", "WIRG", "BUMI", "BRMS", "DEWA", 
    "ENRG", "BINA", "BANK", "BBHI", "BBYB", "CARE", "VIVA", "VOKS", "VINS", 
    "WEHA", "WICO", "WINS", "REAL", "POLI", "MTPS", "POSA", "JAST", "FITT", "BOLA", 
    "CCSI", "SFAN", "POLU", "KJEN", "KAYU", "ITIC", "PAMG", "IPTV", "BLUE", "ENVY", 
    "EAST", "LIFE", "FUJI", "INOV", "ARKA", "SMKL", "HDIT", "KEEN", "BAPI", "TFAS", 
    "GGRP", "OPMS", "NZIA", "SLIS", "PURE", "IRRA", "DMMX", "TAYS", "WMPP", "RMKE",
    "OBMD", "IPPE", "NASI", "BSML", "SEMA", "ASLC", "NETV", "ENAK", "NTBK", "SMKM",
    "NANO", "BIKE", "SICO", "TLDN", "WINR", "IBOS", "OLIV", "ASHA", "SWID", "TRGU",
    "ARKO", "CHEM", "DEWI", "AXIO", "KRYA", "HATM", "RCCC", "GULA", "JARR", "AMMS",
    "RAFI", "KKES", "ELPI", "EURO", "KLIN", "TOOL", "BUAH", "CRAB", "MEDS", "COAL",
    "PRAY", "CBUT", "MKTR", "OMED", "PDPP", "KDTN", "ZATA", "NINE", "MMIX", "PADA",
    "ISAP", "VTNY", "SOUL", "ELIT", "BEER", "CBPE", "SUNI", "CBRE", "WINE", "BMBL",
    "PEVE", "LAJU", "FWCT", "NAYZ", "IRSX", "PACK", "VAST", "CHIP", "HALO", "KING",
    "FUTR", "HILL", "BDKR", "PTMP", "SAGE", "TRON", "CUAN", "NSSS", "GTRA", "HAJJ",
    "PIPA", "MENN", "AWAN", "RAAM", "DOOH", "JATI", "TYRE", "MGLV", "TRUE", "LABA",
    "ARCI", "IPAC", "MASB", "BMHS", "FLMC", "NICL", "UVCR", "HAIS", "OILS", "GPSO",
    "MCOL", "RSGK", "RUNS", "SBMA", "CMNT", "GTSI", "IDEA", "KUAS", "BOBA", "DEPO"
]

def round_to_tick(value):
    if value is None:
        return None
    if value < 200:
        tick = 1
    elif value < 500:
        tick = 2
    elif value < 2000:
        tick = 5
    elif value < 5000:
        tick = 10
    else:
        tick = 25
    return float(round(value / tick) * tick)

def fetch_stock_data(ticker):
    try:
        symbol = f"{ticker}.JK"
        stock = yf.Ticker(symbol)
        # Ambil data lebih panjang untuk MA20
        hist = stock.history(period="3mo")
        
        if hist.empty or len(hist) < 20:
            return None
            
        today = hist.iloc[-1]
        
        # Hitung metrik historis
        last_5_days = hist.tail(5)
        avg_vol_5d = last_5_days['Volume'].mean()
        
        # Volatilitas 5 hari
        max_high_5d = last_5_days['High'].max()
        min_low_5d = last_5_days['Low'].min()
        volatility_5d = ((max_high_5d - min_low_5d) / min_low_5d * 100) if min_low_5d > 0 else 0
        
        # Simple Moving Average 20 hari (Trend jangka pendek-menengah)
        sma_20 = hist['Close'].tail(20).mean()
        
        # Cek harga penutupan tertinggi selama 10 hari terakhir sebelum hari ini
        highest_close_10d = hist['Close'].tail(11).head(10).max()
        
        # Kalkulasi OBV (On-Balance Volume) sebagai proxy Akumulasi Bandar
        obv = [0]
        for i in range(1, len(hist)):
            if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                obv.append(obv[-1] + hist['Volume'].iloc[i])
            elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                obv.append(obv[-1] - hist['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        hist['OBV'] = obv
        
        obv_current = hist['OBV'].iloc[-1]
        obv_sma_5 = hist['OBV'].tail(5).mean()
        
        return {
            'Ticker': ticker,
            'Close': today['Close'],
            'Open': today['Open'],
            'High': today['High'],
            'Low': today['Low'],
            'Volume': today['Volume'],
            'AvgVolume5D': avg_vol_5d,
            'Volatility5D': volatility_5d,
            'SMA20': sma_20,
            'HighestClose10D': highest_close_10d,
            'OBV_Current': obv_current,
            'OBV_SMA5': obv_sma_5,
            'PreviousClose': hist.iloc[-2]['Close'] if len(hist) > 1 else today['Open']
        }
    except Exception as e:
        return None

def screen_bsjp(stocks_list=GORENGAN_STOCKS):
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        data_list = list(executor.map(fetch_stock_data, stocks_list))
        
    for data in data_list:
        if data is None:
            continue
            
        # KRITERIA BSJP SUPER KETAT (High Probability):
        
        close = data['Close']
        open_price = data['Open']
        high = data['High']
        low = data['Low']
        volume = data['Volume']
        avg_vol = data['AvgVolume5D']
        prev_close = data['PreviousClose']
        volatility = data['Volatility5D']
        sma_20 = data['SMA20']
        highest_10d = data['HighestClose10D']
        obv_current = data['OBV_Current']
        obv_sma_5 = data['OBV_SMA5']
        
        # 1. Tren Positif (Harga di atas MA20) -> Mencegah beli saham downtrend/jatuh pisau
        is_uptrend = close > sma_20
        
        # 2. Breakout Harian -> Harga hari ini lebih tinggi dari harga tertinggi 10 hari terakhir
        is_breakout = close >= highest_10d
        
        # 3. Akumulasi Besar -> Volume minimal 1.5x lipat dari rata-rata 5 hari
        is_volume_spike = volume > (avg_vol * 1.5)
        
        # 4. Closing Marubozu (Kuat) -> Harga penutupan sangat mepet dengan High (Toleransi bayangan atas max 1%)
        is_strong_close = high > 0 and close >= (high * 0.99)
        
        # 5. Volatilitas Cukup -> Untuk saham gorengan butuh pergerakan
        is_volatile = volatility > 5.0
        
        # 6. Akumulasi Bandar (OBV) -> Memastikan tren akumulasi lebih kuat dibanding buangan bandar
        is_bandar_akum = obv_current > obv_sma_5
        
        if close > open_price and close > prev_close:
            if is_uptrend and is_strong_close and is_volume_spike and is_volatile and is_bandar_akum:
                price_change_pct = (close - prev_close) / prev_close * 100
                vol_ratio = volume / avg_vol if avg_vol > 0 else 0
                
                # Tambahan bonus poin jika breakout
                breakout_bonus = 10 if is_breakout else 0
                score = price_change_pct + (vol_ratio * 3) + breakout_bonus
                
                target_sell_1 = round_to_tick(close * 1.01)
                target_sell_3 = round_to_tick(close * 1.03)
                stop_loss = round_to_tick(low if low < open_price else open_price)
                
                results.append({
                    'Saham': data['Ticker'],
                    'Harga Beli': close,
                    'Target Jual (+1%)': target_sell_1,
                    'Target Jual (+3%)': target_sell_3,
                    'Stop Loss': stop_loss,
                    'Perubahan (%)': round(price_change_pct, 2),
                    'Rasio Vol': round(vol_ratio, 2),
                    'Volatilitas 5H (%)': round(volatility, 2),
                    'Status': '🚀 Breakout & Akumulasi Bandar' if is_breakout else '✅ Akumulasi Bandar Kuat',
                    'Score': score
                })
                
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by='Score', ascending=False).head(3)
        df = df.drop(columns=['Score'])
        
    return df

def check_specific_stock(ticker):
    ticker = ticker.strip().upper()
    try:
        symbol = f"{ticker}.JK"
        stock = yf.Ticker(symbol)
        
        # Ambil data 1 tahun untuk MA200
        hist = stock.history(period="1y")
        
        if hist.empty or len(hist) < 20:
            return {"error": f"Data saham {ticker} tidak ditemukan atau terlalu baru."}
            
        today = hist.iloc[-1]
        close = today['Close']
        open_price = today['Open']
        high = today['High']
        low = today['Low']
        volume = today['Volume']
        
        last_5_days = hist.tail(5)
        avg_vol = last_5_days['Volume'].mean()
        
        max_high_5d = last_5_days['High'].max()
        min_low_5d = last_5_days['Low'].min()
        volatility = ((max_high_5d - min_low_5d) / min_low_5d * 100) if min_low_5d > 0 else 0
        
        sma_20 = hist['Close'].tail(20).mean()
        highest_10d = hist['Close'].tail(11).head(10).max()
        prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else today['Open']
        
        # Kalkulasi OBV
        obv = [0]
        for i in range(1, len(hist)):
            if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                obv.append(obv[-1] + hist['Volume'].iloc[i])
            elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                obv.append(obv[-1] - hist['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        hist['OBV'] = obv
        obv_current = hist['OBV'].iloc[-1]
        obv_sma_5 = hist['OBV'].tail(5).mean()
        
        # Data Jangka Panjang (Investasi)
        sma_200 = hist['Close'].mean() if len(hist) < 200 else hist['Close'].tail(200).mean()
        
        try:
            info = stock.info
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', info.get('forwardPE', 0))
            dividend = info.get('dividendYield', 0)
        except:
            market_cap = 0
            pe_ratio = 0
            dividend = 0
        
        # 1. EVALUASI BSJP
        is_green = close > open_price and close > prev_close
        is_uptrend = close > sma_20
        is_breakout = close >= highest_10d
        is_volume_spike = volume > (avg_vol * 1.5)
        is_strong_close = high > 0 and close >= (high * 0.99)
        is_volatile = volatility > 5.0
        is_bandar_akum = obv_current > obv_sma_5
        
        passed_all = is_green and is_uptrend and is_volume_spike and is_strong_close and is_volatile and is_bandar_akum
        
        # 2. EVALUASI INVESTASI JANGKA PANJANG
        is_long_uptrend = close > sma_200
        is_big_cap = market_cap > 5_000_000_000_000 # > 5 Triliun Rupiah
        is_good_pe = 0 < pe_ratio < 25 # Valuasi wajar
        is_dividend_payer = dividend is not None and dividend > 0.02 # Yield > 2%
        
        layak_investasi = is_long_uptrend and (is_big_cap or is_good_pe or is_dividend_payer)
        
        target_sell_1 = round_to_tick(close * 1.01)
        target_sell_3 = round_to_tick(close * 1.03)
        stop_loss = round_to_tick(low if low < open_price else open_price)
        
        return {
            "Saham": ticker,
            "Harga Saat Ini": close,
            "Layak BSJP": passed_all,
            "Layak Investasi": layak_investasi,
            "Target Jual 1%": target_sell_1,
            "Target Jual 3%": target_sell_3,
            "Stop Loss": stop_loss,
            "Evaluasi BSJP": {
                "Harga Naik Hari Ini": {"status": is_green, "info": f"Close: {close}, Open: {open_price}"},
                "Sedang Uptrend (Di atas MA20)": {"status": is_uptrend, "info": f"Close: {close}, MA20: {round(sma_20, 2)}"},
                "Volume Spike (> 1.5x Rata-rata)": {"status": is_volume_spike, "info": f"Vol: {int(volume):,}"},
                "Akumulasi Bandar (OBV Naik)": {"status": is_bandar_akum, "info": "Volume Beli mendominasi (OBV > MA5)"},
                "Closing Kuat (Mendekati High)": {"status": is_strong_close, "info": f"Close: {close}, High: {high}"},
                "Volatilitas Memadai (> 5%)": {"status": is_volatile, "info": f"{round(volatility, 2)}%"}
            },
            "Evaluasi Investasi": {
                "Tren Jangka Panjang (Di atas MA200)": {"status": is_long_uptrend, "info": f"MA200: {round(sma_200, 2)}"},
                "Kapitalisasi Pasar Besar (> 5T)": {"status": is_big_cap, "info": f"Rp {market_cap/1_000_000_000_000:.1f} Triliun"},
                "Valuasi (PE Ratio Wajar 0-25)": {"status": is_good_pe, "info": f"PE: {round(pe_ratio, 2) if pe_ratio else 'N/A'}"},
                "Membagikan Dividen (>2%)": {"status": is_dividend_payer, "info": f"Yield: {round(dividend*100, 2) if dividend else 0}%"}
            }
        }
    except Exception as e:
        return {"error": f"Terjadi kesalahan saat memproses data {ticker}: {str(e)}"}
