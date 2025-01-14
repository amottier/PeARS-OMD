# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Import flask dependencies
from flask import Blueprint, request, render_template, send_from_directory, make_response
from flask import current_app
from flask_cors import cross_origin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField

# Import the database object from the main app module
from app import app
from app.api.models import Urls
from app.search import score_pages

# Import matrix manipulation modules
import numpy as np
from scipy import sparse

# Import utilities
import re
import requests
import logging
from os.path import dirname, join, realpath, isfile
from flask import jsonify, Response
from app.utils import init_podsum
from app import LOCAL_RUN

LOG = logging.getLogger(__name__)

# Define the blueprint:
search = Blueprint('search', __name__, url_prefix='')

dir_path = dirname(dirname(dirname(realpath(__file__))))
pod_dir = join(dir_path,'app','static','pods')

class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Submit')

@search.route('/user', methods=['POST','GET'])
@cross_origin()
def user():
    access_token = request.headers.get('Token')
    if not access_token:     
        access_token = request.cookies.get('OMD_SESSION_ID')  
    LOG.info(access_token)    
    if not access_token:
        return render_template('search/anonymous.html')
    if LOCAL_RUN:
        url = 'http://localhost:9191/api' #Local test
    else:
        url = ' https://demo.onmydisk.net/'
    data = {'action': 'getUserInfo', 'session_id': access_token}
    resp = requests.post(url, json=data, headers={'Authorization': 'token:'+access_token})
    username = resp.json()['username']

    results = []
    if Urls.query.count() == 0:
        init_podsum()

    query = request.args.get('q')
    if not query:
        LOG.info("No query")
        return render_template("search/user.html")
    else:

        results = []
        query = query.lower()
        pears = ['0.0.0.0']
        results, pods = score_pages.run(query, pears, url_filter=[ join(url,username), 'http://localhost:9090/static/']) #TODO: replace filter with correct OMD endpoint
        print(results)
        r = app.make_response(jsonify(results))
        r.mimetype = "application/json"
        return r


@search.route('/anonymous', methods=['POST','GET'])
@cross_origin()
def anonymous():  
    results = []
    if Urls.query.count() == 0:
        init_podsum()

    query = request.args.get('q')
    if not query:
        LOG.info("No query")
        return render_template("search/anonymous.html")
    else:
        results = []
        query = query.lower()
        pears = ['0.0.0.0']
        if LOCAL_RUN:
            url = 'http://localhost:9090/static/testdocs/shared' #Local test
        else:
            url = ' https://demo.onmydisk.net/shared'
        results, pods = score_pages.run(query, pears, url_filter=[url])
        print(results)
        r = app.make_response(jsonify(results))
        r.mimetype = "application/json"
        return r



@search.route('/', methods=['GET','POST'])
@search.route('/index', methods=['GET','POST'])
def index():
    if Urls.query.count() == 0:
        init_podsum()
    print("LOCAL",LOCAL_RUN)
    access_token = request.cookies.get('OMD_SESSION_ID')  
    if not access_token:
        return render_template('search/anonymous.html')
    else:
        if LOCAL_RUN:
            url = 'http://localhost:9191/api' #Local test
        else:
            url = ' https://demo.onmydisk.net/'
        print("CONNECTING TO:",url)
        data = {'action': 'getUserInfo', 'session_id': access_token}
        resp = requests.post(url, json=data, headers={'accept':'application/json', 'Authorization': 'token:'+access_token})
        if resp.status_code == requests.codes.ok:
            username = resp.json()['username']
            # Create a new response object
            resp_frontend = make_response(render_template( 'search/user.html', welcome="Welcome "+username))
            # Transfer the cookies from backend response to frontend response
            for name, value in request.cookies.items():
                print("SETTING COOKIE:",name,value)
                resp_frontend.set_cookie(name, value, samesite='Lax')
            return resp_frontend
        else:
            # Create a new response object
            resp_frontend = make_response(render_template( 'search/anonymous.html'))
            resp_frontend.set_cookie('OMD_SESSION_ID', '', expires=0, samesite='Lax')
            return resp_frontend




@search.route('/login', methods=['GET', 'POST'])
def login():
    # Declare the login form using FlaskForm library
    form = LoginForm(request.form)
    print(form)
    # Flask message injected into the page, in case of any errors
    msg = None
    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():
        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str)
        # send authorization message to on my disk
        if LOCAL_RUN:
            url = 'http://localhost:9191/api' #Local test
        else:
            url = ' https://demo.onmydisk.net/signin/'
        data = {'action': 'signin', 'username': username, 'password': password}
        user_info = requests.post(url, json=data) 
        if user_info == None:
            msg = "Incorrect credentials"
            return render_template( 'search/login.html', form=form, msg=msg)
        else:
            access_token = user_info.cookies.get('OMD_SESSION_ID')
            print(user_info.json())
            print(user_info.cookies)
            username = user_info.json()['username']
            # Create a new response object
            resp_frontend = make_response(render_template( 'search/user.html', welcome="Welcome "+username))
            # Transfer the cookies from backend response to frontend response
            for name, value in user_info.cookies.items():
                print("SETTING COOKIE:",name,value)
                resp_frontend.set_cookie(name, value, samesite='Lax')
            return resp_frontend
            #return render_template('search/user.html', welcome="Welcome "+username)
    else:
       msg = "Unknown user"
       return render_template( 'search/login.html', form=form, msg=msg)

@search.route('/logout', methods=['GET','POST'])
def logout():
    access_token = request.cookies.get('OMD_SESSION_ID')
    if LOCAL_RUN:
        url = 'http://localhost:9191/api' #Local test
    else:
        url = ' https://demo.onmydisk.net/signout/'
    data = {'action': 'signout', 'session_id': access_token}
    logout_confirmation = requests.post(url, json=data, headers={'accept':'application/json', 'Authorization': 'token:'+access_token})
    if logout_confirmation.status_code == requests.codes.ok:
        print("Logging out")
    else:
        print("Logged out")
    # Create a new response object
    resp_frontend = make_response(render_template( 'search/anonymous.html'))
    resp_frontend.set_cookie('OMD_SESSION_ID', '', expires=0, samesite='Lax')
    return resp_frontend
