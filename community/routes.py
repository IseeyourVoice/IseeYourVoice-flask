import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from community.file import allowed_file
from models import db
from models.post import Post

community_bp = Blueprint('community_bp', __name__)


@login_required
@community_bp.route('/')
def community():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('community.html', posts=posts)


@community_bp.route('/upload', methods=['GET','POST'])
@login_required
def post():
    if request.method == 'POST':
        content = request.form['content']

        ## 음원
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
        else:
            filename = None

        new_post = Post(user_id=current_user.id, content=content, audio_file=filename)
        db.session.add(new_post)
        db.session.commit()

        flash("Post 성공")
        return redirect(url_for('community_bp.community'))
    return render_template('upload.html')