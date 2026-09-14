from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from io import BytesIO
import sqlite3
from sqlalchemy import func
from app import db
from app.models import Transaction, TransactionItem, Customer, Supplier, CashAccount, BusinessSetting, ShopPOSImport, ShopPOSSyncLog
main=Blueprint('main',__name__)
INCOME=['Printing','Photocopy','Stationery','Binding','Laminating','Sticker','Rubber Stamp','Design','Other']; PURCHASE=['Printing Materials','Stationery Stock','Office Supplies','Equipment','Other']; EXPENSE=['Rent','Electricity','Water','Internet','Telephone','Transport','Repair & Maintenance','Advertising','Bank Charges','Office Expenses','Salary','Other']; PAY=['Cash','Bank','DuitNow / QR','Card','Other','Credit']
def money(v): return Decimal(str(v or 0)).quantize(Decimal('.01'))
@main.app_template_filter('rm')
def rm(v): return 'RM {:,.2f}'.format(float(v or 0))
def cash_balances(): return {x.name:money(x.balance) for x in CashAccount.query.all()}
def adjust(tx, undo=False):
    if tx.paid and tx.payment_method in ['Cash','Bank','DuitNow / QR','Card']:
        a=CashAccount.query.filter_by(name=tx.payment_method).first(); sign=1 if tx.type=='income' else -1
        if undo: sign=-sign
        if a:a.balance=money(a.balance)+sign*money(tx.total)
@main.route('/')
def dashboard():
    month=request.args.get('month',date.today().strftime('%Y-%m')); tx=Transaction.query.filter(func.strftime('%Y-%m',Transaction.date)==month).all(); s={k:sum((money(x.total) for x in tx if x.type==k),Decimal()) for k in ['income','purchase','expense']}; alltx=Transaction.query.all(); out=sum((money(x.total) for x in alltx if x.type=='income' and not x.paid),Decimal()); owing=sum((money(x.total) for x in alltx if x.type=='purchase' and not x.paid),Decimal())
    return render_template('dashboard.html',month=month,stats=s,profit=s['income']-s['purchase']-s['expense'],balances=cash_balances(),outstanding=out,owing=owing,recent=Transaction.query.order_by(Transaction.date.desc(),Transaction.id.desc()).limit(8).all())
@main.route('/income/add',methods=['GET','POST'])
@main.route('/purchases/add',methods=['GET','POST'])
def add_transaction():
    typ='income' if request.path.startswith('/income') else 'purchase'; categories=INCOME if typ=='income' else PURCHASE; people=Customer.query.all() if typ=='income' else Supplier.query.all()
    if request.method=='POST':
        try:
            items=[]
            for c,d,q,p,disc in zip(request.form.getlist('item_category[]'),request.form.getlist('item_description[]'),request.form.getlist('quantity[]'),request.form.getlist('unit_price[]'),request.form.getlist('discount[]')):
                total=money(q)*money(p)-money(disc)
                if total<0:raise ValueError
                items.append(TransactionItem(category=c,description=d,quantity=money(q),unit_price=money(p),discount=money(disc),total=total))
            if not items:raise ValueError
            pay=request.form['payment_method'];tx=Transaction(date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),type=typ,category=items[0].category,description=request.form.get('description'),payment_method=pay,total=sum((x.total for x in items),Decimal()),paid=pay!='Credit',items=items)
            if typ=='income':tx.customer_id=request.form.get('person_id') or None
            else:tx.supplier_id=request.form.get('person_id') or None
            db.session.add(tx);adjust(tx);db.session.commit();flash(f'{typ.title()} saved.','success');return redirect(url_for('main.transactions'))
        except (ValueError,InvalidOperation):flash('Please enter valid, positive amounts.','error')
    return render_template('transaction_form.html',typ=typ,categories=categories,people=people,payments=PAY)
@main.route('/expenses/add',methods=['GET','POST'])
def add_expense():
    if request.method=='POST':
        try:
            pay=request.form['payment_method'];tx=Transaction(date=datetime.strptime(request.form['date'],'%Y-%m-%d').date(),type='expense',category=request.form['category'],description=request.form.get('description'),payment_method=pay,total=money(request.form['amount']),paid=pay!='Credit')
            if tx.total<=0:raise ValueError
            db.session.add(tx);adjust(tx);db.session.commit();flash('Expense saved.','success');return redirect(url_for('main.transactions'))
        except (ValueError,InvalidOperation):flash('Enter a valid positive amount.','error')
    return render_template('expense_form.html',categories=EXPENSE,payments=PAY)
@main.route('/transactions')
@main.route('/income/history')
@main.route('/purchases/history')
@main.route('/expenses/history')
def transactions():
    q=Transaction.query; term=request.args.get('q','');typ=request.args.get('type','')
    if request.path.startswith('/income/'): typ='income'
    if request.path.startswith('/purchases/'): typ='purchase'
    if request.path.startswith('/expenses/'): typ='expense'
    if term:q=q.filter((Transaction.description.ilike('%'+term+'%'))|(Transaction.category.ilike('%'+term+'%')))
    if typ:q=q.filter_by(type=typ)
    return render_template('transactions.html',transactions=q.order_by(Transaction.date.desc(),Transaction.id.desc()).all())
@main.route('/transactions/<int:id>')
def transaction_detail(id):return render_template('transaction_detail.html',tx=db.get_or_404(Transaction,id))
@main.route('/transactions/<int:id>/delete',methods=['POST'])
def delete_transaction(id):
    tx=db.get_or_404(Transaction,id);adjust(tx,True);db.session.delete(tx);db.session.commit();flash('Transaction deleted.','success');return redirect(url_for('main.transactions'))
@main.route('/<kind>',methods=['GET','POST'])
def contacts(kind):
    if kind not in ('customers','suppliers'):return redirect(url_for('main.dashboard'))
    M=Customer if kind=='customers' else Supplier
    if request.method=='POST':db.session.add(M(name=request.form['name'],phone=request.form.get('phone'),email=request.form.get('email'),address=request.form.get('address'),notes=request.form.get('notes')));db.session.commit();flash('Saved.','success');return redirect(request.url)
    term=request.args.get('q','');return render_template('contacts.html',kind=kind,people=M.query.filter(M.name.ilike('%'+term+'%')).all())
@main.route('/<kind>/<int:id>/delete',methods=['POST'])
def delete_contact(kind,id):
    M=Customer if kind=='customers' else Supplier;p=db.get_or_404(M,id)
    if p.transactions:flash('This contact has transactions and cannot be deleted.','error')
    else:db.session.delete(p);db.session.commit();flash('Contact deleted.','success')
    return redirect(url_for('main.contacts',kind=kind))
@main.route('/cash-bank',methods=['GET','POST'])
def cash_bank():
    if request.method=='POST':
        try:
            a=CashAccount.query.filter_by(name=request.form['from_account']).first();b=CashAccount.query.filter_by(name=request.form['to_account']).first();amt=money(request.form['amount']);assert a and b and a!=b and amt>0;a.balance-=amt;b.balance+=amt;db.session.commit();flash('Transfer recorded.','success')
        except:flash('Check transfer details.','error')
        return redirect(request.url)
    return render_template('cash_bank.html',accounts=CashAccount.query.all())
@main.route('/reports/<report>')
def reports(report):
    tx=Transaction.query.order_by(Transaction.date.desc()).all();data={k:sum((money(x.total) for x in tx if x.type==k),Decimal()) for k in ['income','purchase','expense']}; grouped={}
    for x in tx:grouped[x.category]=grouped.get(x.category,Decimal())+money(x.total)
    return render_template('report.html',report=report.replace('-',' ').title(),tx=tx,data=data,grouped=grouped,balances=cash_balances())
@main.route('/settings',methods=['GET','POST'])
def settings():
    s=BusinessSetting.query.first() or BusinessSetting()
    if request.method=='POST':
        for x in ['business_name','address','phone','email','registration_number','sst_status']:setattr(s,x,request.form.get(x))
        s.einvoice_enabled='einvoice_enabled' in request.form;db.session.add(s);db.session.commit();flash('Settings saved.','success');return redirect(request.url)
    return render_template('settings.html',s=s)
@main.route('/shoppos',methods=['GET','POST'])
def shoppos():
    from app.services.shoppos_service import test_connection, sync
    url=current_app.config['SHOPPOS_DATABASE_URL']
    if request.method=='POST':
        try:
            if request.form.get('action')=='test': test_connection(url);flash('ShopPOS connected. Its data is read-only from this application.','success')
            else:
                result=sync(url);flash(f'Sync complete: {result.imported} imported, {result.skipped} already imported, {result.failed} failed.','success')
        except RuntimeError as e: flash(str(e),'error')
        except Exception: flash('ShopPOS could not be reached. Check the configured connection.','error')
        return redirect(url_for('main.shoppos'))
    logs=ShopPOSSyncLog.query.order_by(ShopPOSSyncLog.started_at.desc()).limit(10).all()
    return render_template('shoppos.html',configured=bool(url), imports=ShopPOSImport.query.count(), logs=logs)
@main.route('/settings/backup')
def backup():
    uri=current_app.config['SQLALCHEMY_DATABASE_URI']
    if not uri.startswith('sqlite:///'):
        flash('Database download is available for local SQLite only. Use your production database backup tool.','error');return redirect(url_for('main.settings'))
    path=uri.replace('sqlite:///','',1)
    try:
        with open(path,'rb') as f: return send_file(BytesIO(f.read()),as_attachment=True,download_name='minbook-accounting-backup.db',mimetype='application/octet-stream')
    except OSError: flash('The accounting database file is not available yet.','error');return redirect(url_for('main.settings'))
@main.route('/health')
def health(): return {'status':'ok','database':'available','shoppos_configured':bool(current_app.config['SHOPPOS_DATABASE_URL'])}
