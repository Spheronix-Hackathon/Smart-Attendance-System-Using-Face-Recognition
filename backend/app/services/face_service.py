from __future__ import annotations

import base64
import io
from typing import Any

from fastapi import HTTPException

from ..config import settings

try:
    import face_recognition
    import numpy as np
    FACE_AVAILABLE = True
except Exception as exc:  # pragma: no cover - import guard
    FACE_AVAILABLE = False
    _FACE_ERROR = exc


def get_face_recognition_status() -> dict[str, bool | str | None]:
    return {
        "available": FACE_AVAILABLE,
        "error": None if FACE_AVAILABLE else str(_FACE_ERROR),
    }


def _decode_image(image_data: str):
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    try:
        raw = base64.b64decode(image_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image data") from exc
    return face_recognition.load_image_file(io.BytesIO(raw))


async def extract_encoding(image_data: str) -> list[float]:
    if not FACE_AVAILABLE:
        raise HTTPException(status_code=503, detail=f"Face recognition unavailable: {_FACE_ERROR}")

    image = _decode_image(image_data)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) == 0:
        raise HTTPException(status_code=400, detail="No face detected. Please try again.")
    if len(encodings) > 1:
        raise HTTPException(status_code=400, detail="Multiple faces detected. Please ensure only one face is visible.")
    return encodings[0].tolist()


async def extract_multiple_encodings(image_data: str) -> list[list[float]]:
    if not FACE_AVAILABLE:
        raise HTTPException(status_code=503, detail=f"Face recognition unavailable: {_FACE_ERROR}")

    image = _decode_image(image_data)
    encodings = face_recognition.face_encodings(image)
    return [e.tolist() for e in encodings]


def _as_vector(face_encoding: Any):
    return np.array(face_encoding, dtype=float)


def compare_encoding(candidate: list[float], known: list[float]) -> float:
    if not FACE_AVAILABLE:
        return 1.0
    return float(face_recognition.face_distance([_as_vector(known)], _as_vector(candidate))[0])


async def find_best_match(candidate: list[float], users: list[dict]) -> dict | None:
    if not FACE_AVAILABLE:
        raise HTTPException(status_code=503, detail=f"Face recognition unavailable: {_FACE_ERROR}")

    best_user = None
    best_distance = 1.0
    for user in users:
        known = user.get("face_encoding") or []
        if not known:
            continue
        try:
            distance = compare_encoding(candidate, known)
        except Exception:
            continue
        if distance < best_distance:
            best_distance = distance
            best_user = {"user": user, "distance": distance}

    if best_user and best_user["distance"] <= settings.face_tolerance:
        return best_user
    return None


async def find_matches(candidates: list[list[float]], users: list[dict]) -> list[dict]:
    if not FACE_AVAILABLE:
        return []

    matches = []
    # Optimization: Convert all known face encodings to numpy arrays once
    known_users = []
    for u in users:
        if u.get("face_encoding"):
            known_users.append((u, _as_vector(u["face_encoding"])))

    if not known_users:
        return []

    for candidate in candidates:
        candidate_vec = _as_vector(candidate)
        best_user = None
        best_distance = 1.0

        for user, known_vec in known_users:
            distance = float(face_recognition.face_distance([known_vec], candidate_vec)[0])
            if distance < best_distance:
                best_distance = distance
                best_user = user

        if best_user and best_distance <= settings.face_tolerance:
            matches.append({"user": best_user, "distance": best_distance})

    return matches
