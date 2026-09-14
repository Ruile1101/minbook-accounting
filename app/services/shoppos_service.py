"""Read-only adapter for the verified ShopPOS Mini Sale/SaleItem schema."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from app import db
from app.models import Transaction, TransactionItem, ShopPOSImport, ShopPOSImportItem, ShopPOSSyncLog, CashAccount, Customer
PAYMENT_MAP={'cash':'Cash','bank':'Bank','qr':'DuitNow / QR','duitnow':'DuitNow / QR','card':'Card'}
def decimal(v): return Decimal(str(v or 0)).quantize(Decimal('.01'))
def engine_for(url):
    if not url: raise RuntimeError('SHOPPOS_DATABASE_URL is not configured.')
    return create_engine(url, pool_pre_ping=True)
def test_connection(url):
    with engine_for(url).connect() as c:
        c.execute(text('SELECT 1')); c.execute(text('SELECT id, amount, date, payment_method, customer_name, discount, deposit FROM sale LIMIT 1'))
    return True
def sync(url):
    log=ShopPOSSyncLog(status='running');db.session.add(log);db.session.commit()
    try:
        with engine_for(url).connect() as c:
            sales=c.execute(text('SELECT id, amount, date, payment_method, customer_name, discount, deposit FROM sale ORDER BY id')).mappings().all(); log.found=len(sales)
            for sale in sales:
                sid=str(sale['id'])
                if ShopPOSImport.query.filter_by(source_system='shoppos',source_id=sid).first(): log.skipped+=1;continue
                items=c.execute(text('SELECT id, category, description, quantity, unit_price, line_total FROM sale_item WHERE sale_id=:id ORDER BY id'),{'id':sale['id']}).mappings().all(); method=PAYMENT_MAP.get((sale['payment_method'] or '').lower(),'Other'); customer=None
                if sale['customer_name']: customer=Customer.query.filter_by(name=sale['customer_name']).first() or Customer(name=sale['customer_name']);db.session.add(customer);db.session.flush()
                sale_date=sale['date'] if hasattr(sale['date'],'year') else datetime.strptime(str(sale['date']),'%Y-%m-%d').date(); total=decimal(sale['amount'])-decimal(sale['discount']); tx=Transaction(date=sale_date,type='income',category=(items[0]['category'] if items else 'Other'),description=f"ShopPOS sale #{sid}",payment_method=method,total=total,paid=True,customer=customer)
                db.session.add(tx);db.session.flush()
                for i in items: db.session.add(TransactionItem(transaction=tx,category=i['category'],description=i['description'],quantity=decimal(i['quantity']),unit_price=decimal(i['unit_price']),total=decimal(i['line_total'])))
                imp=ShopPOSImport(source_system='shoppos',source_id=sid,transaction=tx,source_date=sale_date,source_total=total);db.session.add(imp);db.session.flush()
                for i in items: db.session.add(ShopPOSImportItem(imported_sale=imp,source_item_id=str(i['id']),category=i['category'],description=i['description'],quantity=decimal(i['quantity']),unit_price=decimal(i['unit_price']),total=decimal(i['line_total'])))
                account=CashAccount.query.filter_by(name=method).first()
                if account: account.balance=decimal(account.balance)+total
                log.imported+=1
            log.status='success';log.finished_at=datetime.utcnow();db.session.commit();return log
    except Exception as exc:
        db.session.rollback();log.status='failed';log.finished_at=datetime.utcnow();log.message=str(exc)[:500];db.session.add(log);db.session.commit();raise RuntimeError('Could not connect to ShopPOS. Check its URL and that the database is reachable.')
