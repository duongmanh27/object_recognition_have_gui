from flask import Flask, request, jsonify
import os
import sqlite3
import base64


app = Flask(__name__)

DB_NAME = 'images.db'


def init_db() :
    """Tạo bảng images nếu chưa tồn tại"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/upload', methods=['POST'])
def upload() :
    """Nhận file ảnh qua POST, lưu vào DB"""
    if 'image' not in request.files :
        return "No image file", 400

    file = request.files['image']
    image_data = file.read()
    # Lưu vào DB dưới dạng BLOB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO images (data) VALUES (?)', (image_data,))
    conn.commit()
    conn.close()

    return "Image saved to DB", 200


@app.route('/images', methods=['GET'])
def get_images() :
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, data FROM images')
    rows = c.fetchall()
    conn.close()

    # Mỗi ảnh được trả về dưới dạng {"id":..., "data":...} với data là base64
    images_list = []
    for row in rows :
        img_id = row[0]
        blob_data = row[1]
        # Chuyển blob -> base64 string
        b64_data = base64.b64encode(blob_data).decode('utf-8')
        images_list.append({"id" : img_id, "data" : b64_data})

    return jsonify(images_list)

@app.route('/delete/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM images WHERE id=?', (image_id,))
    conn.commit()
    conn.close()
    return f"Image with id {image_id} deleted", 200

if __name__ == '__main__' :
    init_db()
    app.run(debug=True)
