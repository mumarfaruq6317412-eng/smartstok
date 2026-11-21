from datetime import datetime, timedelta
from io import BytesIO
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .db import Base, engine, get_db
from .models import *
from .schemas import *
from .auth import *
from .services import monthly_sales, forecast_product

Base.metadata.create_all(bind=engine)
app=FastAPI(title='SMARTSTOK API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def audit(db,user,action,entity,eid='',detail=''):
    db.add(AuditLog(user_id=user.id if user else None,action=action,entity=entity,entity_id=str(eid),detail=detail)); db.commit()

def seed():
    db=next(get_db())
    if db.query(User).count()==0:
        db.add_all([User(username='admin',password_hash=hash_password('admin123'),full_name='Administrator',role='admin'),User(username='kasir',password_hash=hash_password('kasir123'),full_name='Kasir',role='kasir'),User(username='gudang',password_hash=hash_password('gudang123'),full_name='Petugas Gudang',role='gudang')])
    if db.query(Category).count()==0:
        cats=[Category(name=x) for x in ['Minuman','Snack','Sembako','ATK','Kebersihan']]; db.add_all(cats); db.flush()
        sup=Supplier(name='PT Sumber Makmur',phone='081234567890',address='Surabaya'); db.add(sup); db.flush()
        products=[('SKU001','Air Mineral 600ml',1,2500,4000,80,15),('SKU002','Kopi Sachet',1,1200,2000,120,20),('SKU003','Mie Instan',3,2200,3000,100,20),('SKU004','Biskuit',2,5000,7000,40,10),('SKU005','Pulpen',4,2000,3500,25,5),('SKU006','Sabun Mandi',5,3500,5000,18,5)]
        for sku,name,cat,buy,sell,stock,minstock in products: db.add(Product(sku=sku,name=name,category_id=cat,supplier_id=sup.id,buy_price=buy,sell_price=sell,stock=stock,min_stock=minstock))
    db.commit(); db.close()
seed()

@app.get('/api/health')
def health(): return {'status':'ok','app':'SMARTSTOK'}

@app.post('/api/auth/login')
def login(data:LoginIn, db:Session=Depends(get_db)):
    u=db.query(User).filter(User.username==data.username).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,'Username atau password salah')
    return {'access_token':create_token(u),'token_type':'bearer','user':{'id':u.id,'username':u.username,'name':u.full_name,'role':u.role}}

@app.get('/api/auth/me')
def me(user=Depends(current_user)): return {'id':user.id,'username':user.username,'name':user.full_name,'role':user.role}

@app.get('/api/categories')
def categories(db=Depends(get_db), user=Depends(current_user)): return [{'id':x.id,'name':x.name} for x in db.query(Category).order_by(Category.name).all()]
@app.post('/api/categories')
def add_category(data:CategoryIn,db=Depends(get_db),user=Depends(require_roles('admin'))):
    x=Category(name=data.name); db.add(x); db.commit(); db.refresh(x); audit(db,user,'CREATE','category',x.id,x.name); return {'id':x.id,'name':x.name}

@app.get('/api/suppliers')
def suppliers(db=Depends(get_db), user=Depends(current_user)): return [{'id':x.id,'name':x.name,'phone':x.phone,'address':x.address} for x in db.query(Supplier).order_by(Supplier.name).all()]
@app.post('/api/suppliers')
def add_supplier(data:SupplierIn,db=Depends(get_db),user=Depends(require_roles('admin','gudang'))):
    x=Supplier(**data.model_dump()); db.add(x); db.commit(); db.refresh(x); audit(db,user,'CREATE','supplier',x.id,x.name); return x

@app.get('/api/products')
def products(db=Depends(get_db),user=Depends(current_user)):
    return [{'id':x.id,'sku':x.sku,'name':x.name,'category_id':x.category_id,'category':x.category.name if x.category else '', 'supplier_id':x.supplier_id,'buy_price':x.buy_price,'sell_price':x.sell_price,'stock':x.stock,'min_stock':x.min_stock,'unit':x.unit,'expiry_date':x.expiry_date} for x in db.query(Product).filter(Product.active==True).order_by(Product.name).all()]
@app.post('/api/products')
def add_product(data:ProductIn,db=Depends(get_db),user=Depends(require_roles('admin','gudang'))):
    if db.query(Product).filter(Product.sku==data.sku).first(): raise HTTPException(400,'SKU sudah digunakan')
    x=Product(**data.model_dump()); db.add(x); db.commit(); db.refresh(x); audit(db,user,'CREATE','product',x.id,x.name); return {'id':x.id}
@app.put('/api/products/{pid}')
def update_product(pid:int,data:ProductIn,db=Depends(get_db),user=Depends(require_roles('admin','gudang'))):
    x=db.get(Product,pid)
    if not x: raise HTTPException(404,'Produk tidak ditemukan')
    for k,v in data.model_dump().items(): setattr(x,k,v)
    db.commit(); audit(db,user,'UPDATE','product',pid,x.name); return {'message':'updated'}
@app.delete('/api/products/{pid}')
def delete_product(pid:int,db=Depends(get_db),user=Depends(require_roles('admin'))):
    x=db.get(Product,pid)
    if not x: raise HTTPException(404,'Produk tidak ditemukan')
    x.active=False; db.commit(); audit(db,user,'DELETE','product',pid,x.name); return {'message':'deleted'}

@app.get('/api/customers')
def customers(db=Depends(get_db),user=Depends(current_user)): return [{'id':x.id,'name':x.name,'phone':x.phone,'address':x.address,'points':x.points} for x in db.query(Customer).order_by(Customer.name).all()]
@app.post('/api/customers')
def add_customer(data:CustomerIn,db=Depends(get_db),user=Depends(current_user)):
    x=Customer(**data.model_dump()); db.add(x); db.commit(); db.refresh(x); return x

@app.post('/api/stock/adjust')
def adjust_stock(data:StockAdjustIn,db=Depends(get_db),user=Depends(require_roles('admin','gudang'))):
    p=db.get(Product,data.product_id)
    if not p: raise HTTPException(404,'Produk tidak ditemukan')
    if p.stock+data.qty<0: raise HTTPException(400,'Stok tidak cukup')
    p.stock+=data.qty; db.add(StockMovement(product_id=p.id,movement_type='adjustment',qty=data.qty,reference='MANUAL',note=data.note)); db.commit(); audit(db,user,'STOCK_ADJUST','product',p.id,data.note); return {'stock':p.stock}
@app.get('/api/stock/movements')
def movements(db=Depends(get_db),user=Depends(current_user)): return [{'id':m.id,'product_id':m.product_id,'type':m.movement_type,'qty':m.qty,'reference':m.reference,'note':m.note,'created_at':m.created_at} for m in db.query(StockMovement).order_by(desc(StockMovement.created_at)).limit(200).all()]

@app.post('/api/sales')
def create_sale(data:SaleIn,db=Depends(get_db),user=Depends(require_roles('admin','kasir'))):
    if not data.items: raise HTTPException(400,'Item transaksi kosong')
    subtotal=0; items=[]
    for it in data.items:
        p=db.get(Product,it.product_id)
        if not p or not p.active: raise HTTPException(404,'Produk tidak ditemukan')
        if p.stock<it.qty: raise HTTPException(400,f'Stok {p.name} tidak cukup')
        sub=p.sell_price*it.qty; subtotal+=sub; items.append((p,it,sub))
    total=subtotal-data.discount+data.tax
    if data.payment<total: raise HTTPException(400,'Pembayaran kurang')
    invoice='INV-'+datetime.now().strftime('%Y%m%d%H%M%S')+f'{user.id:02d}'
    s=Sale(invoice_no=invoice,customer_id=data.customer_id,cashier_id=user.id,subtotal=subtotal,discount=data.discount,tax=data.tax,total=total,payment=data.payment,change_amount=data.payment-total)
    db.add(s); db.flush()
    for p,it,sub in items:
        p.stock-=it.qty; db.add(SaleItem(sale_id=s.id,product_id=p.id,qty=it.qty,price=p.sell_price,cost_price=p.buy_price,subtotal=sub)); db.add(StockMovement(product_id=p.id,movement_type='sale',qty=-it.qty,reference=invoice,note='Penjualan'))
    if data.customer_id:
        c=db.get(Customer,data.customer_id); c.points+=int(total//10000)
    db.commit(); audit(db,user,'CREATE','sale',s.id,invoice); return {'id':s.id,'invoice_no':invoice,'total':total,'change':s.change_amount}

@app.get('/api/sales')
def sales(limit:int=100,db=Depends(get_db),user=Depends(current_user)):
    return [{'id':s.id,'invoice_no':s.invoice_no,'date':s.sale_date,'total':s.total,'payment':s.payment,'change':s.change_amount,'status':s.status} for s in db.query(Sale).order_by(desc(Sale.sale_date)).limit(limit).all()]

@app.post('/api/purchases')
def create_purchase(data:PurchaseIn,db=Depends(get_db),user=Depends(require_roles('admin','gudang'))):
    total=0; po='PO-'+datetime.now().strftime('%Y%m%d%H%M%S')
    pch=Purchase(po_no=po,supplier_id=data.supplier_id); db.add(pch); db.flush()
    for it in data.items:
        p=db.get(Product,it.product_id)
        if not p: raise HTTPException(404,'Produk tidak ditemukan')
        sub=it.qty*it.cost_price; total+=sub; p.stock+=it.qty
        db.add(PurchaseItem(purchase_id=pch.id,product_id=p.id,qty=it.qty,cost_price=it.cost_price,subtotal=sub)); db.add(StockMovement(product_id=p.id,movement_type='purchase',qty=it.qty,reference=po,note='Penerimaan pembelian'))
    pch.total=total; db.commit(); audit(db,user,'CREATE','purchase',pch.id,po); return {'id':pch.id,'po_no':po,'total':total}

@app.get('/api/dashboard')
def dashboard(db=Depends(get_db),user=Depends(current_user)):
    now=datetime.now(); start=datetime(now.year,now.month,1)
    if now.month==12: nxt=datetime(now.year+1,1,1)
    else: nxt=datetime(now.year,now.month+1,1)
    revenue=db.query(func.coalesce(func.sum(Sale.total),0)).filter(Sale.sale_date>=start,Sale.sale_date<nxt,Sale.status=='paid').scalar() or 0
    transactions=db.query(func.count(Sale.id)).filter(Sale.sale_date>=start,Sale.sale_date<nxt).scalar() or 0
    products=db.query(func.count(Product.id)).filter(Product.active==True).scalar() or 0
    low=db.query(func.count(Product.id)).filter(Product.active==True,Product.stock<=Product.min_stock).scalar() or 0
    profit=db.query(func.coalesce(func.sum(SaleItem.subtotal-(SaleItem.cost_price*SaleItem.qty)),0)).join(Sale,Sale.id==SaleItem.sale_id).filter(Sale.sale_date>=start,Sale.sale_date<nxt).scalar() or 0
    top=db.query(Product.name,func.sum(SaleItem.qty).label('qty')).join(SaleItem,SaleItem.product_id==Product.id).join(Sale,Sale.id==SaleItem.sale_id).filter(Sale.sale_date>=start,Sale.sale_date<nxt).group_by(Product.id).order_by(desc('qty')).limit(5).all()
    daily=[]
    for i in range((nxt-start).days):
        d=start+timedelta(days=i); e=d+timedelta(days=1)
        val=db.query(func.coalesce(func.sum(Sale.total),0)).filter(Sale.sale_date>=d,Sale.sale_date<e).scalar() or 0
        daily.append({'date':d.strftime('%Y-%m-%d'),'revenue':float(val)})
    alerts=[{'id':p.id,'name':p.name,'stock':p.stock,'min_stock':p.min_stock} for p in db.query(Product).filter(Product.active==True,Product.stock<=Product.min_stock).order_by(Product.stock).all()]
    return {'month':start.strftime('%Y-%m'),'revenue':float(revenue),'profit':float(profit),'transactions':int(transactions),'products':int(products),'low_stock':int(low),'top_products':[{'name':n,'qty':int(q)} for n,q in top],'daily':daily,'alerts':alerts}

@app.get('/api/reports/monthly')
def report_monthly(year:int=Query(...),month:int=Query(...),db=Depends(get_db),user=Depends(current_user)):
    rows=monthly_sales(db,year,month); revenue=sum(x['revenue'] for x in rows); qty=sum(x['qty'] for x in rows)
    return {'year':year,'month':month,'revenue':revenue,'qty':qty,'products':rows}

@app.get('/api/reports/monthly.csv')
def report_csv(year:int,month:int,db=Depends(get_db),user=Depends(current_user)):
    import csv
    rows=monthly_sales(db,year,month); out=BytesIO(); import io; s=io.StringIO(); w=csv.writer(s); w.writerow(['Produk','Qty','Pendapatan']); [w.writerow([r['product'],r['qty'],r['revenue']]) for r in rows]; out.write(s.getvalue().encode()); out.seek(0)
    return StreamingResponse(out,media_type='text/csv',headers={'Content-Disposition':f'attachment; filename=laporan-{year}-{month:02d}.csv'})

@app.get('/api/reports/monthly.pdf')
def report_pdf(year:int,month:int,db=Depends(get_db),user=Depends(current_user)):
    rows=monthly_sales(db,year,month); buf=BytesIO(); c=canvas.Canvas(buf,pagesize=A4); y=800
    c.setFont('Helvetica-Bold',16); c.drawString(45,y,f'Laporan Penjualan SMARTSTOK - {year}-{month:02d}'); y-=35
    c.setFont('Helvetica',10); c.drawString(45,y,f'Total pendapatan: Rp {sum(r["revenue"] for r in rows):,.0f}'); y-=25
    for r in rows:
        c.drawString(45,y,f'{r["product"]} | Qty {r["qty"]} | Rp {r["revenue"]:,.0f}'); y-=18
        if y<50: c.showPage(); y=800
    c.save(); buf.seek(0); return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename=laporan-{year}-{month:02d}.pdf'})

@app.get('/api/ai/forecast/{product_id}')
def forecast(product_id:int,days:int=7,db=Depends(get_db),user=Depends(current_user)):
    if days not in [7,14,30]: raise HTTPException(400,'Hari forecast harus 7, 14, atau 30')
    p=db.get(Product,product_id)
    if not p: raise HTTPException(404,'Produk tidak ditemukan')
    return {'product':p.name,'stock':p.stock,'days':days,**forecast_product(db,product_id,days)}

@app.get('/api/ai/forecasts')
def forecasts(days:int=7,db=Depends(get_db),user=Depends(current_user)):
    return [{'product_id':p.id,'product':p.name,'stock':p.stock,**forecast_product(db,p.id,days)} for p in db.query(Product).filter(Product.active==True).all()]

@app.post('/api/ai/chat')
def chat(data:ChatIn,db=Depends(get_db),user=Depends(current_user)):
    q=data.question.lower(); now=datetime.now(); start=datetime(now.year,now.month,1)
    revenue=db.query(func.coalesce(func.sum(Sale.total),0)).filter(Sale.sale_date>=start).scalar() or 0
    top=db.query(Product.name,func.sum(SaleItem.qty).label('qty')).join(SaleItem,SaleItem.product_id==Product.id).join(Sale,Sale.id==SaleItem.sale_id).filter(Sale.sale_date>=start).group_by(Product.id).order_by(desc('qty')).first()
    low=db.query(Product).filter(Product.active==True,Product.stock<=Product.min_stock).all()
    if 'paling laku' in q or 'terlaris' in q:
        ans=f"Produk terlaris bulan ini adalah {top[0]} dengan {int(top[1])} unit." if top else 'Belum ada data penjualan bulan ini.'
    elif 'pendapatan' in q or 'omzet' in q:
        ans=f"Pendapatan bulan berjalan saat ini sekitar Rp {revenue:,.0f}."
    elif 'stok' in q or 'dibeli' in q or 'restock' in q:
        names=', '.join(f'{p.name} ({p.stock})' for p in low[:10]) or 'Tidak ada produk di bawah stok minimum.'; ans='Produk yang perlu diperhatikan: '+names
    else:
        ans='Saya bisa membantu pertanyaan tentang omzet/pendapatan, produk terlaris, stok minimum, dan restock. Mode chatbot ini read-only dan tidak dapat mengubah database.'
    return {'answer':ans,'source':'SMARTSTOK database (read-only)','role':user.role}

@app.get('/api/anomalies')
def anomalies(db=Depends(get_db),user=Depends(current_user)):
    # Aturan sederhana: transaksi > 3x median 30 hari ditandai.
    since=datetime.now()-timedelta(days=30); vals=[x.total for x in db.query(Sale).filter(Sale.sale_date>=since).all()]
    if not vals: return []
    import statistics
    med=statistics.median(vals); rows=db.query(Sale).filter(Sale.sale_date>=since,Sale.total>med*3).order_by(desc(Sale.total)).all()
    return [{'invoice':x.invoice_no,'date':x.sale_date,'total':x.total,'reason':'Total transaksi > 3x median 30 hari'} for x in rows]
