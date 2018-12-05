from flask import Flask, redirect, url_for, session, request, jsonify,render_template
from flask_oauthlib.client import OAuth
import MySQLdb
import sqlite3
from pypika import Query, Table, Field
import re

app = Flask(__name__)
app.config['GOOGLE_ID'] = "450616066868-bbfdvhu2b96aj59v32b7flljthskl4et.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "jzMkCkgwUbW5RoXxKlQ3pyPu"

app.debug = True
app.secret_key = 'development'

oauth = OAuth(app)
Udata = {}
email = ""
google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@app.route('/')
def index():
    return render_template("index.html")
#    if 'google_token' in session:
#        me = google.get('userinfo')
#        Udata = me.data
#        return redirect(url_for('login'))
#    return redirect(url_for('login'))

#@app.route('/login/check')
#def LoginCheck():
#    con = sqlite3.connect('data.sqlite3')
#    cur = con.execute("SELECT email from Users")
#    for rows in cur:
#        if rows[0] is email:
#            return redirect(url_for('Dashboard'))
#    return "Invalid"

@app.route('/dashboard')
def Dashboard():
    if 'google_token' in session:
        return render_template('dashboard.html',access=session['access'],name=session['user'])
    else:
        return redirect(url_for('login'))

@app.route('/login')
def login():
    #return google.authorize(callback=url_for('authorized', _external=True))
    return google.authorize(callback=url_for('authorized', _external=True),prompt='consent')

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    session.pop('user', None)
    session.pop('access', None)
    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    Udata = me.data
    email = Udata['email']
    con = sqlite3.connect('data.sqlite3')
    cur = con.execute("SELECT * from Users")
    for rows in cur:
        if rows[0] == email:
            session['user'] = rows[2]
            session['access'] = rows[1]
            con.close()
            return redirect('/dashboard')
            
    session.pop('google_token', None)
    return redirect('/invalid')

@app.route('/invalid')
def Invalid():
    return render_template('invalid.html')
    
    #return redirect(url_for('LoginCheck'))


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/dashboard/display')
def Display():
    return render_template("display.html")

@app.route('/dashboard/display2' , methods = ['GET' , 'POST'])
def Display2():
    if 'user' not in session:
        return redirect('/logout')
    else:
        print ("Logged in")
    if request.method == "POST":
        table = request.form['table']
        query = request.form['query']
        StartDate = ""
        EndDate = ""
        con = MySQLdb.connect("54.254.180.97","moksh","moksh@moglix@123","analytics_temp")
        cur = con.cursor()
        if "all orders of " in query.lower():
            tmp = query.split("all orders of")
            date = tmp[1].strip()
            year = None
            month = None
            day = None
            LastDay = 0
            print (date)
            if re.match(r'(2+0+\d+\d)',date):
                m = re.match(r'(2+0+\d+\d)',date)
                print ("in year")
                year = m.group(0)
                if re.match(r'(2+0+\d+\d+.\d+\d)',date):
                    print ("in month")
                    m = re.match(r'(2+0+\d+\d+.\d+\d)',date)
                    tmp = m.group(0)
                    month = tmp[5:7]
                    print (month)
                    if month in ["01","03","05","07","08","10","12"]:
                        LastDay = 31
                    elif month == "02":
                        if (int(year) % 4) == 0:
                            if (int(year) % 100) == 0:
                                if (int(year) % 400) == 0:
                                    LastDay = 29
                                else:
                                    LastDay = 28
                            else:
                                LastDay = 29
                        else:
                            LastDay = 28
                    else:
                        LastDay = 30
                    if re.match(r'(2+0+\d+\d+.+\d+\d+.+\d+\d)',date):
                        print("in day")
                        m = re.match(r'(2+0+\d+\d+.+\d+\d+.+\d+\d)',date)
                        tmp = m.group(0)
                        day = tmp[8:10]
                        StartDate = year+"-"+month+"-"+day+" 00:00:00"
                        EndDate = year+"-"+month+"-"+day+" 23:59:59"
                    else:
                        StartDate = year+"-"+month+"-"+"01"+" 00:00:00"
                        EndDate = year+"-"+month+"-"+str(LastDay)+" 23:59:59"
                else:
                    StartDate = year+"-"+"01"+"-"+"01"+" 00:00:00"
                    EndDate = year+"-"+"12"+"-"+"31"+" 23:59:59"
            sql = "select * from {} where created_at >= %s AND created_at <= %s".format(table)
            print (sql)
            print (StartDate+" "+EndDate)
            cur.execute(sql,(StartDate,EndDate))
            field_names = [i[0] for i in cur.description]
            data = cur.fetchall()
            con.close()
            try:
                return render_template("display.html",data = data,field_names = field_names)
            except:
                return render_template("display.html")
        elif "details of" in query.lower():
            cur = con.cursor()
            tmp = query.split("details of")
            where = str(tmp[1].strip())
            where = where.split(" ")
            print (where[0])
            print (where[1])
            sql = 'SELECT * from {} where {} = {}'.format(where[0],where[1])
            print (sql)
            cur.execute(sql,())
            field_names = [i[0] for i in cur.description]
            data = cur.fetchall()
            con.close()
            return render_template("display.html" , data = data , field_names = field_names )
        elif "of" in query.lower():
            cur = con.cursor()
            tmp = query.split("of")
            m = re.match(r'(2+0+\d+\d+.+\d+\d+.+\d+\d)',tmp[1].strip())
            if m is not None:
                if m.group(1):
                    print ("SPECIFIC DATE")
                    StartDate = m.group(0)+" 00:00:00"
                    EndDate = m.group(0)+" 23:59:59"
                    print (StartDate+" "+EndDate)
                    sql = 'select * from {} where created_at >= "{}" AND created_at <= "{}" '.format(table,StartDate,EndDate)
                    cur.execute(sql)
                    print ("Query executed: ",sql)
                    con.close()
                    data = cur.fetchall()
                    field_names = [i[0] for i in cur.description]
                    return render_template("display.html" , data = data , field_names = field_names)
            cols = tmp[0].strip()
            cols = cols.replace(',','","')
            where = str(tmp[1].strip())
            where = where.split(" ")
            print (where[0])
            print (where[1])
            print (cols)
            where[1] = where[1]
            sql = 'SELECT {} from {} where {} = {}'.format(cols,table,where[0],where[1])
            print (sql)
            cur.execute(sql)
            field_names = [i[0] for i in cursor.description]
            con.close()
            data = cur.fetchall()
            return render_template("display.html" , data = data , field_names = field_names)
    else:
        return render_template("display.html")
    """ DISP = ""
        if "display" in query.lower():
            DISP = "display"
        elif "show" in query.lower():
            DISP = "show"
        elif "select" in query.lower():
            DISP = "select"
        elif "get" in query.lower():
            DISP = "get"
        elif "view" in query.lower():
            DISP = "view"
        if DISP in query.lower():
            if " of " in query.lower():
                query = query.split("of")
                cols = query[0].strip()
                cols = cols.replace(DISP+" ","")
                cols = cols.replace(",",'","')
                con = sqlite3.connect('Main.db')
                Name = query[1].strip()
                Employee = Table('Employee')
                q = Query.from_('Employee').select(cols).where(Employee.Name == Name)
                cur = con.execute(str(q))
                print (str(q))
                data = cur.fetchall()
                print (data)
                return render_template("display.html" , data = data, Query = str (q))
                con.close()
            elif " in " in query.lower():
                WHERE = "in"
            elif " from " in query.lower():
                WHERE = "from"
            else:
                cols = query.replace(DISP+" ","")
                cols = cols.replace(",",'","')
                con = sqlite3.connect('Main.db')
                Employee = Table('Employee')
                q = Query.from_('Employee').select(cols)
                cur = con.execute(str(q))
                print (str(q))
                data = cur.fetchall()
                print (data)
                return render_template("display.html" , data = data)
                con.close()
            try:
                if WHERE in query.lower():
                    query = query.split(WHERE)
                    cols = query[0].strip()
                    cols = cols.replace(DISP+" ","")
                    cols = cols.replace(",",'","')
                    con = sqlite3.connect('Main.db')
                    Dept = query[1].strip()
                    Employee = Table('Employee')
                    q = Query.from_('Employee').select(cols).where(Employee.Department == Dept)
                    cur = con.execute(str(q))
                    print (str(q))
                    data = cur.fetchall()
                    print (data)
                    return render_template("display.html" , data = data, Query = str (q))
                    con.close()
            except:
                print ("ok")
            if " where salary >" in query.lower():
                gt = "where salary >"
            elif " where salary is greater than" in query.lower():
                gt = "where salary is greater than"
            try:
                if gt in query.lower():
                    query = query.split(gt)
                    cols = query[0].strip()
                    cols = cols.replace(DISP+" ","")
                    cols = cols.replace(",",'","')
                    con = sqlite3.connect('Main.db')
                    Sal = int(query[1].strip())
                    Employee = Table('Employee')
                    q = Query.from_('Employee').select(cols).where(Employee.salary > Sal)
                    cur = con.execute(str(q))
                    print (str(q))
                    data = cur.fetchall()
                    print (data)
                    return render_template("display.html" , data = data , Query = str (q))
                    con.close()
            except:
                print ("ok")
            if " where salary <" in query.lower():
                lt = "where salary <"
            elif " where salary is less than" in query.lower():
                lt = "where salary is less than"
            try:
                if lt in query.lower():
                    query = query.split(lt)
                    cols = query[0].strip()
                    cols = cols.replace(DISP+" ","")
                    cols = cols.replace(",",'","')
                    con = sqlite3.connect('Main.db')
                    Sal = int(query[1].strip())
                    Employee = Table('Employee')
                    q = Query.from_('Employee').select(cols).where(Employee.salary < Sal)
                    cur = con.execute(str(q))
                    print (str(q))
                    data = cur.fetchall()
                    print (data)
                    return render_template("display.html" , data = data , Query = str (q))
                    con.close()
            except:
                print ("ok")
            if " where salary =" in query.lower():
                eq = "where salary ="
            elif " where salary is equal to" in query.lower():
                eq = "where salary is equal to"
            try:
                if eq in query.lower():
                    query = query.split("where salary >")
                    cols = query[0].strip()
                    cols = cols.replace(DISP+" ","")
                    cols = cols.replace(",",'","')
                    con = sqlite3.connect('Main.db')
                    Sal = int(query[1].strip())
                    Employee = Table('Employee')
                    q = Query.from_('Employee').select(cols).where(Employee.salary == Sal)
                    cur = con.execute(str(q))
                    print (str(q))
                    data = cur.fetchall()
                    print (data)
                    return render_template("display.html" , data = data)
                    con.close()
            except:
                print (".")
            """
if __name__ == '__main__':
    app.run(debug=True)