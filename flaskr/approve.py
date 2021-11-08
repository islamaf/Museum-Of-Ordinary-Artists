from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_login import current_user, login_required

from flaskr.database import *
from flaskr.home import cache

approve = Blueprint('approve', __name__, template_folder='./templates', static_folder='./static', static_url_path='/static/approve')


@approve.route('/approval')
@cache.cached(timeout=10)
@login_required
def to_approve():
    if current_user.is_admin:
        username = User.query.all()

        post_list = []
        for user in username:
            posts = user.posts.all()
            for p in posts:
                if not p.is_approved:
                    post_list.append((p.name, p.Author.name, p.is_approved))

        return render_template('secret.html', all_posts=post_list)
    else:
        abort(404)


@approve.route('/confirm_approval', methods=['POST'])
@login_required
def confirm_approval():
    name = request.form.get('name')
    post = request.form.get('post')

    username = User.query.all()
    for user in username:
        posts = user.posts.all()
        for p in posts:
            if (not p.is_approved) and p.name == post and p.Author.name == name:
                p.is_approved = True
                db.session.commit()

    return redirect(url_for('approve.to_approve'))