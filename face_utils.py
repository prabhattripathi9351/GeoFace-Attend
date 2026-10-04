from PIL import Image, ImageOps
import face_recognition
import numpy as np
import io


def extract_embedding(image_bytes):
    """Single photo se 128-point face embedding"""
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)

        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        img_array = np.array(pil_image)

        h, w = img_array.shape[:2]
        if w > 800:
            scale = 800 / w
            img_array = np.array(pil_image.resize((800, int(h * scale))))

        face_locations = face_recognition.face_locations(img_array, model="hog")
        if not face_locations:
            return None

        face_encodings = face_recognition.face_encodings(img_array, face_locations)
        if not face_encodings:
            return None

        return face_encodings[0].tolist()
    except Exception as e:
        print(f"Embedding extract error: {e}")
        return None


def match_face(stored_embedding, new_embedding, tolerance=0.6):
    """Do embeddings compare karta hai"""
    if stored_embedding is None or new_embedding is None:
        return False
    try:
        matches = face_recognition.compare_faces(
            [np.array(stored_embedding)],
            np.array(new_embedding),
            tolerance=tolerance
        )
        return matches[0]
    except:
        return False


def detect_face(image_bytes):
    """Check karta hai face hai ya nahi"""
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)
        img_array = np.array(pil_image)
        face_locations = face_recognition.face_locations(img_array)
        return len(face_locations) > 0
    except:
        return False


def detect_all_faces(image_bytes):
    """
    Group photo mein saare faces detect karta hai.
    Photo galat orientation mein ho sakti hai, isliye 0/90/180/270
    sab angles try karte hain aur jisme sabse zyada faces milein
    wahi use karte hain.
    """
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)

        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        w, h = pil_image.size
        if w > 1200:
            scale = 1200 / w
            pil_image = pil_image.resize((1200, int(h * scale)), Image.LANCZOS)

        best_locations = []
        best_img_array = None
        best_angle = 0

        for angle in [0, 90, 180, 270]:
            rotated = pil_image.rotate(-angle, expand=True)
            img_array = np.array(rotated)

            face_locations = face_recognition.face_locations(
                img_array, number_of_times_to_upsample=1, model="hog"
            )
            print(f"[DEBUG] Angle {angle}: {len(face_locations)} faces")

            if len(face_locations) > len(best_locations):
                best_locations = face_locations
                best_angle = angle
                best_img_array = img_array

            if len(face_locations) >= 2:
                break

        print(f"[DEBUG] Best angle: {best_angle}, faces: {len(best_locations)}")

        if best_locations:
            best_encodings = face_recognition.face_encodings(best_img_array, best_locations)
            print(f"[DEBUG] Encodings ready: {len(best_encodings)}")
            return best_locations, best_encodings

        return [], []

    except Exception as e:
        print(f"[DEBUG] ERROR: {e}")
        return [], []


def match_against_database(face_encodings, all_students, tolerance=0.6):
    """
    Faces ko database se match karta hai (tolerance 0.6 = better match)
    """
    matched = []
    unmatched = []
    used_roll_nos = set()

    print(f"[DEBUG] Matching {len(face_encodings)} faces against {len(all_students)} students")

    for i, encoding in enumerate(face_encodings):
        best_match = None
        best_distance = 1.0

        for student in all_students:
            stored = student.get('face_embedding')
            if not stored:
                continue

            if student['roll_no'] in used_roll_nos:
                continue

            try:
                stored_arr = np.array(stored)
                distance = face_recognition.face_distance([stored_arr], encoding)[0]
                print(f"[DEBUG] Face {i+1} vs {student['roll_no']}: distance = {distance:.3f}")

                if distance < best_distance:
                    best_distance = distance
                    best_match = student
            except Exception as e:
                print(f"[DEBUG] Error: {e}")
                continue

        if best_match and best_distance <= tolerance:
            matched.append({
                'student': best_match,
                'distance': float(best_distance)
            })
            used_roll_nos.add(best_match['roll_no'])
            print(f"[DEBUG] ✅ Face {i+1} matched: {best_match['name']} (dist={best_distance:.3f})")
        else:
            unmatched.append(i)
            if best_match:
                print(f"[DEBUG] ❌ Face {i+1} best was {best_match['name']} but dist={best_distance:.3f} > {tolerance}")
            else:
                print(f"[DEBUG] ❌ Face {i+1} no match found")

    return matched, unmatched