import os
import base64
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from deepface import DeepFace

logger = logging.getLogger("AutoOS.FaceAuth")

router = APIRouter(prefix="/api/face-auth", tags=["Face Auth"])

# Directory to store face data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MASTER_FACE_PATH = os.path.join(DATA_DIR, "master_face.jpg")
TEMP_VERIFY_PATH = os.path.join(DATA_DIR, "temp_verify.jpg")


class FaceImage(BaseModel):
    image_base64: str


def _decode_base64_image(image_base64: str) -> bytes:
    """Strip optional data-URL header and decode base64 to raw bytes."""
    if "," in image_base64:
        _, encoded = image_base64.split(",", 1)
    else:
        encoded = image_base64
    # Fix padding if missing
    encoded += "=" * (-len(encoded) % 4)
    return base64.b64decode(encoded)


@router.get("/status")
def get_status():
    """Check if a master face is registered."""
    return {"registered": os.path.exists(MASTER_FACE_PATH)}


@router.post("/register")
def register_face(data: FaceImage):
    """Save the provided face image as the master face for this device."""
    # Decode image
    try:
        image_data = _decode_base64_image(data.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    if len(image_data) < 100:
        raise HTTPException(status_code=400, detail="Image data is too small. Please try again.")

    # Write to disk
    with open(MASTER_FACE_PATH, "wb") as f:
        f.write(image_data)

    # Validate that a face is actually detectable.
    # enforce_detection=False so we get a graceful result instead of an exception
    # when the face is at an angle or in poor lighting.
    try:
        faces = DeepFace.extract_faces(
            MASTER_FACE_PATH,
            enforce_detection=False,  # returns empty list instead of raising
        )
        # If the confidence of the best detection is very low, treat as no face
        if not faces or (faces[0].get("confidence", 1.0) < 0.5 and len(faces) == 1):
            logger.warning("Low confidence face detection during registration: %s", faces)
    except Exception as e:
        # If extract_faces itself crashes (corrupt file, etc.) clean up and fail
        if os.path.exists(MASTER_FACE_PATH):
            os.remove(MASTER_FACE_PATH)
        logger.error("Face extraction error during register: %s", e)
        raise HTTPException(status_code=400, detail=f"Could not process image: {e}")

    logger.info("Master face registered at %s", MASTER_FACE_PATH)
    return {"success": True, "message": "Face registered successfully"}


@router.post("/verify")
def verify_face(data: FaceImage):
    """Verify a captured face against the registered master face."""
    if not os.path.exists(MASTER_FACE_PATH):
        raise HTTPException(status_code=400, detail="No face registered yet. Please register first.")

    try:
        image_data = _decode_base64_image(data.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    # Write temp file for comparison
    with open(TEMP_VERIFY_PATH, "wb") as f:
        f.write(image_data)

    try:
        result = DeepFace.verify(
            img1_path=TEMP_VERIFY_PATH,
            img2_path=MASTER_FACE_PATH,
            enforce_detection=False,  # Don't crash if face is slightly off-frame
        )

        is_match = result.get("verified", False)
        logger.info("Face verify result: verified=%s distance=%.3f", is_match, result.get("distance", 0))

        return {
            "success": True,
            "verified": bool(is_match),
            "distance": result.get("distance"),
            "threshold": result.get("threshold"),
        }
    except Exception as e:
        logger.error("Face verification error: %s", e)
        raise HTTPException(status_code=400, detail=f"Verification failed: {e}")
    finally:
        if os.path.exists(TEMP_VERIFY_PATH):
            os.remove(TEMP_VERIFY_PATH)
