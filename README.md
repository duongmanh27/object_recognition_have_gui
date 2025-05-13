YOLOv8 + Flask + Tkinter Image App
A GUI-based application that uses YOLOv8 for object detection from live camera, images, or video, with options to save and manage processed images via a Flask API and SQLite.

🚀 Features
  - Real-time object detection using YOLOv8.
  - User interface built with Tkinter.
  - Save processed images to SQLite via Flask API.
  - View and delete saved images by ID.
    
🛠️ Setup
Clone the repository:
   git clone https://github.com/your-username/your-repo-name.git
   cd object_recognition_have_gui
   pip install -r requirements.txt

▶️ Run the App
1. Start the Flask API server:
    python call_api.py
2. Start the main GUI:
   python main.py

📁 Project Structure
  ├── call_api.py        # Flask API for image upload and management
  ├── main.py            # Main GUI + YOLOv8 inference
  ├── saved_images/      # (Optional) Background or UI images
  ├── images.db          # SQLite database (auto-created)
  ├── requirements.txt   # Required dependencies
