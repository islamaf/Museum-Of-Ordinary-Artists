from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

from flaskr.database import *

auth = Blueprint('auth', __name__, template_folder='./templates', static_folder='./static', static_url_path='/static/auth')

mail_on_signup = Mail()
s = URLSafeTimedSerializer('SecretMailMessage')

@auth.route('/login')
def login():
    if current_user.is_authenticated:
        from flaskr.user_control import user_control
        return redirect(url_for('user_control.profile', name=current_user.name))
    return render_template('login.html')

@auth.route('/signup')
def signup():
    if current_user.is_authenticated:
        from flaskr.user_control import user_control
        return redirect(url_for('user_control.profile', name=current_user.name))
    return render_template('signup.html')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home.index'))

@auth.route('/signup', methods=['POST', 'GET'])
def signup_post():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))

        new_user = User(name=name, email=email, password=generate_password_hash(password, method='sha256'))

        # print(new_user)

        db.session.add(new_user)
        db.session.commit()

        send(email)

        return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('auth.signup'))


@auth.route('/send_mail_on_signup', methods=['POST', 'GET'])
def send(email_from_signup):
    email = email_from_signup
    token = s.dumps(email, salt='email-confirm')

    msg = Message('Confirm Email', sender='islam3501@gmail.com', recipients=[email])
    link = url_for('user_control.confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail_on_signup.send(msg)

    # return '<h1> The email you entered is {}. The token is {}.</h1>'.format(email, token)
    return render_template('token.html', email=email)


@auth.route('/confirm_email_on_signup/<token>')
def confirm_email(token):
    try:
        email_confirm = s.loads(token, salt='email-confirm', max_age=3600)
        confirm = User.query.filter_by(email=email_confirm).first()
        confirm.is_confirmed = True
        db.session.commit()
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    # return '<h1>Confirmation succeeded!</h1>'
    return render_template('confirm.html')


@auth.route('/login', methods=['POST', 'GET'])
def login_post():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()
        # print(user)

        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        return redirect(url_for('user_control.profile', name=current_user.name))
    else:
        return redirect(url_for('auth.login'))