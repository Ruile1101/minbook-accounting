from datetime import date, timedelta
from decimal import Decimal
from app import db
from app.models import CashAccount, Customer, Supplier, Transaction, BusinessSetting

def seed():
    if Transaction.query.first(): return
    db.session.add_all([CashAccount(name=x, balance=Decimal(v)) for x,v in [('Cash','850'),('Bank','2150'),('DuitNow / QR','320'),('Card','180')]])
    c=Customer(name='Demo: SJK(C) Harmony',phone='03-5555 0101'); s=Supplier(name='Demo: Paper World'); db.session.add_all([c,s]);db.session.flush(); today=date.today()
    for i,args in enumerate([('income','Printing','School flyers','Cash',240,c,None),('income','Binding','Thesis binding','DuitNow / QR',75,c,None),('purchase','Printing Materials','A4 paper stock','Bank',320,None,s),('expense','Electricity','TNB bill','Bank',180,None,None),('expense','Rent','Shop rental','Bank',900,None,None)]):
        typ,cat,desc,pay,total,cu,su=args;db.session.add(Transaction(date=today-timedelta(days=i*2),type=typ,category=cat,description=desc,payment_method=pay,total=Decimal(total),customer=cu,supplier=su))
    db.session.add(BusinessSetting());db.session.commit()
