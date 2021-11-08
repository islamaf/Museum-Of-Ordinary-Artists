from flask import Flask, request, url_for
from flask_mail import Mail, Message
from itsdangerous import SignatureExpired, URLSafeSerializer

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

# mail = Mail(app)
# s = URLSafeSerializer('safemessage')

@app.route('/')
def index():
    if request.method == 'GET':
        return '<form action="/" method="POST"><label class="label-mod">Email confirmation: </label>' \
               '<input type="text" name="email"><input type="submit" value="Submit"></form>'

    email = request.form.get('email')
    token = s.dumps(email, salt='email-confirm')

    msg = Message('Confirm Email', sender='islam3501@gmail.com', recipients=[email])

    link = url_for('home.confirm_email', token=token, _external=True)

    msg.body = 'Your link is {}'.format(link)

    mail.send(msg)

    return '<h1> The email you entered is {}. The token is {}.</h1>'.format(email, token)


@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.load(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    return '<h1>The token works!</h1>'

if __name__ == 'main':
    app.run(debug=True)