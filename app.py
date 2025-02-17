from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder=None)  # 禁用默认的静态文件夹
UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
# 创建必要的目录
for folder in [UPLOAD_FOLDER, COMPRESSED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# 添加压缩文件的静态服务路由
@app.route('/compressed/<path:filename>')
def download_file(filename):
    response = send_from_directory(COMPRESSED_FOLDER, filename)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    # 确保文件名是安全的
    filename = secure_filename(file.filename)

    # 获取用户设置的分辨率
    width = request.form.get('width', type=int)
    height = request.form.get('height', type=int)

    # 保存上传的文件
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # 压缩图片
    compressed_filename = 'compressed_' + filename

    # 获取保存路径
    save_path = request.form.get('save_path')
    if save_path and os.path.isdir(save_path):
        compressed_path = os.path.join(save_path, compressed_filename)
    else:
        compressed_path = os.path.join(COMPRESSED_FOLDER, compressed_filename)

    with Image.open(file_path) as img:
        original_width, original_height = img.size
        new_width, new_height = original_width, original_height

        if width and height:
            new_width, new_height = width, height
        elif width:
            ratio = width / original_width
            new_width = width
            new_height = int(original_height * ratio)
        elif height:
            ratio = height / original_height
            new_height = height
            new_width = int(original_width * ratio)

        # 只有在需要调整大小时才进行resize
        if (new_width, new_height) != (original_width, original_height):
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        img.save(compressed_path, "JPEG", quality=70)

    # 返回可访问的URL
    download_url = f'/compressed/{compressed_filename}'
    return jsonify({
        'message': f'文件已压缩 ({new_width}x{new_height})', 
        'compressed_file': download_url
    }), 200

@app.route('/clear-images', methods=['POST'])
def clear_images():
    try:
        # 清空上传和压缩文件夹
        for folder in [UPLOAD_FOLDER, COMPRESSED_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f'Error deleting {file_path}: {e}')
        
        return jsonify({
            'message': '所有图片已清除'
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
