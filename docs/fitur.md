# Modul SMARTSTOK

| Modul | Implementasi |
|---|---|
| Autentikasi | JWT, role admin/kasir/gudang |
| Master Data | Produk, kategori, pemasok, pelanggan |
| Inventori | stok masuk/keluar, mutasi, minimum stock |
| Penjualan | POS, keranjang, pembayaran, kembalian, poin pelanggan |
| Pembelian | penerimaan barang dan update stok |
| Dashboard | omzet, laba kotor, transaksi, stok menipis, tren harian, produk terlaris |
| Laporan | laporan bulanan + CSV/PDF |
| AI Forecast | moving average 7/14/30 hari + rekomendasi restock |
| AI Asisten | chatbot bisnis read-only |
| Anomali | transaksi di atas 3x median 30 hari |
| Audit | pencatatan aktivitas penting |

## Catatan AI
Proposal mengusulkan baseline moving average lalu membandingkan dengan Prophet/Random Forest/XGBoost dan evaluasi MAE/RMSE. Versi implementasi ini menyediakan baseline moving average terlebih dahulu agar sistem dapat langsung dijalankan. Model lanjutan dapat ditambahkan setelah histori data cukup.
