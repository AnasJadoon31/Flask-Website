from datetime import datetime
import json
from werkzeug.utils import secure_filename 
from flask import Flask, render_template, request, session, flash, redirect, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import VARCHAR, Integer, String, or_
from sqlalchemy.orm import Mapped, mapped_column
import requests
import os
import asyncio
from pyppeteer import launch

with open("C:\\Python\\Website\\config.json", 'r') as c:
    params = json.load(c)["params"]


local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params["upload_location"]

if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["live_uri"]
db = SQLAlchemy(app)

class Contact(db.Model):
    __tablename__ = 'contact'
    
    sno: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), unique=False, nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=False, nullable=False)
    phone: Mapped[str] = mapped_column(VARCHAR(15), unique=False, nullable=False)
    message: Mapped[str] = mapped_column(String(500), unique=False, nullable=False)
    dated: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)

class Post(db.Model):
    __tablename__ = 'posts'
    
    sno: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), unique=False, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(200), unique=False, nullable=False)
    slug: Mapped[str] = mapped_column(VARCHAR(50), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(VARCHAR(999999), unique=False, nullable=False)
    cover_img: Mapped[str] = mapped_column(String(500), unique=False, nullable=True)
    category: Mapped[str] = mapped_column(String(500), unique=False, nullable=False)
    volume: Mapped[str] = mapped_column(String(500), unique=False, nullable=False)
    volume_link: Mapped[str] = mapped_column(String(500), unique=False, nullable=False)
    labels: Mapped[str] = mapped_column(String(500), unique=False, nullable=True)
    author: Mapped[str] = mapped_column(String(500), unique=False, nullable=False)
    dated: Mapped[datetime] = mapped_column(default=datetime.now(), nullable=False)
    
@app.route("/")
def home():
    posts_per_page = params['posts_per_page']
    # Get the current page number from the query string (defaults to 1)
    page = request.args.get('page', 1, type=int)
    
    # Calculate the offset for SQL query
    offset = (page - 1) * posts_per_page
    
    # Query the database with limit and offset
    posts = Post.query.order_by(Post.dated.desc()).limit(posts_per_page).offset(offset).all()
    
    # Calculate the total number of pages
    total_posts = Post.query.count()
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    no_posts = len(posts) == 0
    
    if no_posts:
        return render_template('no_posts.html', params=params)
    
    return render_template('index.html', params=params, posts=posts, page=page, total_pages=total_pages)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/contact/success")
def contact_success():
    return render_template('contact_success.html', params=params)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session) and (session['user'] == params['admin_user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return render_template('upload_success.html', params=params)
        return render_template('dashboard.html', params=params)
    return render_template('login.html', params=params)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        form_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "access_key": "d0d73ebb-4808-412a-8225-dffdbc6bb0d5"
    }
        entry = Contact(name = name, email = email, phone = phone, message = message, dated = datetime.now())     #type:ignore
        db.session.add(entry)
        db.session.commit()
        web3forms_url = "https://api.web3forms.com/submit"
        web3forms_response = requests.post(web3forms_url, data=form_data)
        return render_template('contact_success.html', params=params)
    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/preview/<string:post_slug>", methods = ['GET'])
def preview_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('preview.html', params=params, post=post)

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if ('user' in session) and (session['user'] == params['admin_user']):
        posts = Post.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params['admin_user'] and password == params['admin_pass']:
            session['user'] = username
            posts = Post.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
        
    return render_template('login.html', params=params)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session) and (session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            content = request.form.get('content')
            cover_img = request.form.get('cover_img')
            category = request.form.get('category')
            volume = request.form.get('volume')
            volume_link = request.form.get('volume_link')
            labels = request.form.get('labels')
            author = request.form.get('author')
            dated = request.form.get('dated')
            f = request.files['file1']
            if sno == '0':
                post = Post(
                    title=box_title,
                    subtitle=subtitle,
                    slug=slug,
                    content=content,
                    cover_img=cover_img,
                    category=category,
                    volume=volume,
                    volume_link=volume_link,
                    labels=labels,
                    author=author,
                    dated=datetime.now()
                )
                db.session.add(post)
                db.session.commit()
                if f:
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
                    cover_img = Post(cover_img=f.filename)
                    post.cover_img = f.filename
                    db.session.commit()
                flash('Post created successfully!', 'success')
                return redirect(url_for('edit', sno=post.sno, params=params, post=post))
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.sno = sno
                post.title = box_title
                post.subtitle = subtitle
                post.slug = slug
                post.content = content
                post.cover_img = cover_img
                post.category = category
                post.volume = volume
                post.volume_link = volume_link
                post.labels = labels
                post.author = author
                post.dated = dated
                db.session.commit()
                if f:
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
                    post.cover_img = f.filename
                    db.session.commit()
                flash('Post edited successfully!', 'success')
                return redirect(url_for('edit', sno=sno, params=params,post=post))
        else:
            post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)
    return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect ("/dashboard")

@app.route("/delete/<string:sno>")
def delete(sno):
    if ('user' in session) and (session['user'] == params['admin_user']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
        return redirect(url_for('dashboard', params=params))
    return render_template ("/login.html", params = params)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Return the URL of the uploaded image
        return jsonify({'location': url_for('static', filename=f'uploads/{filename}')})
    return jsonify({'error': 'File not saved'})

@app.route("/volume_i")
def volume_i():
    posts_per_page = params['posts_per_page']
    # Get the current page number from the query string (defaults to 1)
    page = request.args.get('page', 1, type=int)
    
    # Calculate the offset for SQL query
    offset = (page - 1) * posts_per_page
    
    # Query the database with limit and offset, filtering by Volume I
    posts = Post.query.filter(Post.volume == 'Volume I').order_by(Post.dated.desc()).limit(posts_per_page).offset(offset).all()
    
    # Calculate the total number of posts for Volume I
    total_posts = Post.query.filter(Post.volume == 'Volume I').count()
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    no_posts = len(posts) == 0
    
    if no_posts:
        return render_template('no_posts.html', params=params)
    
    return render_template('volumei.html', params=params, posts=posts, page=page, total_pages=total_pages)

@app.route("/volume_ii")
def volume_ii():
    posts_per_page = params['posts_per_page']
    # Get the current page number from the query string (defaults to 1)
    page = request.args.get('page', 1, type=int)
    
    # Calculate the offset for SQL query
    offset = (page - 1) * posts_per_page
    
    # Query the database with limit and offset, filtering by Volume II
    posts = Post.query.filter(Post.volume == 'Volume II').order_by(Post.dated.desc()).limit(posts_per_page).offset(offset).all()
    
    # Calculate the total number of posts for Volume II
    total_posts = Post.query.filter(Post.volume == 'Volume II').count()
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    no_posts = len(posts) == 0
    
    if no_posts:
        return render_template('no_posts.html', params=params)
    
    return render_template('volumeii.html', params=params, posts=posts, page=page, total_pages=total_pages)

@app.route("/jadore")
def jadore():
    return render_template('jadore.html', params=params)


@app.route("/memorials", methods = ['GET'])
def memorials():
    posts_per_page = params['posts_per_page']
    # Get the current page number from the query string (defaults to 1)
    page = request.args.get('page', 1, type=int)
    
    # Calculate the offset for SQL query
    offset = (page - 1) * posts_per_page
    
    # Query the database with limit and offset, filtering by Volume II
    posts = Post.query.filter(Post.category == 'Memorials').order_by(Post.dated.desc()).limit(posts_per_page).offset(offset).all()
    
    # Calculate the total number of posts for Volume II
    total_posts = Post.query.filter(Post.category == 'Memorials').count()
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    no_posts = len(posts) == 0
    
    if no_posts:
        return render_template('no_posts.html', params=params)
    
    return render_template('memorials.html', params=params, posts=posts, page=page, total_pages=total_pages)


@app.route("/gallery", methods = ['GET'])
def gallery():
    posts_per_page = params['posts_per_page']
    # Get the current page number from the query string (defaults to 1)
    page = request.args.get('page', 1, type=int)
    
    # Calculate the offset for SQL query
    offset = (page - 1) * posts_per_page
    
    # Query the database with limit and offset, filtering by Volume II
    posts = Post.query.filter(Post.category == 'Gallery').order_by(Post.dated.desc()).limit(posts_per_page).offset(offset).all()
    
    # Calculate the total number of posts for Volume II
    total_posts = Post.query.filter(Post.category == 'Gallery').count()
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    no_posts = len(posts) == 0
    
    if no_posts:
        return render_template('no_posts.html', params=params)
    
    return render_template('gallery.html', params=params, posts=posts, page=page, total_pages=total_pages)

@app.route("/search", methods=['GET'])
def search():
    search = request.args.get('search', '')
    posts_per_page = 10
    # Get the current page number from the query string (defaults to 1)
    page = request.args.get('page', 1, type=int)
    
    # Calculate the offset for SQL query
    offset = (page - 1) * posts_per_page
    
    # Adjust the search query with wildcards for partial matches
    search_filter = "%{}%".format(search)
    
    # Query the database with limit and offset
    posts = Post.query.filter(
        or_(
            Post.title.ilike(search_filter),
            Post.content.ilike(search_filter),
            Post.subtitle.ilike(search_filter),
            Post.author.ilike(search_filter),
            Post.volume.ilike(search_filter)
        )
    ).order_by(Post.dated.desc()).limit(posts_per_page).offset(offset).all()
    
    # Calculate the total number of matching posts
    total_posts = Post.query.filter(
        or_(
            Post.title.ilike(search_filter),
            Post.content.ilike(search_filter),
            Post.subtitle.ilike(search_filter),
            Post.author.ilike(search_filter),
            Post.volume.ilike(search_filter)
        )
    ).count()
    
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    no_posts = len(posts) == 0
    
    if no_posts:
        return render_template('no_posts.html', params=params)
    
    return render_template('search.html', params=params, posts=posts, page=page, total_pages=total_pages, search=search)

@app.route("/archive", methods=['GET'])
def archive():
    
    # Prepare the data for each post
    archive_data = []
    # Initialize the data dictionary
    data = {
        'title': "Test",
        'start': "2024-09-03",
        'end': ''  # Initialize the end date
        }
    
    # Set end date to start date if end is empty
    if not data['end']:
        data['end'] = data['start']

    # Add the data dictionary to archive_data
    archive_data.append(data)

    
    return render_template('archive.html', params=params, archive_data=archive_data)


@app.route('/load-content/<string:volume>/<string:category>', methods=['GET'])
def load_content(volume, category):
    # Load posts from the single specified volume
    if category == "Others":
        # Load posts from Gallery and Memorials
        posts = Post.query.filter(Post.volume == volume).filter(Post.category.in_(['Gallery', 'Memorials'])).order_by(Post.dated.desc()).all()
    else:
        # Load posts from the single specified category
        posts = Post.query.filter(Post.volume == volume).filter_by(category=category).order_by(Post.dated.desc()).all()

    return render_template('content-snippet.html', posts=posts)

@app.route('/load-content-home/<category>', methods=['GET'])
def load_content_home(category):
    page = request.args.get('page', 1, type=int)
    
    if category == "Others":
        # Load posts from Gallery and Memorials and paginate them
        posts = Post.query.filter(Post.category.in_(['Gallery', 'Memorials'])).order_by(Post.dated.desc()).paginate(page=page, per_page=5)
    else:
        # Load posts from the single specified category and paginate them
        posts = Post.query.filter_by(category=category).order_by(Post.dated.desc()).paginate(page=page, per_page=5)
    
    return render_template('content-snippet.html', posts=posts.items, page=posts.page, total_pages=posts.pages, selected_category=category)

@app.route('/load-gallery/<volume>', methods=['GET'])
def load_gallery(volume):
    # Fetch posts with the category "Gallery" from the specified volume
    posts = Post.query.filter_by(volume=volume, category='Gallery').order_by(Post.dated.desc()).all()
    return render_template('content-snippet.html', posts=posts)

@app.route('/load-memorials/<volume>', methods=['GET'])
def load_memorials(volume):
    # Fetch posts with the category "Memorials" from the specified volume
    posts = Post.query.filter_by(volume=volume, category='Memorials').order_by(Post.dated.desc()).all()
    return render_template('content-snippet.html', posts=posts)

if __name__ == "__main__":
    app.run(debug=True)