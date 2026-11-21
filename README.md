# SMARTSTOK — Enterprise Inventory & Sales System berbasis AI

Implementasi berdasarkan proposal **Sistem Manajemen Inventori & Penjualan UMKM Berbasis AI (SMARTSTOK)**. Proposal menyebut modul autentikasi, master data, inventori, penjualan, pembelian, dashboard/laporan, AI prediksi permintaan, chatbot bisnis, dan deteksi anomali opsional. fileciteturn0file0L51-L64

## Teknologi
- Backend: Python + FastAPI + SQLAlchemy + JWT
- Database: MySQL (bisa SQLite untuk demo cepat)
- Frontend: React + Vite + Chart.js
- AI/ML: pandas + scikit-learn; baseline moving average
- Laporan: CSV dan PDF (backend)
- Docker Compose opsional

## Fitur tambahan yang sengaja ditambahkan
- Manajemen pelanggan
- Audit log
- Low-stock dan near-expiry alert
- Profit/kinerja penjualan
- Filter laporan berdasarkan bulan
- Export CSV/PDF
- Forecast 7–30 hari dan rekomendasi restock
- Anomali transaksi sederhana
- Role admin/kasir/gudang
- Backup database SQL

## Akun demo
- admin / admin123
- kasir / kasir123
- gudang / gudang123

## Menjalankan dengan Docker
1. Salin `.env.example` menjadi `.env`.
2. `docker compose up --build`
3. Frontend: http://localhost:5173
4. API docs: http://localhost:8000/docs

## Menjalankan tanpa Docker
### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Jika MySQL tersedia, ubah `DATABASE_URL` di `.env`. Untuk demo paling cepat, gunakan SQLite: `sqlite:///./smartstok.db`.
