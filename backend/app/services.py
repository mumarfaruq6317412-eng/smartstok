from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import SaleItem, Sale, Product, StockMovement
import pandas as pd

def monthly_sales(db:Session, year:int, month:int):
    start=datetime(year,month,1)
    end=datetime(year+1,1,1) if month==12 else datetime(year,month+1,1)
    rows=db.query(SaleItem.product_id, Product.name, func.sum(SaleItem.qty).label('qty'), func.sum(SaleItem.subtotal).label('revenue')).join(Sale, Sale.id==SaleItem.sale_id).join(Product,Product.id==SaleItem.product_id).filter(Sale.sale_date>=start,Sale.sale_date<end,Sale.status=='paid').group_by(SaleItem.product_id,Product.name).all()
    return [{'product_id':r.product_id,'product':r.name,'qty':int(r.qty or 0),'revenue':float(r.revenue or 0)} for r in rows]

def forecast_product(db:Session, product_id:int, days:int=7):
    since=datetime.utcnow()-timedelta(days=90)
    rows=db.query(func.date(Sale.sale_date).label('d'),func.sum(SaleItem.qty).label('q')).join(SaleItem,Sale.id==SaleItem.sale_id).filter(SaleItem.product_id==product_id,Sale.sale_date>=since,Sale.status=='paid').group_by(func.date(Sale.sale_date)).order_by(func.date(Sale.sale_date)).all()
    if not rows: return {'average_daily':0,'forecast':0,'restock':0,'method':'moving_average'}
    vals=[float(r.q) for r in rows]
    avg=sum(vals[-7:])/min(7,len(vals))
    p=db.get(Product,product_id)
    forecast=round(avg*days)
    safety=round(avg*3)
    restock=max(0,forecast+safety-(p.stock if p else 0))
    return {'average_daily':round(avg,2),'forecast':forecast,'safety_stock':safety,'restock':restock,'method':'moving_average'}
