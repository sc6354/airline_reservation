from flask import Blueprint, render_template, session, request, flash, redirect, url_for, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from . import db 
from flask_login import login_user, current_user, login_required, logout_user
from .models import customer, booking_agent, airline_staff, users 

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST', 'GET'])
def userLogin():
    if request.method =='POST':
        username = request.form.get('email')
        pw = request.form.get('password')
        remember = True if request.form.get('remember') else False
        curr_user = users.query.filter_by(username=username).first()
        curr_staff = airline_staff.query.filter_by(username=username).first()
        curr_customer = customer.query.filter_by(email=username).first()

        if not username:
            flash('Email is required.')
            return (redirect(url_for('auth.login')))
        elif not pw:
            flash('Password is required.')
            return (redirect(url_for('auth.login')))
        elif not curr_user and not check_password_hash(curr_user.password, pw):
            flash('Login unsuccefully, try again.')
            return (redirect(url_for('auth.login')))
        else:
            login_user(curr_user, remember = remember)
            if curr_staff:
                return redirect(url_for('main.staffHome'))
            if curr_customer:
                return redirect(url_for('main.profile'))

        return redirect(url_for('main.index'))
    return render_template('login.html')

@auth.route('/signup')
def signup():
    return render_template('signup.html') 

@auth.route('/user_signup', methods=['GET', 'POST'])
def userSignup(): 
        if request.method == 'POST':
            email = request.form.get('email')
            name = request.form.get('name')
            pw = request.form.get('password')
            building = request.form.get('address')
            street = request.form.get('address')
            city = request.form.get('city')
            state = request.form.get('state')
            phone_number = request.form.get('phone_number')
            passport_num = request.form.get('passport_num')
            passport_expiration = request.form.get('passport_expiration')
            passport_country = request.form.get('passport_country')
            dob = request.form.get('dob')

            error = None

            cust =  customer.query.filter_by(email=email).first()

            if not email:
                error = 'Email is required.'
            elif not pw:
                error = 'Password is required.'
            elif(cust):
                error = 'Email address {} is already registered. Go to the login page.'.format(email)
            else:
                new_customer = customer(email = email, password = generate_password_hash(pw, method='sha256'), name = name)
                new_user = users(username=email, password = generate_password_hash(pw, method='sha256'))
                db.session.add(new_user)
                db.session.add(new_customer)
                db.session.commit()
                return redirect(url_for('auth.login'))
                
            flash(error)
        return render_template('userSignup.html')

@auth.route('/agent_signup', methods=['GET', 'POST'])
def agentSignup():
    if request.method == 'POST':
            email = request.form.get('email')
            agent_id = request.form.get('id')
            pw = request.form.get('password')
            error = None
            agent =  booking_agent.query.filter_by(email=email).first()

            if not email:
                error = 'Email is required.'
            elif not pw:
                error = 'Password is required.'
            elif(agent):
                error = 'Agent email address {} is already registered. Go to the login page.'.format(email)
            else:
                new_agent = booking_agent(email = email, password = generate_password_hash(pw, method='sha256'), booking_agent_id = id)
                db.session.add(new_agent)
                db.session.commit()
                return redirect(url_for('main.index'))
                
            flash(error)
    return render_template('agentSignup.html')

@auth.route('/staff_signup', methods =['GET', 'POST'])
def staffSignup():
    if request.method == 'POST':
        email = request.form.get('username')
        pw = request.form.get('password')
        f_name = request.form.get('first_name')
        l_name = request.form.get('last_name')
        dob = request.form.get('date')
        airline = request.form.get('airline')
        
        error = None
        staff =  airline_staff.query.filter_by(username=email).first()
        
        if not email:
            error = 'Username (Email) is required.'
        elif not pw:
            error = 'Password is required.'
        elif(staff):
            error = 'Staff email address {} is already registered. Go to the login page.'.format(email)
        else:
            new_staff = airline_staff(username= email, password = generate_password_hash(pw, method='sha256'),first_name =f_name,
                                            last_name=l_name, date_of_birth=dob, airline_name =airline)
            new_user = users(username = email, password = generate_password_hash(pw, method='sha256'))
            db.session.add(new_staff)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('main.staff_home'))
                    
        flash(error)
    return render_template('staffSignup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


