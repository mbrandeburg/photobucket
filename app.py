from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['PHOTOBUCKET_ADMIN']
app.config['UPLOAD_FOLDER'] = 'uploads/rehearsal'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'heif', 'hevc', 'mp4', 'mov', 'avi'}

# Ensure the upload path exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def check_password(password):
    with open('password.txt') as f:
        return f.read().strip() == password

@app.route('/')
def index():
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=file_list)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if check_password(request.form['password']):
            session['authenticated'] = True
            return redirect(url_for('manage_photos'))
        else:
            flash('Incorrect password', 'danger')
    return render_template('admin.html')

@app.route('/manage_photos')
def manage_photos():
    if not session.get('authenticated'):
        return redirect(url_for('admin'))
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('manage_photos.html', files=file_list)

@app.route('/delete_photo/<filename>')
def delete_photo(filename):
    if not session.get('authenticated'):
        return redirect(url_for('admin'))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    flash('Photo deleted', 'success')
    return redirect(url_for('manage_photos'))

if __name__ == '__main__':
    app.run(debug=True, port=7043)
