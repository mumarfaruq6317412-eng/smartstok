from datetime import date
from pydantic import BaseModel, Field

class LoginIn(BaseModel): username:str; password:str
class ProductIn(BaseModel):
    sku:str; name:str; category_id:int|None=None; supplier_id:int|None=None; buy_price:float=0; sell_price:float=0; stock:int=0; min_stock:int=5; unit:str='pcs'; expiry_date:date|None=None
class CustomerIn(BaseModel): name:str; phone:str=''; address:str=''
class SupplierIn(BaseModel): name:str; phone:str=''; address:str=''
class CategoryIn(BaseModel): name:str
class SaleItemIn(BaseModel): product_id:int; qty:int=Field(gt=0)
class SaleIn(BaseModel): customer_id:int|None=None; items:list[SaleItemIn]; discount:float=0; tax:float=0; payment:float=0
class PurchaseItemIn(BaseModel): product_id:int; qty:int=Field(gt=0); cost_price:float=Field(ge=0)
class PurchaseIn(BaseModel): supplier_id:int; items:list[PurchaseItemIn]
class StockAdjustIn(BaseModel): product_id:int; qty:int; note:str='Penyesuaian stok'
class ChatIn(BaseModel): question:str
