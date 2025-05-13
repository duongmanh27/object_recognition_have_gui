import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import requests
import os
import base64
import numpy as np

from ultralytics import YOLO
import torch

# --- CẤU HÌNH & KHỞI TẠO MODEL ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model = YOLO("yolov8s.pt")
model.eval()
names_class = model.names

# Địa chỉ Flask API
API_UPLOAD_URL = "http://127.0.0.1:5000/upload"
API_IMAGES_URL = "http://127.0.0.1:5000/images"

# Biến toàn cục cho camera và video
cap = None          # Camera live
cap_video = None    # Video từ file
stop = False
current_frame = None
camera_running = False  # flag kiểm tra camera có đang chạy hay không
paused = False

# --- TẠO GIAO DIỆN TKINTER ---
root = tk.Tk()
root.geometry("1140x720")
root.title("YOLOv8 + DB Demo")
bg_img = Image.open("E:\\Code\\Python\\CNPM\\saved_images\\4092785.jpg")  # Thay bằng ảnh nền của bạn
bg_img = bg_img.resize((1140,720))
bg_photo = ImageTk.PhotoImage(bg_img)
# Danh sách để giữ tham chiếu ảnh hiển thị
saved_photos = []

# --- HÀM XỬ LÝ ẢNH VỚI YOLOv8 ---
def run_detection_on_frame(frame):
    results = model(frame)
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0].item())
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, names_class[cls], (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return frame

# --- HIỂN THỊ ẢNH TRÊN LABEL CHÍNH ---
def show_image(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb)
    # Lấy kích thước hiện tại của widget hiển thị ảnh
    frame_width = image_label.winfo_width()
    frame_height = image_label.winfo_height()

    # Nếu kích thước hợp lệ, resize ảnh giữ tỉ lệ ban đầu
    if frame_width > 0 and frame_height > 0:
        img.thumbnail((frame_width, frame_height), Image.Resampling.LANCZOS)

    imgtk = ImageTk.PhotoImage(image=img)
    image_label.config(image=imgtk)
    image_label.image = imgtk

# --- DỪNG TẤT CẢ CHẾ ĐỘ (CAMERA & VIDEO) ---
def stop_all_modes():
    global cap, cap_video, paused
    # Nếu đang chạy camera, giải phóng nó
    if cap is not None and cap.isOpened():
        paused = True
        cap.release()
        cap = None
    # Nếu đang chạy video, giải phóng nó
    if cap_video is not None and cap_video.isOpened():
        paused = True
        cap_video.release()
        cap_video = None
    # Xoá hiển thị chế độ hiện tại (đặt lại với ảnh nền)
    image_label.config(image=bg_photo)
    image_label.image = bg_photo  # Giữ tham chiếu đến ảnh nền

def stop_camera_func():
    global paused, camera_running
    paused = True
    camera_running = False
    # Không giải phóng cap hoặc cap_video để giữ nguồn cho Resume

def resume_processing():
    global paused
    if paused:
        paused = False
        if cap_video is not None and cap_video.isOpened():
            update_video()  # Tiếp tục phát video
        elif cap is not None and cap.isOpened():
            update_frame()  # Tiếp tục camera live

 # Tiếp tục camera live


# --- CHUYỂN VỀ CHẾ ĐỘ HIỂN THỊ CHÍNH ---
def back_to_main():
    """
    Ẩn frame xem ảnh đã lưu (nếu đang hiển thị),
    và hiển thị lại Label chính (image_label).
    """
    saved_images_frame.pack_forget()
    image_label.pack(fill=tk.BOTH, expand=True)

# -------------------------
# CÁC HÀM CHUYỂN CHẾ ĐỘ
# -------------------------

def select_image():
    stop_all_modes()
    back_to_main()
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg;*.png;*.jpeg")]
    )
    if file_path:
        frame = cv2.imread(file_path)
        frame = run_detection_on_frame(frame)
        show_image(frame)

def select_folder():
    stop_all_modes()
    back_to_main()
    folder_path = filedialog.askdirectory()
    if folder_path:
        image_paths = [os.path.join(folder_path, f)
                       for f in os.listdir(folder_path)
                       if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        image_paths.sort()  # Sắp xếp đường dẫn nếu cần
        show_folder_images(image_paths, 0)

def show_folder_images(paths, index):
    if index < len(paths):
        frame = cv2.imread(paths[index])
        frame = run_detection_on_frame(frame)
        show_image(frame)
        # Sau 1000ms, gọi lại hàm với ảnh kế tiếp
        root.after(1000, lambda: show_folder_images(paths, index + 1))
 # Tạm dừng 1 giây xem từng ảnh

def select_video():
    global cap_video, paused
    stop_all_modes()
    back_to_main()
    file_path = filedialog.askopenfilename(
        filetypes=[("Video files", "*.mp4;*.avi;*.mov;*.mkv")]
    )
    if not file_path:
        return
    paused = False  # Đảm bảo không bị tạm dừng
    cap_video = cv2.VideoCapture(file_path)
    update_video()


def start_camera():
    global cap, paused, camera_running
    stop_all_modes()
    back_to_main()
    if camera_running:
        return
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    paused = False  # Đảm bảo không bị tạm dừng
    camera_running = True
    update_frame()


# -------------------------
# HÀM CẬP NHẬT VIDEO & CAMERA
# -------------------------

def update_video():
    global cap_video, current_frame
    if cap_video is not None and cap_video.isOpened() and not paused:
        ret, frame = cap_video.read()
        if ret:
            frame = run_detection_on_frame(frame)
            current_frame = frame.copy()
            show_image(frame)
            root.after(30, update_video)  # 30ms gọi lại
        else:
            cap_video.release()
            cap_video = None

 # Đảm bảo cap_video được giải phóng khi stop


def update_frame():
    global cap, current_frame, camera_running
    if cap and cap.isOpened() and not paused:
        ret, frame = cap.read()
        if ret:
            frame_proc = run_detection_on_frame(frame)
            current_frame = frame_proc.copy()
            show_image(frame_proc)
        root.after(10, update_frame)
    else:
        camera_running = False
        if cap:
            cap.release()



# -------------------------
# HÀM CHỤP ẢNH & XEM ẢNH ĐÃ LƯU
# -------------------------

def capture_image():
    global current_frame
    if current_frame is not None:
        retval, buffer = cv2.imencode('.jpg', current_frame)
        files = {'image': ('capture.jpg', buffer.tobytes(), 'image/jpeg')}
        try:
            response = requests.post(API_UPLOAD_URL, files=files)
            if response.status_code == 200:
                messagebox.showinfo("Info",
                                    f"Image captured and saved to DB.\nServer response: {response.text}")
            else:
                messagebox.showerror("Error", f"Server error: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", "No frame available!")

def view_saved_images():
    stop_all_modes()
    image_label.pack_forget()
    for widget in saved_images_frame.winfo_children():
        widget.destroy()
    saved_photos.clear()
    try:
        r = requests.get(API_IMAGES_URL)
        if r.status_code == 200:
            data = r.json()  # list of {"id":..., "data": base64_string}
            if not data:
                messagebox.showinfo("Info", "No saved images found in DB!")
            else:
                # Tạo canvas + scrollbar dọc để hiển thị lưới ảnh
                scroll_canvas = tk.Canvas(saved_images_frame)
                scrollbar = tk.Scrollbar(saved_images_frame, orient="vertical",
                                         command=scroll_canvas.yview)
                scroll_canvas.configure(yscrollcommand=scrollbar.set)

                images_container = tk.Frame(scroll_canvas)
                scroll_canvas.create_window((0, 0), window=images_container, anchor="nw")
                scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                columns = 5
                row_i = 0
                col_i = 0

                for idx, item in enumerate(data):
                    b64_str = item["data"]
                    img_id = item["id"]
                    raw_data = base64.b64decode(b64_str)
                    np_arr = np.frombuffer(raw_data, np.uint8)
                    img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    pil_img.thumbnail((200, 200))  # Thu nhỏ ảnh
                    photo = ImageTk.PhotoImage(pil_img)
                    lbl = tk.Label(images_container, image=photo,
                                   text=f"ID: {img_id}", compound=tk.TOP)
                    lbl.image = photo  # giữ tham chiếu
                    lbl.grid(row=row_i, column=col_i, padx=10, pady=10)
                    saved_photos.append(photo)
                    lbl.img_id = img_id
                    lbl.full_pil_img = Image.fromarray(img_rgb)  # Ảnh gốc (chưa thumbnail)

                    # Bắt sự kiện double-click
                    lbl.bind("<Double-Button-1>", on_double_click)
                    # Bắt sự kiện right-click
                    lbl.bind("<Button-3>", on_right_click)

                    col_i += 1
                    if col_i >= columns:
                        col_i = 0
                        row_i += 1

                images_container.update_idletasks()
                scroll_canvas.config(scrollregion=scroll_canvas.bbox("all"))
        else:
            messagebox.showerror("Error", f"Failed to fetch images: {r.text}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

    # Hiển thị khung chứa danh sách ảnh đã lưu
    saved_images_frame.pack(fill=tk.BOTH, expand=True)

# -------------------------
# HÀM XỬ LÝ SỰ KIỆN CLICK LÊN ẢNH
# -------------------------
def on_double_click(event):
    """Mở ảnh lớn trong cửa sổ mới khi double-click vào Label."""
    lbl = event.widget
    full_img = lbl.full_pil_img  # Ảnh PIL gốc

    # Tạo cửa sổ mới để hiển thị ảnh lớn
    top = tk.Toplevel(root)
    top.title(f"Image ID: {lbl.img_id}")

    # Resize ảnh nếu muốn, ở đây giữ nguyên
    img_w, img_h = full_img.size
    max_w, max_h = 800, 600
    if img_w > max_w or img_h > max_h:
        full_img.thumbnail((max_w, max_h))

    photo_big = ImageTk.PhotoImage(full_img)
    lbl_big = tk.Label(top, image=photo_big)
    lbl_big.image = photo_big
    lbl_big.pack()

def on_right_click(event):
    """Hiển thị menu chuột phải, cho phép xóa ảnh."""
    lbl = event.widget
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Delete Image", command=lambda: delete_image(lbl.img_id))
    menu.post(event.x_root, event.y_root)

def delete_image(img_id):
    """Gửi yêu cầu xóa ảnh lên server, rồi load lại danh sách ảnh."""
    confirm = messagebox.askyesno("Confirm", f"Are you sure to delete image ID: {img_id}?")
    if not confirm:
        return

    # Gửi lệnh xóa
    delete_url = f"http://127.0.0.1:5000/delete/{img_id}"
    try:
        r = requests.delete(delete_url)
        if r.status_code == 200:
            messagebox.showinfo("Info", r.text)
            # Sau khi xóa xong, load lại danh sách ảnh
            view_saved_images()
        else:
            messagebox.showerror("Error", f"Delete failed: {r.text}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Frame chứa các nút bấm
button_frame = tk.Frame(root, bg="lightgray")
button_frame.pack(side=tk.TOP, fill=tk.X)

btn_select_image = tk.Button(button_frame, text="Select Image", command=select_image)
btn_select_image.pack(side=tk.LEFT, padx=5, pady=5)

btn_select_folder = tk.Button(button_frame, text="Select Folder", command=select_folder)
btn_select_folder.pack(side=tk.LEFT, padx=5, pady=5)

btn_select_video = tk.Button(button_frame, text="Select Video", command=select_video)
btn_select_video.pack(side=tk.LEFT, padx=5, pady=5)

btn_camera = tk.Button(button_frame, text="Live Camera", command=start_camera)
btn_camera.pack(side=tk.LEFT, padx=5, pady=5)

btn_stop = tk.Button(button_frame, text="Stop", command=stop_camera_func)
btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

btn_resume = tk.Button(button_frame, text="Resume", command=resume_processing)
btn_resume.pack(side=tk.LEFT, padx=5, pady=5)


btn_capture = tk.Button(button_frame, text="Capture Image", command=capture_image)
btn_capture.pack(side=tk.LEFT, padx=5, pady=5)

btn_view = tk.Button(button_frame, text="View Saved Images", command=view_saved_images)
btn_view.pack(side=tk.LEFT, padx=5, pady=5)

image_label = tk.Label(root, image=bg_photo)
image_label.pack(fill=tk.BOTH, expand=True)

# Frame chứa danh sách ảnh đã lưu (mặc định không được hiển thị)
saved_images_frame = tk.Frame(root, bg="lightgray")

root.mainloop()
