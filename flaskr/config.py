import os

secret_key = 'mofoaSecretKey'

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
S3_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY")