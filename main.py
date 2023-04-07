from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from PIL import Image#, ImageDraw, ImageFont
import os, io
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from moviepy.editor import ImageClip, CompositeVideoClip, VideoFileClip

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Required for Flask-Login

login_manager = LoginManager()
login_manager.init_app(app)

# Mock user data for this example
USERS = {
    '1': {'id': '1', 'username': 'admin', 'password': '!38N04SW5W*yG!z4'}

}

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = USERS[id]['username']
        self.password = USERS[id]['password']

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password are valid
        user_data = next((user for user in USERS.values() if user['username'] == username), None)
        if user_data and user_data['password'] == password:
            # Log the user in
            user = User(user_data['id'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    else:
        return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # get the uploaded file
    file = request.files['file']

    # set the filename and path
    filename = file.filename
    filepath = os.path.join(app.root_path, 'static/uploads', filename)

    # save the file to the server
    file.save(filepath)

    # open the image using Pillow
    img = Image.open(filepath)

    # get the image size
    width, height = img.size
    #img_size = max(width, height)
    img = img.resize((1080, 1080), resample=Image.LANCZOS)
    '''
    # set the text and font for the watermark
    text = 'Adorav'
    font = ImageFont.truetype('arial.ttf', 36)

    # create a new image for the watermark
    mark = Image.new('RGBA', img.size, (255, 255, 255, 0))

    # draw the text on the watermark image
    draw = ImageDraw.Draw(mark)
    textwidth, textheight = draw.textsize(text, font)
    x = (width - textwidth) / 3
    y = (height - textheight) / 4
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))

    # add the watermark to the original image
    img.paste(mark, None, mark)
    '''
    # create a watermark image
    watermark = Image.open(app.root_path + '/static/watermark1.png').convert('RGBA')

    logo_width, logo_height = watermark.size
    #watermark = watermark.resize((img_size // 3, (logo_height*img_size) // (logo_width*3)))
    logo_width, logo_height = watermark.size
    white_image = Image.new('RGBA', watermark.size, (255, 255, 255, 0))
    white_image.paste(watermark, (0, 0), mask=watermark.split()[3])
    # create a new image with the same size as the original image
    #new_img = Image.new(mode='RGBA', size=(logo_width, logo_height), color=(255, 255, 255, 0))

    # paste the original image onto the new image
    #new_img.paste(img, (0, 0))

    # add the watermark to the new image
    #alpha = 0.1  # set the opacity of the watermark to 50%

    #new_img.alpha_composite(watermark, dest=(10, height - watermark.height - 10)) #, alpha=alpha
    #new_img = Image.blend(im1=new_img, im2=watermark, alpha=alpha)
    #blended = Image.blend(new_img, watermark, alpha)
    #img.paste(blended, (10, height - watermark.height))

    #alpha = Image.new('L', (watermark.width, watermark.height), int(255*opacity))
    #watermark.putalpha(alpha)
    opacity = 0.65
    r, g, b, a = watermark.split()
    a = a.point(lambda i: i * opacity)
    watermark = Image.merge('RGBA', (r, g, b, a))
    #watermark.putalpha(a)
    #mask = a
    img.paste(watermark, (0,0),mask=watermark.split()[3]) #5 + (width//11), height-watermark.height-(height//3)

    # add the logo to the image
    logo = Image.open(app.root_path + '/static/logo3.png', mode='r')
    logo_width, logo_height = logo.size

    #logo = logo.resize((img_size // 3, (logo_height*img_size) // (logo_width*3)), resample=Image.LANCZOS)  # resize the logo to half its original size
    img.paste(logo, (0, 0), logo)
    img = img.convert('RGB')
    os.remove(filepath)
    filepath = f"{filepath}.jpeg"
    # save the new image
    img.save(filepath, format='JPEG')#

    return redirect(url_for('download', filename=filename))

@app.route('/download/<filename>')
def download(filename):
    # set the file path
    filepath = os.path.join(app.root_path, 'static/uploads', f"{filename}.jpeg" )

    # create a file-like object in memory
    file_stream = io.BytesIO()

    # open the image file and write it to the file stream
    with open(filepath, 'rb') as file:
        file_stream.write(file.read())

    # set the file stream's position back to the beginning
    file_stream.seek(0)

    # delete the file from the server
    os.remove(filepath)
    #filename = filename.replace("")
    # return the file stream as a download
    return send_file(file_stream, download_name=f"{filename}.jpeg", as_attachment=True)

# ----- Video Composting
LOGO_PATH = app.root_path + '/static/vid_logo.png' # 'logo.png'
WATERMARK_PATH = app.root_path + '/static/vid_wm.png' # 'watermark.png'

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mpeg', 'mov'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def add_logo(clip, logo_path):
    logo = ImageClip(logo_path).set_duration(clip.duration)#.resize(height=clip.h // 8)#
    return CompositeVideoClip([clip, logo.set_position(('left', 'top'))])


def add_watermark(clip, watermark_path):
    watermark = ImageClip(watermark_path).set_duration(clip.duration).set_opacity(0.3)#.resize(height=clip.h // 6)
    return CompositeVideoClip([clip, watermark.set_position(('left', 'top'))])


@app.route('/video', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename #secure_filename(file.filename)
            filepath = os.path.join(app.root_path, 'static/uploads', filename)

            # save the file to the server
            file.save(filepath)
            video = VideoFileClip(filepath)
            logoed_video = add_logo(video, LOGO_PATH)
            watermarked_video = add_watermark(logoed_video, WATERMARK_PATH)
            new_filename = filename.split(' ')[0] + '.mp4'
            new_path = os.path.join(app.root_path, 'static/uploads', new_filename)
            watermarked_video.write_videofile(new_path, codec='libx264')
            os.remove(filepath)
            # create a file-like object in memory
            file_stream = io.BytesIO()
            # open the image file and write it to the file stream
            with open(new_path, 'rb') as file:
                file_stream.write(file.read())

            # set the file stream's position back to the beginning
            file_stream.seek(0)


            # delete the file from the server
            #os.remove(new_path)
            return send_file(file_stream, as_attachment=True,
                             download_name=new_filename, mimetype='video/mp4')
    #return

if __name__ == '__main__':
    app.run(host="0.0.0.0")
