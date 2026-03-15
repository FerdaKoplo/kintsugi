import numpy as np
import uuid
from sqlalchemy.orm import Session
from app.schemas.schema import UserSkill, User, UserVerifyStatus

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    return float(EARTH_RADIUS_KM * c)


def haversine_batch(
    origin_lat: float,
    origin_lng: float,
    lats: np.ndarray,
    lngs: np.ndarray,
) -> np.ndarray:
    origin_lat, origin_lng = map(np.radians, [origin_lat, origin_lng])
    lats = np.radians(lats)
    lngs = np.radians(lngs)

    dlat = lats - origin_lat
    dlng = lngs - origin_lng

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(origin_lat) * np.cos(lats) * np.sin(dlng / 2) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))

    return EARTH_RADIUS_KM * c


class SkillMatchingService:
    def __init__(self, db: Session):
        self.db = db

    def match_fixers(
        self,
        required_skill: str,
        client_lat: float,
        client_lng: float,
        radius_km: float = 5.0,
    ) -> list[dict]:
        results = (
            self.db.query(UserSkill, User)
            .join(User, UserSkill.user_id == User.id)
            .filter(
                UserSkill.skill_name.ilike(f"%{required_skill}%"),
                UserSkill.verified_level == UserVerifyStatus.VERIFIED,
                User.latitude.isnot(None),
                User.longitude.isnot(None),
            )
            .all()
        )

        if not results:
            return []

        skills, users = zip(*results)
        lats = np.array([u.latitude for u in users])
        lngs = np.array([u.longitude for u in users])

        distances = haversine_batch(client_lat, client_lng, lats, lngs)

        matched = [
            {
                "user_id": users[i].id,
                "skill_name": skills[i].skill_name,
                "skill_level": skills[i].level,
                "distance_km": round(float(distances[i]), 2),
            }
            for i in np.where(distances <= radius_km)[0]
        ]

        return sorted(matched, key=lambda x: x["distance_km"])
