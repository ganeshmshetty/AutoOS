import os
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from deepface import DeepFace

router = APIRouter(prefix="/api/face-auth", tags=["Face Auth"])

# Directory to store face data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MASTER_FACE_PATH = os.path.join(DATA_DIR, "master_face.jpg")
TEMP_VERIFY_PATH = os.path.join(DATA_DIR, "temp_verify.jpg")

class FaceImage(BaseModel):
    image_base64: str

@router.get("/status")
def get_status():
    """Check if a master face is registered."""
    return {"registered": os.path.exists(MASTER_FACE_PATH)}

@router.post("/register")
def register_face(data: FaceImage):
    """Save the provided face as the master face."""
    try:
        # Decode base64 image
        header, encoded = data.image_base64.split(",", 1) if "," in data.image_base64 else ("", data.image_base64)
        image_data = base64.b64decode(encoded)
        
        with open(MASTER_FACE_PATH, "wb") as f:
            f.write(image_data)
            
        # Try to detect a face to ensure it's valid
        try:
            DeepFace.extract_faces(MASTER_FACE_PATH)
        except ValueError:
            os.remove(MASTER_FACE_PATH)
            raise HTTPException(status_code=400, detail="No face detected in the image. Please try again.")
            
        return {"success": True, "message": "Face registered successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Failed to register face: {str(e)}")

@router.post("/verify")
def verify_face(data: FaceImage):
    """Verify the provided face against the master face."""
    if not os.path.exists(MASTER_FACE_PATH):
        raise HTTPException(status_code=400, detail="No face registered yet")
        
    try:
        # Decode base64 image
        header, encoded = data.image_base64.split(",", 1) if "," in data.image_base64 else ("", data.image_base64)
        image_data = base64.b64decode(encoded)
        
        with open(TEMP_VERIFY_PATH, "wb") as f:
            f.write(image_data)
            
        # Verify using DeepFace
        result = DeepFace.verify(
            img1_path=TEMP_VERIFY_PATH,
            img2_path=MASTER_FACE_PATH,
            enforce_detection=False # Don't crash if face is slightly out of frame
        )
        
        # Clean up temp file
        if os.path.exists(TEMP_VERIFY_PATH):
            os.remove(TEMP_VERIFY_PATH)
            
        is_match = result.get("verified", False)
        return {
            "success": True,
            "verified": bool(is_match),
            "distance": result.get("distance"),
            "threshold": result.get("threshold")
        }
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(TEMP_VERIFY_PATH):
            os.remove(TEMP_VERIFY_PATH)
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")
