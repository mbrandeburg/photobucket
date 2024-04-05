from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session, flash, after_this_request
from werkzeug.utils import secure_filename
import os
import argparse
import logging

# Parse command-line arguments for mode
parser = argparse.ArgumentParser(description='Run the Flask app in test or main mode.')
parser.add_argument('--mode', type=str, default=None, help='Mode in which to run the app: test or main')
args = parser.parse_args()

# Determine the UPLOAD_FOLDER based on the mode
if args.mode == 'test':
    upload_folder = 'uploads'  # Relative path for test mode
elif args.mode == 'main':
    upload_folder = '/mnt/uploads'  # Absolute path for main mode
else:
    logging.error("You must pass either main or test for mode flag. Please run -h for help.")
    exit(1)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['PHOTOBUCKET_ADMIN']
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'heif', 'hevc', 'mp4', 'mov', 'avi'}
app.config['SUBFOLDERS'] = ['BCN', 'rehearsal', 'reception']

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Ensure the upload paths for all specified subfolders exist
def ensure_upload_folders_exist():
    for folder in app.config['SUBFOLDERS']:
        path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(path, exist_ok=True)

ensure_upload_folders_exist()

# Helper function to check password
def check_password(password):
    return password == app.config['SECRET_KEY']

@app.route('/')
def index():
    photos = {folder: os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], folder)) for folder in app.config['SUBFOLDERS']}
    return render_template('index.html', photos=photos)

@app.route('/upload/<folder_name>', methods=['POST'])
def upload_file(folder_name):
    if folder_name not in app.config['SUBFOLDERS']:
        flash('Folder not allowed')
        logging.warn('Attempted to upload a folder -- not allowed')
        return redirect(url_for('index'))

    if 'photo' not in request.files:
        flash('No file part')
        logging.warn('Attempted to upload without a file -- not allowed')
        return redirect(url_for('index'))

    file = request.files['photo']
    if file.filename == '' or not allowed_file(file.filename):
        flash('No selected file or file type not allowed', 'danger')
        logging.warn(f"Attempted to upload an non-allowed file type: {filename.rsplit('.', 1)[1].lower()}")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename)
    file.save(save_path)
    flash(f'File {filename} was uploaded successfully', 'success')  # Flash success message
    logging.info(f'File {filename} was uploaded successfully')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if check_password(request.form['password']):
            session['authenticated'] = True
            logging.info('Admin login accepted')
            return redirect(url_for('manage_photos'))
        else:
            flash('Incorrect password')
            logging.warn('Attempted to log into Admin console with wrong password -- not allowed')
    return render_template('admin.html')

@app.route('/manage_photos')
def manage_photos():
    if not session.get('authenticated'):
        return redirect(url_for('admin'))

    files = {folder: os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], folder)) for folder in app.config['SUBFOLDERS']}
    return render_template('manage_photos.html', files=files)

@app.route('/uploads/<folder_name>/<filename>')
def serve_image(folder_name, filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    return send_from_directory(folder_path, filename)

@app.route('/download/<folder_name>/<filename>')
def download_image(folder_name, filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    
    @after_this_request
    def set_download_headers(response):
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    
    return send_from_directory(folder_path, filename, as_attachment=True)

@app.route('/delete_photo/<folder_name>/<filename>')
def delete_photo(folder_name, filename):
    if not session.get('authenticated'):
        flash('You need to login first')
        return redirect(url_for('admin'))

    if folder_name not in app.config['SUBFOLDERS']:
        flash('Folder not allowed')
        return redirect(url_for('manage_photos'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'Successfully deleted {filename} from {folder_name}')
        logging.info(f'Successfully deleted {filename} from {folder_name}')
    else:
        flash('File not found')
    return redirect(url_for('manage_photos'))


@app.route('/view_album/<folder_name>')
def view_album(folder_name):
    if folder_name not in app.config['SUBFOLDERS']:
        flash('Album does not exist.')
        return redirect(url_for('index'))
    
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    files = os.listdir(folder_path)
    return render_template('view_album.html', folder=folder_name, files=files)


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(message)s'
    logging.basicConfig(format=FORMAT,level=logging.INFO)

    # app.run(debug=True, port=7043)
    app.run(host='0.0.0.0', port=7043)