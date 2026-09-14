from datetime import datetime
from app import db


class Customer(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(120), nullable=False); phone=db.Column(db.String(50)); email=db.Column(db.String(120)); address=db.Column(db.Text); notes=db.Column(db.Text)
class Supplier(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(120), nullable=False); phone=db.Column(db.String(50)); email=db.Column(db.String(120)); address=db.Column(db.Text); notes=db.Column(db.Text)
class ProductService(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(120), nullable=False); category=db.Column(db.String(80)); price=db.Column(db.Numeric(12,2), default=0)
class CashAccount(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(40), unique=True, nullable=False); balance=db.Column(db.Numeric(12,2), default=0)
class BusinessSetting(db.Model):
    id=db.Column(db.Integer, primary_key=True); business_name=db.Column(db.String(120), default='Min Book Shop'); address=db.Column(db.Text); phone=db.Column(db.String(50)); email=db.Column(db.String(120)); registration_number=db.Column(db.String(100)); sst_status=db.Column(db.String(30), default='Not Registered'); einvoice_enabled=db.Column(db.Boolean, default=False)
class Transaction(db.Model):
    id=db.Column(db.Integer, primary_key=True); date=db.Column(db.Date, nullable=False); type=db.Column(db.String(20), nullable=False); category=db.Column(db.String(80)); description=db.Column(db.Text); payment_method=db.Column(db.String(40), default='Cash'); total=db.Column(db.Numeric(12,2), nullable=False, default=0); paid=db.Column(db.Boolean, default=True); customer_id=db.Column(db.Integer, db.ForeignKey('customer.id')); supplier_id=db.Column(db.Integer, db.ForeignKey('supplier.id')); created_at=db.Column(db.DateTime, default=datetime.utcnow)
    customer=db.relationship('Customer', backref='transactions'); supplier=db.relationship('Supplier', backref='transactions'); items=db.relationship('TransactionItem', cascade='all, delete-orphan', backref='transaction')
class TransactionItem(db.Model):
    id=db.Column(db.Integer, primary_key=True); transaction_id=db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False); category=db.Column(db.String(80)); description=db.Column(db.String(250)); quantity=db.Column(db.Numeric(12,2), default=1); unit_price=db.Column(db.Numeric(12,2), default=0); discount=db.Column(db.Numeric(12,2), default=0); total=db.Column(db.Numeric(12,2), default=0)
class AccountTransaction(db.Model):
    id=db.Column(db.Integer, primary_key=True); date=db.Column(db.Date, nullable=False,index=True); account_name=db.Column(db.String(40),nullable=False,index=True); amount=db.Column(db.Numeric(12,2),nullable=False); direction=db.Column(db.String(3),nullable=False); transaction_id=db.Column(db.Integer,db.ForeignKey('transaction.id')); memo=db.Column(db.String(250)); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class ShopPOSImport(db.Model):
    id=db.Column(db.Integer,primary_key=True); source_system=db.Column(db.String(30),nullable=False,default='shoppos'); source_id=db.Column(db.String(80),nullable=False); transaction_id=db.Column(db.Integer,db.ForeignKey('transaction.id'),nullable=False); imported_at=db.Column(db.DateTime,default=datetime.utcnow); source_date=db.Column(db.Date); source_total=db.Column(db.Numeric(12,2)); transaction=db.relationship('Transaction',backref=db.backref('shoppos_import',uselist=False)); __table_args__=(db.UniqueConstraint('source_system','source_id',name='uq_shoppos_source'),)
class ShopPOSImportItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); import_id=db.Column(db.Integer,db.ForeignKey('shop_pos_import.id'),nullable=False); source_item_id=db.Column(db.String(80)); category=db.Column(db.String(80)); description=db.Column(db.Text); quantity=db.Column(db.Numeric(12,2)); unit_price=db.Column(db.Numeric(12,2)); total=db.Column(db.Numeric(12,2)); imported_sale=db.relationship('ShopPOSImport',backref=db.backref('imported_items',cascade='all, delete-orphan'))
class ShopPOSSyncLog(db.Model):
    id=db.Column(db.Integer,primary_key=True); started_at=db.Column(db.DateTime,default=datetime.utcnow); finished_at=db.Column(db.DateTime); status=db.Column(db.String(30)); found=db.Column(db.Integer,default=0); imported=db.Column(db.Integer,default=0); skipped=db.Column(db.Integer,default=0); failed=db.Column(db.Integer,default=0); message=db.Column(db.Text)
