import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import { BarChart3, Boxes, ShoppingCart, Truck, FileText, Bot, LogOut, Package, Users, AlertTriangle } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js';
import './styles.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const API = 'http://localhost:8000/api';
const money = n => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n || 0);

function api() {
  const t = localStorage.getItem('token');
  return axios.create({ baseURL: API, headers: t ? { Authorization: `Bearer ${t}` } : {} });
}

function Login({ onLogin }) {
  const [f, setF] = useState({ username: 'admin', password: 'admin123' }), [err, setErr] = useState('');
  const go = async e => {
    e.preventDefault();
    try {
      const r = await axios.post(API + '/auth/login', f);
      localStorage.setItem('token', r.data.access_token);
      localStorage.setItem('user', JSON.stringify(r.data.user));
      onLogin(r.data.user);
    } catch (x) {
      setErr(x.response?.data?.detail || 'Login gagal');
    }
  };
  return <div className="login"><div className="login-card"><div className="logo">S</div><h1>SMARTSTOK</h1><p>Enterprise Inventory & Sales + AI</p><form onSubmit={go}><input placeholder="Username" value={f.username} onChange={e => setF({ ...f, username: e.target.value })} /><input type="password" placeholder="Password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} /><button>Masuk</button></form>{err && <div className="error">{err}</div>}<small>Demo: admin/admin123 · kasir/kasir123 · gudang/gudang123</small></div></div>;
}

const menu = [
  ['dashboard', 'Dashboard', BarChart3],
  ['products', 'Produk', Boxes],
  ['sales', 'Penjualan', ShoppingCart],
  ['purchases', 'Pembelian', Truck],
  ['reports', 'Laporan', FileText],
  ['forecast', 'AI Forecast', Package],
  ['chat', 'AI Asisten', Bot],
  ['customers', 'Pelanggan', Users]
];

function App() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [page, setPage] = useState('dashboard');
  if (!user) return <Login onLogin={setUser} />;
  return <div className="app"><aside><div className="brand"><div className="logo sm">S</div><b>SMARTSTOK</b></div><div className="role">{user.name}<span>{user.role}</span></div>{menu.map(([id, n, I]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => setPage(id)}><I size={18} />{n}</button>)}<button className="logout" onClick={() => { localStorage.clear(); setUser(null); }}><LogOut size={18} />Keluar</button></aside><main><header><div><h2>{menu.find(x => x[0] === page)?.[1]}</h2><span>Sistem manajemen usaha terintegrasi</span></div><div className="header-right"><span className="pill">● Online</span><span>{new Date().toLocaleDateString('id-ID', { dateStyle: 'full' })}</span></div></header>{page === 'dashboard' && <Dashboard />}{page === 'products' && <Products user={user} />}{page === 'sales' && <Sales user={user} />}{page === 'purchases' && <Purchases />}{page === 'reports' && <Reports />}{page === 'forecast' && <Forecast />}{page === 'chat' && <Chat />}{page === 'customers' && <Customers />}</main></div>;
}

function Dashboard() {
  const [d, setD] = useState(null);
  useEffect(() => { api().get('/dashboard').then(r => setD(r.data)); }, []);
  if (!d) return <div className="loading">Memuat dashboard...</div>;
  const chart = { labels: d.daily.map(x => x.date.slice(8)), datasets: [{ label: 'Penjualan', data: d.daily.map(x => x.revenue), tension: .35 }] };
  return <><div className="cards"><Card title="Omzet Bulan Ini" value={money(d.revenue)} icon={ShoppingCart} /><Card title="Laba Kotor" value={money(d.profit)} icon={BarChart3} /><Card title="Transaksi" value={d.transactions} icon={FileText} /><Card title="Stok Menipis" value={d.low_stock} icon={AlertTriangle} danger /></div><div className="grid2"><section className="panel"><h3>Tren Penjualan Bulan {d.month}</h3><Line data={chart} options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: v => 'Rp ' + Number(v).toLocaleString('id-ID') } } } }} /></section><section className="panel"><h3>Produk Terlaris</h3>{d.top_products.map((x, i) => <div className="rank" key={x.name}><b>{i + 1}</b><span>{x.name}</span><strong>{x.qty} unit</strong></div>)}</section></div><section className="panel"><h3><AlertTriangle size={18} /> Peringatan Stok</h3>{d.alerts.length ? <table><thead><tr><th>Produk</th><th>Stok</th><th>Minimum</th><th>Status</th></tr></thead><tbody>{d.alerts.map(x => <tr key={x.id}><td>{x.name}</td><td>{x.stock}</td><td>{x.min_stock}</td><td><span className="badge red">Perlu Restock</span></td></tr>)}</tbody></table> : <div className="empty">Semua stok aman.</div>}</section></>;
}

function Card({ title, value, icon: Icon, danger }) {
  return <div className={'card ' + (danger ? 'danger' : '')}><div><span>{title}</span><strong>{value}</strong></div><div className="card-icon"><Icon size={23} /></div></div>;
}

function Products({ user }) {
  const [rows, setRows] = useState([]), [cats, setCats] = useState([]), [form, setForm] = useState({ sku: '', name: '', category_id: '', buy_price: 0, sell_price: 0, stock: 0, min_stock: 5, unit: 'pcs' }), [show, setShow] = useState(false);
  const load = () => { api().get('/products').then(r => setRows(r.data)); api().get('/categories').then(r => setCats(r.data)); };
  useEffect(() => { load(); }, []);
  const save = async e => {
    e.preventDefault();
    await api().post('/products', { ...form, category_id: form.category_id ? Number(form.category_id) : null });
    setShow(false);
    setForm({ sku: '', name: '', category_id: '', buy_price: 0, sell_price: 0, stock: 0, min_stock: 5, unit: 'pcs' });
    load();
  };
  return <section className="panel"><div className="toolbar"><div><h3>Master Produk</h3><span>{rows.length} produk aktif</span></div>{['admin', 'gudang'].includes(user.role) && <button onClick={() => setShow(true)}>+ Tambah Produk</button>}</div>{show && <Modal title="Tambah Produk" close={() => setShow(false)}><form className="formgrid" onSubmit={save}>{[['sku', 'SKU'], ['name', 'Nama Produk'], ['buy_price', 'Harga Beli'], ['sell_price', 'Harga Jual'], ['stock', 'Stok Awal'], ['min_stock', 'Stok Minimum']].map(([k, l]) => <label key={k}>{l}<input required value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} /></label>)}<label>Kategori<select value={form.category_id} onChange={e => setForm({ ...form, category_id: e.target.value })}><option value="">- pilih -</option>{cats.map(c => <option value={c.id} key={c.id}>{c.name}</option>)}</select></label><button>Simpan</button></form></Modal>}<table><thead><tr><th>SKU</th><th>Produk</th><th>Kategori</th><th>Harga Jual</th><th>Stok</th><th>Status</th></tr></thead><tbody>{rows.map(x => <tr key={x.id}><td>{x.sku}</td><td><b>{x.name}</b></td><td>{x.category}</td><td>{money(x.sell_price)}</td><td>{x.stock}</td><td>{x.stock <= x.min_stock ? <span className="badge red">Menipis</span> : <span className="badge green">Aman</span>}</td></tr>)}</tbody></table></section>;
}

function Sales() {
  const [products, setProducts] = useState([]), [customers, setCustomers] = useState([]), [cart, setCart] = useState([]), [customer, setCustomer] = useState(''), [pay, setPay] = useState(0), [msg, setMsg] = useState('');
  useEffect(() => { api().get('/products').then(r => setProducts(r.data)); api().get('/customers').then(r => setCustomers(r.data)); }, []);
  const add = p => {
    const old = cart.find(x => x.id === p.id);
    setCart(old ? cart.map(x => x.id === p.id ? { ...x, qty: x.qty + 1 } : x) : [...cart, { ...p, qty: 1 }]);
  };
  const total = cart.reduce((a, x) => a + x.sell_price * x.qty, 0);
  const checkout = async () => {
    try {
      const r = await api().post('/sales', { customer_id: customer ? Number(customer) : null, items: cart.map(x => ({ product_id: x.id, qty: x.qty })), payment: Number(pay) });
      setMsg(`Transaksi ${r.data.invoice_no} berhasil. Kembalian ${money(r.data.change)}`);
      setCart([]);
      setPay(0);
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Transaksi gagal');
    }
  };
  return <div className="pos"><section className="panel"><h3>Produk</h3><div className="product-grid">{products.map(p => <button className="product" key={p.id} disabled={!p.stock} onClick={() => add(p)}><b>{p.name}</b><span>{money(p.sell_price)}</span><small>Stok {p.stock}</small></button>)}</div></section><section className="panel cart"><h3>Keranjang</h3>{cart.map(x => <div className="cart-row" key={x.id}><span>{x.name}<small>{x.qty} × {money(x.sell_price)}</small></span><b>{money(x.qty * x.sell_price)}</b></div>)}{!cart.length && <div className="empty">Belum ada item</div>}<hr /><label>Pelanggan<select value={customer} onChange={e => setCustomer(e.target.value)}><option value="">Umum</option>{customers.map(c => <option value={c.id} key={c.id}>{c.name}</option>)}</select></label><div className="total">Total <strong>{money(total)}</strong></div><input type="number" placeholder="Nominal bayar" value={pay} onChange={e => setPay(e.target.value)} /><button disabled={!cart.length || pay < total} onClick={checkout}>Bayar Sekarang</button>{msg && <div className="success">{msg}</div>}</section></div>;
}

function Purchases() {
  const [products, setProducts] = useState([]), [sup, setSup] = useState([]), [items, setItems] = useState([]), [supplier, setSupplier] = useState(''), [msg, setMsg] = useState('');
  useEffect(() => { api().get('/products').then(r => setProducts(r.data)); api().get('/suppliers').then(r => setSup(r.data)); }, []);
  const add = p => setItems([...items, { ...p, qty: 1, cost_price: p.buy_price }]);
  const save = async () => {
    try {
      const r = await api().post('/purchases', { supplier_id: Number(supplier), items: items.map(x => ({ product_id: x.id, qty: Number(x.qty), cost_price: Number(x.cost_price) })) });
      setMsg(`PO ${r.data.po_no} diterima. Total ${money(r.data.total)}`);
      setItems([]);
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Gagal');
    }
  };
  return <div className="grid2"><section className="panel"><h3>Pilih Produk</h3><select value={supplier} onChange={e => setSupplier(e.target.value)}><option value="">Pilih pemasok</option>{sup.map(s => <option value={s.id} key={s.id}>{s.name}</option>)}</select><div className="product-grid">{products.map(p => <button className="product" key={p.id} onClick={() => add(p)}><b>{p.name}</b><span>HPP {money(p.buy_price)}</span></button>)}</div></section><section className="panel"><h3>Penerimaan Barang</h3>{items.map(x => <div className="cart-row" key={x.id}><span>{x.name}<input className="qty" type="number" value={x.qty} onChange={e => setItems(items.map(i => i.id === x.id ? { ...i, qty: e.target.value } : i))} /></span><b>{money(x.qty * x.cost_price)}</b></div>)}<button disabled={!supplier || !items.length} onClick={save}>Terima Pembelian</button>{msg && <div className="success">{msg}</div>}</section></div>;
}

function Reports() {
  const d = new Date();
  const [year, setYear] = useState(d.getFullYear());
  const [month, setMonth] = useState(d.getMonth() + 1);
  const [r, setR] = useState(null);
  const [err, setErr] = useState('');

  const load = () => {
    setErr('');
    api().get('/reports/monthly', { params: { year, month } })
      .then(x => setR(x.data))
      .catch(e => setErr(e.response?.data?.detail || 'Gagal memuat laporan'));
  };

  useEffect(() => {
    load();
  }, []);

  const list = Array.isArray(r?.products) ? r.products : [];

  return (
    <section className="panel">
      <div className="toolbar">
        <h3>Laporan Penjualan Bulanan</h3>
        <div className="filters">
          <input type="number" value={year} onChange={e => setYear(e.target.value)} />
          <select value={month} onChange={e => setMonth(e.target.value)}>
            {Array.from({ length: 12 }, (_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}
          </select>
          <button onClick={load}>Tampilkan</button>
          <a href={`${API}/reports/monthly.csv?year=${year}&month=${month}`} target="_blank" rel="noreferrer">CSV</a>
          <a href={`${API}/reports/monthly.pdf?year=${year}&month=${month}`} target="_blank" rel="noreferrer">PDF</a>
        </div>
      </div>
      {err && <div className="error">{err}</div>}
      {r && (
        <>
          <div className="summary">
            <Card title="Pendapatan" value={money(r.revenue)} icon={BarChart3} />
            <Card title="Unit Terjual" value={r.qty} icon={Boxes} />
          </div>
          <table>
            <thead>
              <tr><th>Produk</th><th>Qty</th><th>Pendapatan</th></tr>
            </thead>
            <tbody>
              {list.map((x, i) => <tr key={x.product || i}><td>{x.product}</td><td>{x.qty}</td><td>{money(x.revenue)}</td></tr>)}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}

function Forecast() {
  const [rows, setRows] = useState([]), [days, setDays] = useState(7);
  useEffect(() => { api().get('/ai/forecasts', { params: { days } }).then(r => setRows(r.data)); }, [days]);
  return <section className="panel"><div className="toolbar"><div><h3>AI Prediksi Permintaan & Restock</h3><span>Baseline moving average dari histori penjualan</span></div><select value={days} onChange={e => setDays(e.target.value)}><option value="7">7 hari</option><option value="14">14 hari</option><option value="30">30 hari</option></select></div><table><thead><tr><th>Produk</th><th>Stok</th><th>Rata-rata/Hari</th><th>Prediksi</th><th>Rekomendasi Restock</th></tr></thead><tbody>{rows.map(x => <tr key={x.product_id}><td><b>{x.product}</b></td><td>{x.stock}</td><td>{x.average_daily}</td><td>{x.forecast}</td><td>{x.restock > 0 ? <span className="badge red">Beli {x.restock}</span> : <span className="badge green">Cukup</span>}</td></tr>)}</tbody></table></section>;
}

function Chat() {
  const [q, setQ] = useState(''), [msgs, setMsgs] = useState([]);
  const send = async () => {
    if (!q.trim()) return;
    const ask = q;
    setQ('');
    setMsgs([...msgs, { who: 'me', text: ask }]);
    const r = await api().post('/ai/chat', { question: ask });
    setMsgs(m => [...m, { who: 'ai', text: r.data.answer }]);
  };
  return <section className="panel chat"><div className="chat-head"><Bot /> <div><h3>AI Asisten Bisnis</h3><span>Read-only • berbasis data SMARTSTOK</span></div></div><div className="messages">{msgs.length ? msgs.map((m, i) => <div className={m.who} key={i}>{m.text}</div>) : <div className="empty">Contoh: “Produk apa yang paling laku bulan ini?” atau “Berapa omzet bulan ini?”</div>}</div><div className="chat-input"><input value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder="Tanyakan kondisi bisnis..." /><button onClick={send}>Kirim</button></div></section>;
}

function Customers() {
  const [rows, setRows] = useState([]), [f, setF] = useState({ name: '', phone: '', address: '' });
  const load = () => api().get('/customers').then(r => setRows(r.data));
  useEffect(() => { load(); }, []);
  const save = async e => {
    e.preventDefault();
    await api().post('/customers', f);
    setF({ name: '', phone: '', address: '' });
    load();
  };
  return <div className="grid2"><section className="panel"><h3>Tambah Pelanggan</h3><form onSubmit={save} className="formgrid"><label>Nama<input required value={f.name} onChange={e => setF({ ...f, name: e.target.value })} /></label><label>No. HP<input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} /></label><label>Alamat<textarea value={f.address} onChange={e => setF({ ...f, address: e.target.value })} /></label><button>Simpan</button></form></section><section className="panel"><h3>Daftar Pelanggan</h3><table><thead><tr><th>Nama</th><th>HP</th><th>Poin</th></tr></thead><tbody>{rows.map(x => <tr key={x.id}><td>{x.name}</td><td>{x.phone}</td><td>{x.points}</td></tr>)}</tbody></table></section></div>;
}

function Modal({ title, close, children }) {
  return <div className="overlay"><div className="modal"><div className="toolbar"><h3>{title}</h3><button onClick={close}>×</button></div>{children}</div></div>;
}

createRoot(document.getElementById('root')).render(<App />);
