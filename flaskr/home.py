import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from flask_caching import Cache
from werkzeug.utils import secure_filename
from base64 import b64encode, decode
import datetime
from datetime import timedelta
import string
import random

from flaskr.database import *

from resources import get_bucket, get_buckets_list
from azure.storage.blob import BlockBlobService

home = Blueprint('home', __name__, template_folder='./templates', static_folder='./static',
                 static_url_path='/static/home')

cache = Cache()

account_name = 'mofoa'
# account_key = '+R0ExML/EbevWuhOHibLzZ4OR4/4/haTYnC6Hcv0I9c8/0jHCa1/Iu45NcrG7LKiAuhaQMGoZ+fGDV6K+qUTUA=='
account_key = os.environ.get("ACCOUNT_KEY")
container_name = 'mofoa-images'

block_blob_service = BlockBlobService(
    account_name=account_name,
    account_key=account_key
)

@home.route('/')
@cache.cached(timeout=10)
def index():
    check_if_deleted = Post.query.filter_by(Author=None).all()
    try:
        for x in check_if_deleted:
            db.session.delete(x)
        db.session.commit()
    except EOFError as e:
        print('Connection failed:(')

    username = User.query.all()

    post_list = []
    all_posts = Post.query.all()
    for post in all_posts:
        if post.is_approved:
            post_list.append(post)

    return render_template('base.html', wall=post_list)


@home.route('/upload')
def do_upload():
    if current_user.is_authenticated:
        username = User.query.filter_by(name=current_user.name).first()

        if not username.is_confirmed:
            from flaskr.user_control import user_control
            return redirect(url_for('user_control.send'))

    return render_template('upload.html')


allowed_extensions = ["JPEG", "JPG", "PNG"]


def allowed_image(filename):
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in allowed_extensions:
        return True
    else:
        return False


def generate_random_string():
    S = 15
    filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=S))
    return filename


def images_append(images_list):
    filenames = []
    for image in images_list[:3]:

        if image.filename == "":
            return redirect(request.url)

        if image and allowed_image(image.filename):
            filename = secure_filename(image.filename)

            path_to_dir = './flaskr/static/images/uploads/' + filename
            user = User.query.filter_by(name=current_user.name).first()

            add_post = Post(name=filename, user_email=current_user.email, Author=user)

            db.session.add(add_post)
            db.session.commit()

            image.seek(0)
            image.save(path_to_dir)

            filenames.append(image.filename)

    return filenames


@home.route('/submit_post', methods=['POST'])
@login_required
def submit_post():
    images = request.files.getlist("images")

    username = User.query.filter_by(name=current_user.name).first()

    pl = []
    posts = username.posts.all()
    if posts:
        for p in posts:
            if p.is_approved:
                pl.append(p.insertion_date)

        pl_s = sorted(pl, reverse=True)

        for image in images:

            if image.filename == "":
                return redirect(request.url)

            if image and allowed_image(image.filename):
                filename = secure_filename(image.filename)

                my_bucket = get_bucket()

                user = User.query.filter_by(name=current_user.name).first()

                add_post = Post(name=filename, user_email=current_user.email, Author=user)

                db.session.add(add_post)
                db.session.commit()

                image.seek(0)
                my_bucket.Object("static/images/uploads/" + image.filename).put(Body=image)

        flash('Post(s) have been submitted for approval!')

        return render_template('approve.html')
    else:
        for image in images:
            filename = secure_filename(image.filename)

            my_bucket = get_bucket()

            user = User.query.filter_by(name=current_user.name).first()

            add_post = Post(name=filename, user_email=current_user.email, Author=user)

            db.session.add(add_post)
            db.session.commit()

            image.seek(0)
            my_bucket.Object("static/images/uploads/" + image.filename).put(Body=image)

        flash('Post(s) have been submitted for approval!')

        return render_template('approve.html')


@home.route('/test_confirm')
def test_confirm():
    return render_template('confirm.html')
