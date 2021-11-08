from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('users.id'))
                     )

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(1000), default='img_avatar.png')
    posts = db.relationship('Post', backref='Author', lazy='dynamic')
    followed = db.relationship('User', secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    liked = db.relationship('PostLike',
                            foreign_keys='PostLike.user_id',
                            backref='user', lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(user_id=self.id, post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(PostLike.user_id == self.id,
                                     PostLike.post_id == post.id).count() > 0

    def __repr__(self):
        return "<User(name='%s', email='%s', password='%s')>" % (self.name, self.email, self.password)


class Post(db.Model):
    import datetime
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    # data = db.Column(db.BLOB)
    insertion_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_email = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)
    user_name = db.Column(db.String(1000), db.ForeignKey('users.name'))
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')

    def __repr__(self):
        return "<Post(name='%s', user_email='%s')>" % (self.name, self.user_email)


class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))