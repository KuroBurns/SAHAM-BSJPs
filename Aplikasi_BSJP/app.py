import streamlit as st
import datetime
import pytz
from bsjp_screener import screen_bsjp

st.set_page_config(page_title="Rekomendasi BSJP Saham", layout="wide")

st.title("📈 Rekomendasi Saham BSJP (Beli Sore Jual Pagi)")

st.markdown("""
Aplikasi ini memindai saham-saham **Gorengan & Second Liner** (volatilitas tinggi) di Bursa Efek Indonesia (BEI) untuk mencari **Top 3 Saham** yang cocok untuk dibeli pada sore hari (direkomendasikan jam **15:30 WIB**) dan dijual pada keesokan paginya.

**Kriteria BSJP High Probability:**
1. **Uptrend:** Harga berada di atas MA20 (mencegah saham yang sedang jatuh).
2. **Akumulasi Bandar:** OBV (On-Balance Volume) naik dan Volume transaksi > 1.2x rata-rata 5 hari.
3. **Closing Kuat:** Harga penutupan dekat dengan harga tertinggi hari ini (toleransi ekor atas max 3%).
4. **Breakout (Opsional/Bonus):** Mencatat rekor penutupan tertinggi baru dalam 10 hari terakhir.
""")

# Menampilkan waktu saat ini (WIB)
try:
    tz_wib = pytz.timezone('Asia/Jakarta')
    now = datetime.datetime.now(tz_wib)
except:
    now = datetime.datetime.now()

st.write(f"**Waktu saat ini (Server):** {now.strftime('%Y-%m-%d %H:%M:%S')}")

if now.hour < 15:
    st.warning("⚠️ Sebaiknya tekan tombol generate pada pukul 15:30 - 15:50 WIB untuk mendapatkan data penutupan yang lebih akurat.")

if st.button("🔄 Generate Rekomendasi BSJP", type="primary"):
    with st.spinner('Memindai saham... (Estimasi 10-20 detik)'):
        try:
            df_rekomendasi = screen_bsjp()
            
            if df_rekomendasi is None or df_rekomendasi.empty:
                st.error("Tidak ada saham yang memenuhi kriteria BSJP yang ketat saat ini. Lebih baik 'Wait and See' besok.")
            else:
                st.success(f"✅ Berhasil menemukan {len(df_rekomendasi)} rekomendasi saham!")
                
                st.subheader("🔥 Top 3 Saham Pilihan Utama")
                # Menampilkan metrik utama untuk Top 3
                top_3 = df_rekomendasi.head(3)
                for index, row in top_3.iterrows():
                    status_text = row.get('Status', '🔥 BSJP')
                    with st.expander(f"📌 {row['Saham']} | {status_text} | Naik {row['Perubahan (%)']}% | Volatilitas: {row['Volatilitas 5H (%)']}%", expanded=True):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric("Harga Beli (Terakhir)", f"Rp {int(row['Harga Beli']):,}")
                        col2.metric("Target Jual Pagi (+1%)", f"Rp {int(row['Target Jual (+1%)']):,}")
                        col3.metric("Target Jual Pagi (+3%)", f"Rp {int(row['Target Jual (+3%)']):,}")
                        col4.metric("Stop Loss", f"Rp {int(row['Stop Loss']):,}")
                        
                        st.info(f"Volume Transaksi: **{row['Rasio Vol']}x** lipat lebih besar dari rata-rata 5 hari. Saham ini tergolong aktif dan bergejolak (Volatilitas 5 Hari: **{row['Volatilitas 5H (%)']}%**).")
                
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")

st.markdown("---")
st.subheader("🔍 Verifikasi Saham Pilihan Anda")
st.write("Tertarik dengan saham tertentu tapi ragu apakah memenuhi standar BSJP yang ketat? Masukkan kodenya di bawah ini:")

col_input, col_btn = st.columns([3, 1])
with col_input:
    ticker_input = st.text_input("Kode Saham (contoh: KOTA, GOTO, BUMI):", max_chars=4).upper()
with col_btn:
    st.write("") # padding
    st.write("") # padding
    check_btn = st.button("Cek Kelayakan", use_container_width=True)

if check_btn and ticker_input:
    from bsjp_screener import check_specific_stock
    with st.spinner(f"Menganalisis {ticker_input}..."):
        result = check_specific_stock(ticker_input)
        
        if "error" in result:
            st.error(result["error"])
        else:
            col_bsjp, col_invest = st.columns(2)
            
            with col_bsjp:
                if result["Layak BSJP"]:
                    st.success(f"🚀 **LAYAK untuk BSJP!**")
                else:
                    st.warning(f"❌ **TIDAK LAYAK untuk BSJP.**")
                    
                st.write("**Evaluasi Trading Harian:**")
                for kriteria, detail in result["Evaluasi BSJP"].items():
                    icon = "✅" if detail["status"] else "❌"
                    st.markdown(f"{icon} **{kriteria}** *(Info: {detail['info']})*")
            
            with col_invest:
                if result["Layak Investasi"]:
                    st.success(f"💎 **LAYAK untuk INVESTASI Jangka Panjang!**")
                else:
                    st.warning(f"❌ **TIDAK LAYAK untuk Investasi Jangka Panjang.**")
                    
                st.write("**Evaluasi Fundamental & Long Term:**")
                for kriteria, detail in result["Evaluasi Investasi"].items():
                    icon = "✅" if detail["status"] else "❌"
                    st.markdown(f"{icon} **{kriteria}** *(Info: {detail['info']})*")
                
            st.markdown("---")
            st.write(f"**Harga Saat Ini:** Rp {int(result['Harga Saat Ini']):,}")
            if result["Layak BSJP"]:
                st.info(f"🎯 **Trading Plan:** Beli di Rp {int(result['Harga Saat Ini']):,} | Target Jual: Rp {int(result['Target Jual 1%']):,} - Rp {int(result['Target Jual 3%']):,} | Stop Loss: Rp {int(result['Stop Loss']):,}")

st.caption("⚠️ **Disclaimer:** Aplikasi ini dibuat hanya untuk tujuan referensi. Keputusan investasi dan trading sepenuhnya berada di tangan pengguna. Do your own research (DYOR).")
