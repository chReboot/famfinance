from flask import Flask,render_template,request,redirect
import sqlite3,hashlib,pandas as pd,os
app=Flask(__name__)
DB='/data/finance.db'
os.makedirs('/data',exist_ok=True)
con=sqlite3.connect(DB)
con.execute('create table if not exists transactions(hash text primary key,date text,payee text,amount real,category text)')
con.close()

def cat(payee):
 p=(payee or '').upper()
 if 'REWE' in p or 'EDEKA' in p: return 'Lebensmittel'
 if 'AMAZON' in p: return 'Shopping'
 return 'Unkategorisiert'

@app.route('/',methods=['GET','POST'])
def idx():
 if request.method=='POST':
  f=request.files['file']
  df=pd.read_csv(f,sep=';',encoding='cp1252')
  con=sqlite3.connect(DB)
  new=0
  for _,r in df.iterrows():
   payee=str(r.get('Empfänger/Auftraggeber Name',''))
   amount=str(r.get('Soll/Haben',''))
   date=str(r.get('Buchungstag',''))
   h=hashlib.sha256(f'{date}|{payee}|{amount}'.encode()).hexdigest()
   try:
    con.execute('insert into transactions values(?,?,?,?,?)',(h,date,payee,float(str(amount).replace(',','.')),cat(payee)))
    new+=1
   except: pass
  con.commit(); con.close()
  return redirect('/')
 con=sqlite3.connect(DB)
 rows=con.execute('select count(*),coalesce(sum(amount),0) from transactions').fetchone(); con.close()
 return render_template('index.html',count=rows[0],summe=rows[1])
app.run(host='0.0.0.0',port=5000)
