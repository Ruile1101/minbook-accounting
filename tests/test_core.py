import os, tempfile, sqlite3
from app import create_app, db
from app.models import CashAccount, Transaction, ShopPOSImport
def app_client(monkeypatch):
    path=tempfile.mktemp(suffix='.db'); monkeypatch.setenv('ACCOUNTING_DATABASE_URL','sqlite:///'+path); app=create_app(); return app,app.test_client()
def test_income_and_balance(monkeypatch):
    app,c=app_client(monkeypatch)
    with app.app_context(): db.session.add(CashAccount(name='Cash',balance=0));db.session.commit()
    r=c.post('/income/add',data={'date':'2026-09-11','payment_method':'Cash','item_category[]':['Printing'],'item_description[]':['x'],'quantity[]':['2'],'unit_price[]':['10'],'discount[]':['0']});assert r.status_code==302
    with app.app_context(): assert str(CashAccount.query.filter_by(name='Cash').first().balance)=='20.00'
def test_shoppos_duplicate_guard(monkeypatch):
    app,c=app_client(monkeypatch); pos=tempfile.mktemp(suffix='.db'); con=sqlite3.connect(pos);con.executescript("CREATE TABLE sale (id integer,amount real,date text,payment_method text,customer_name text,discount real,deposit real);CREATE TABLE sale_item (id integer,sale_id integer,category text,description text,quantity integer,unit_price real,line_total real);INSERT INTO sale VALUES(1,20,'2026-09-11','Cash','Lee',0,0);INSERT INTO sale_item VALUES(1,1,'Printing','Copies',10,2,20);");con.commit();con.close();app.config['SHOPPOS_DATABASE_URL']='sqlite:///'+pos
    with app.app_context(): db.session.add(CashAccount(name='Cash',balance=0));db.session.commit()
    c.post('/shoppos',data={'action':'sync'});c.post('/shoppos',data={'action':'sync'})
    with app.app_context(): assert ShopPOSImport.query.count()==1 and Transaction.query.count()==1
