print("Starting import test...")
try:
    import motor
    print("motor imported")
except ImportError as e:
    print(f"motor failed: {e}")

try:
    import numpy
    print(f"numpy imported: {numpy.__version__}")
except ImportError as e:
    print(f"numpy failed: {e}")

try:
    import dlib
    print(f"dlib imported: {dlib.__version__}")
except ImportError as e:
    print(f"dlib failed: {e}")

try:
    import face_recognition
    print(f"face_recognition imported: {face_recognition.__version__}")
except ImportError as e:
    print(f"face_recognition failed: {e}")
except Exception as e:
    print(f"face_recognition error: {e}")
