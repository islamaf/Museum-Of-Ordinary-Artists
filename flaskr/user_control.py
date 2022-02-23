import os
from flask import Blueprint, redirect, render_template, url_for, abort, request, flash, json
from flask_login import current_user, login_required
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from werkzeug.utils import secure_filename

from flaskr.database import *
from resources import get_bucket, get_buckets_list
from flaskr.home import cache

user_control = Blueprint('user_control', __name__, template_folder='./templates', static_folder='./static',
                         static_url_path='/static/user_control')


mail = Mail()
s = URLSafeTimedSerializer('SecretMailMessage')


@user_control.route('/send_mail', methods=['POST', 'GET'])
@login_required
def send():
    email = current_user.email
    token = s.dumps(email, salt='email-confirm')

    msg = Message('Confirm Email', sender='islam3501@gmail.com', recipients=[email])
    link = url_for('user_control.confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)

    return render_template('token.html', email=email)


@user_control.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    try:
        email_confirm = s.loads(token, salt='email-confirm', max_age=3600)
        confirm = User.query.filter_by(email=email_confirm).first()
        confirm.is_confirmed = True
        db.session.commit()
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    return render_template('confirm.html')


@user_control.route('/<name>')
@cache.cached(timeout=10)
def profile(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        return abort(404)
    profile_picture = user.profile_picture

    post_list = []
    pending_list = []
    posts = user.posts.all()
    for p in posts:
        if p.is_approved:
            post_list.append(p.name)
        else:
            pending_list.append(p.name)

    post_list = sorted(post_list, key=lambda k: k[2], reverse=True)

    return render_template('profile.html', user=user, posts=post_list, pending_posts=pending_list,
                           profile_pic=profile_picture)


@user_control.route('/edit')
@login_required
def edit():
    return render_template('edit.html', email=current_user.email, password=current_user.password)


def profile_image_append(image):
    from flaskr.home import allowed_image

    filenames = []
    if image.filename == "":
        return redirect(request.url)

    if image and allowed_image(image.filename):
        filename = secure_filename(image.filename)

        path_to_dir = './flaskr/static/images/dp/' + filename
        user = User.query.filter_by(name=current_user.name).first()

        default = 'img_avatar.png'
        if user.profile_picture != default:
            os.remove('./flaskr/static/images/dp/' + user.profile_picture)
        user.profile_picture = filename

        db.session.commit()

        image.seek(0)
        image.save(path_to_dir)

        filenames.append(image.filename)

    return filenames


@user_control.route('/update_image', methods=['POST'])
@login_required
def update_image():
    from flaskr.home import allowed_image

    new_image = request.files['new_pic']

    if new_image.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if new_image and allowed_image(new_image.filename):
        filename = secure_filename(new_image.filename)
        user = User.query.filter_by(name=current_user.name).first()
        my_bucket = get_bucket()
        default = 'img_avatar.png'
        user.profile_picture = filename

        db.session.commit()

        new_image.seek(0)
        my_bucket.Object("static/images/dp/" + new_image.filename).put(Body=new_image)

    flash('Profile picture updated!')
    return redirect(url_for('user_control.profile', name=current_user.name))


@user_control.route('/edit', methods=['POST'])
@login_required
def edit_user():
    email = request.form.get('email')
    password = request.form.get('password')
    new_password = generate_password_hash(password, method='sha256')

    email_update = User.query.filter_by(email=current_user.email).first()
    password_update = User.query.filter_by(password=current_user.password).first()

    posts_query_update = Post.query.filter_by(user_email=current_user.email).all()
    for post_iter in posts_query_update:
        post_iter.user_email = email

    username = User.query.all()
    for user in username:
        posts = user.posts.all()
        for p in posts:
            p.email = email
            p.password = new_password

    email_update.email = email
    password_update.password = new_password
    db.session.commit()

    flash('Updates saved!')

    return redirect(url_for('user_control.profile', name=current_user.name))


@user_control.route('/delete_user')
def u_delete():
    return redirect(url_for('home.index'))


@user_control.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    email = request.form.get('email')

    if email == current_user.email:
        user = User.query.filter_by(email=email).first()
        db.session.delete(user)

        posts = Post.query.filter_by(user_email=email).all()
        for post in posts:
            db.session.delete(post)
        db.session.commit()
    else:
        return redirect(url_for('user_control.edit_user'))

    return redirect(url_for('home.index'))


def del_cancel(link_post):
    my_bucket = get_bucket()
    my_bucket.Object('static/images/uploads/' + link_post).delete()

    post_in_db = Post.query.filter_by(name=link_post).first()
    db.session.delete(post_in_db)
    db.session.commit()
    return flash('Post has been deleted!')


@user_control.route('/delete_post', methods=['POST'])
@login_required
def delete_post():
    link_post = request.form.get('post_to_delete')
    del_cancel(link_post)

    return redirect(url_for('user_control.profile', name=current_user.name))


@user_control.route('/cancel_submission', methods=['POST'])
@login_required
def cancel_submission():
    link_post = request.form.get('post_to_cancel')
    del_cancel(link_post)

    return redirect(url_for('user_control.profile', name=current_user.name))


@user_control.route('/follow/<name>', methods=['POST'])
@login_required
def follow(name):
    user = User.query.filter_by(name=name).first()
    if user is None:
        flash('User {} is not found.'.format(name))
        return redirect(url_for('home.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user_control.profile', name=name))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}!'.format(name))
    return redirect(url_for('user_control.profile', name=name))


@user_control.route('/unfollow/<name>', methods=['POST'])
@login_required
def unfollow(name):
    user = User.query.filter_by(name=name).first()
    if user is None:
        flash('User {} is not found.'.format(name))
        return redirect(url_for('home.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user_control.profile', name=name))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are unfollowing {}!'.format(name))
    return redirect(url_for('user_control.profile', name=name))


@user_control.route('/like/<int:post_id>', methods=['GET', 'POST'])
def like_action(post_id):
    if request.method == "POST":
        post = Post.query.filter_by(id=post_id).first_or_404()
        if not current_user.has_liked_post(post):
            current_user.like_post(post)
            db.session.commit()
            return json.dumps({'status': 'liked'})
        else:
            current_user.unlike_post(post)
            db.session.commit()
            return json.dumps({'status': 'unliked'})
    return redirect(request.referrer)