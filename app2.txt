from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
import sqlite3


app = Flask(__name__)
app.config['GOOGLE_ID'] = "450616066868-bbfdvhu2b96aj59v32b7flljthskl4et.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "jzMkCkgwUbW5RoXxKlQ3pyPu"
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)
Udata = {}

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
    if 'google_token' in session:
        me = google.get('userinfo')
        return jsonify({"data": me.data})
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('google_token', None)
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
    Udata = jsonify(me.data)
    return redirect(url_for('login/check')

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/login/check')
def logincheck():
    con = sqlite3.connect('data.sqlite3')
    cur = con.execute("SELECT email from Users")
    chk = 0
    for row in cur:
        if Udata['email'] == row[0]:
            chk = 1
        con.close()
        return redirect(url_for('dashboard')
    return "Invalid"

@app.route('/dashboard')
def Dashboard():
    return render_template('dashboard.html')
if __name__ == '__main__':
    app.run()