"""
AgriTwin Kullanıcı Kayıt, Giriş ve Yetkilendirme Motoru (Authentication & Identity Twin)
- Standart Güvenlik: PBKDF2-HMAC-SHA256 (100.000 iterasyon, kriptografik tuzlama),
- Çoklu Rol Desteği: Baş Veteriner Hekim, Çiftlik Müdürü, Enerji Mühendisi, Sürü Genetikçisi, Besleme Uzmanı,
- Çiftlik / İşletme Özelleştirmesi ve Oturum Yönetimi (Session Token).
"""

import os
import json
import secrets
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

ROLE_DETAILS = {
    "vet": {
        "title": "Baş Veteriner Hekim & Sürü Danışmanı",
        "avatar": "🩺",
        "department": "Sürü Sağlığı & Biyogüvenlik",
        "permissions": ["Reçete Yazma", "Karantina Kilidi", "Doğum & Distosi Müdahalesi", "Brix Kolostrum Onayı"]
    },
    "manager": {
        "title": "Çiftlik Müdürü & Kıdemli Zooteknist",
        "avatar": "🚜",
        "department": "Operasyon & TMR Rasyon Yönetimi",
        "permissions": ["Pareto Rasyon Uygulama", "Robot Filo Kontrolü", "Ayırma Kapısı Yönlendirme", "Finansal ROI"]
    },
    "energy": {
        "title": "Biyogaz & Kojenerasyon Baş Mühendisi",
        "avatar": "⚡",
        "department": "Döngüsel Ekonomi & Kojenerasyon (CHP)",
        "permissions": ["CHP Jeneratör Ayarı", "Biyogaz Basınç İzleme", "Şebeke Elektrik Satışı", "Karbon Kredisi"]
    },
    "genetics": {
        "title": "Genomik Damızlık & Islah Danışmanı",
        "avatar": "🧬",
        "department": "Genomik Damızlık & Akıllı Çiftleştirme",
        "permissions": ["Net Merit ($NM$) Seleksiyonu", "Akrabalık (Inbreeding) Denetimi", "Dişi Ayrıştırılmış Boğa Kataloğu"]
    },
    "nutritionist": {
        "title": "Sürü Besleme ve Rasyon Uzmanı",
        "avatar": "🌾",
        "department": "Besleme & Enterik Metan Azaltımı",
        "permissions": ["TMR Rasyon Optimizasyonu", "Rumen pH Takibi", "Yem Depo & Silo Yönetimi"]
    },
    "operator": {
        "title": "Çiftlik Otomasyon Teknisyeni",
        "avatar": "🔧",
        "department": "Teknik Bakım & Sensör Kalibrasyonu",
        "permissions": ["Cihaz Aktüatör Testi", "Sensör Kalibrasyonu", "RTLS Ağ Yönetimi"]
    }
}

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    role_title: str
    avatar: str
    farm_name: str
    department: str
    permissions: List[str]
    created_at: str
    last_login: Optional[str] = None

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: Optional[str] = "vet"
    farm_name: Optional[str] = "AgriTwin Akıllı Süt Çiftliği"

class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str
    remember_me: Optional[bool] = False

class AuthResponse(BaseModel):
    status: str
    message: str
    token: Optional[str] = None
    user: Optional[UserProfile] = None

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return key.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return secrets.compare_digest(key.hex(), password_hash)

class AuthManager:
    def __init__(self, db_path: str = "users_db.json"):
        self.db_path = db_path
        self.users: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, str] = {}  # token -> user_id
        self._current_user_id: str = "vet_01"  # default active
        self._load_or_seed()

    def _load_or_seed(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.users = data.get("users", {})
            except Exception as e:
                print(f"Auth DB read error: {e}, re-seeding.")
                self._seed_default_users()
        else:
            self._seed_default_users()

    def _save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({"users": self.users, "updated_at": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Auth DB write error: {e}")

    def _seed_default_users(self):
        default_accounts = [
            {
                "id": "vet_01",
                "username": "vet",
                "email": "vet@agritwin.com",
                "full_name": "Dr. Mehmet Yılmaz",
                "password": "demo123",
                "role": "vet",
                "farm_name": "AgriTwin Akıllı Çiftlik A.Ş."
            },
            {
                "id": "mgr_01",
                "username": "manager",
                "email": "manager@agritwin.com",
                "full_name": "Selim Aksoy",
                "password": "demo123",
                "role": "manager",
                "farm_name": "AgriTwin Akıllı Çiftlik A.Ş."
            },
            {
                "id": "eng_01",
                "username": "energy",
                "email": "energy@agritwin.com",
                "full_name": "Müh. Emre Demir",
                "password": "demo123",
                "role": "energy",
                "farm_name": "AgriTwin Akıllı Çiftlik A.Ş."
            },
            {
                "id": "gen_01",
                "username": "genetics",
                "email": "genetics@agritwin.com",
                "full_name": "Doç. Dr. Ayşe Kaya",
                "password": "demo123",
                "role": "genetics",
                "farm_name": "AgriTwin Akıllı Çiftlik A.Ş."
            }
        ]

        self.users = {}
        for acc in default_accounts:
            pwd_hash, salt = hash_password(acc["password"])
            role_meta = ROLE_DETAILS.get(acc["role"], ROLE_DETAILS["vet"])
            self.users[acc["id"]] = {
                "id": acc["id"],
                "username": acc["username"],
                "email": acc["email"].lower(),
                "password_hash": pwd_hash,
                "salt": salt,
                "full_name": acc["full_name"],
                "role": acc["role"],
                "role_title": role_meta["title"],
                "avatar": role_meta["avatar"],
                "farm_name": acc["farm_name"],
                "department": role_meta["department"],
                "permissions": role_meta["permissions"],
                "created_at": "2026-01-01T08:00:00",
                "last_login": datetime.now().isoformat()
            }
        self._save()

    def register_user(self, req: UserRegisterRequest) -> AuthResponse:
        username_clean = req.username.strip().lower()
        email_clean = req.email.strip().lower()

        # Validation
        if len(username_clean) < 3:
            return AuthResponse(status="error", message="Kullanıcı adı en az 3 karakter olmalıdır.")
        if "@" not in email_clean or "." not in email_clean:
            return AuthResponse(status="error", message="Lütfen geçerli bir e-posta adresi giriniz.")
        if len(req.password) < 6:
            return AuthResponse(status="error", message="Parola güvenlik gereği en az 6 karakter olmalıdır.")

        # Check existing username or email
        for uid, u in self.users.items():
            if u["username"].lower() == username_clean:
                return AuthResponse(status="error", message="Bu kullanıcı adı zaten kullanılmaktadır.")
            if u["email"].lower() == email_clean:
                return AuthResponse(status="error", message="Bu e-posta adresi ile kayıtlı bir hesap mevcuttur.")

        user_id = f"user_{secrets.token_hex(4)}"
        pwd_hash, salt = hash_password(req.password)
        role_key = req.role if req.role in ROLE_DETAILS else "vet"
        role_meta = ROLE_DETAILS[role_key]

        new_user = {
            "id": user_id,
            "username": req.username.strip(),
            "email": email_clean,
            "password_hash": pwd_hash,
            "salt": salt,
            "full_name": req.full_name.strip(),
            "role": role_key,
            "role_title": role_meta["title"],
            "avatar": role_meta["avatar"],
            "farm_name": req.farm_name.strip() if req.farm_name else "AgriTwin Akıllı Çiftlik",
            "department": role_meta["department"],
            "permissions": role_meta["permissions"],
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }

        self.users[user_id] = new_user
        self._save()

        token = f"agritwin_tk_{secrets.token_urlsafe(24)}"
        self.active_sessions[token] = user_id
        self._current_user_id = user_id

        user_profile = self._build_profile(new_user)
        return AuthResponse(
            status="success",
            message=f"Hesabınız başarıyla oluşturuldu. Hoş geldiniz, {req.full_name}!",
            token=token,
            user=user_profile
        )

    def login_user(self, req: UserLoginRequest) -> AuthResponse:
        query = req.username_or_email.strip().lower()
        matched_user = None

        for uid, u in self.users.items():
            if u["username"].lower() == query or u["email"].lower() == query:
                matched_user = u
                break

        if not matched_user:
            return AuthResponse(status="error", message="Kullanıcı bulunamadı. Lütfen bilgilerinizi kontrol ediniz.")

        if not verify_password(req.password, matched_user["password_hash"], matched_user["salt"]):
            return AuthResponse(status="error", message="Hatalı parola! Lütfen tekrar deneyiniz.")

        # Update last login
        matched_user["last_login"] = datetime.now().isoformat()
        self._save()

        token = f"agritwin_tk_{secrets.token_urlsafe(24)}"
        self.active_sessions[token] = matched_user["id"]
        self._current_user_id = matched_user["id"]

        user_profile = self._build_profile(matched_user)
        return AuthResponse(
            status="success",
            message=f"Giriş başarılı! Hoş geldiniz, {matched_user['full_name']}.",
            token=token,
            user=user_profile
        )

    def get_current_user(self, token: Optional[str] = None) -> Optional[UserProfile]:
        user_id = None
        if token and token in self.active_sessions:
            user_id = self.active_sessions[token]
        elif self._current_user_id and self._current_user_id in self.users:
            user_id = self._current_user_id

        if user_id and user_id in self.users:
            return self._build_profile(self.users[user_id])
        return None

    def switch_to_persona(self, persona_id: str) -> Optional[UserProfile]:
        """Demo profiline anında geçiş desteği"""
        target_uid = None
        for uid, u in self.users.items():
            if u["role"] == persona_id or u["username"] == persona_id:
                target_uid = uid
                break

        if target_uid:
            self._current_user_id = target_uid
            return self._build_profile(self.users[target_uid])
        return None

    def logout_user(self, token: Optional[str] = None) -> bool:
        if token and token in self.active_sessions:
            del self.active_sessions[token]
        # Keep guest or default
        return True

    def _build_profile(self, user_dict: Dict[str, Any]) -> UserProfile:
        return UserProfile(
            id=user_dict["id"],
            username=user_dict["username"],
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            role=user_dict["role"],
            role_title=user_dict["role_title"],
            avatar=user_dict["avatar"],
            farm_name=user_dict["farm_name"],
            department=user_dict["department"],
            permissions=user_dict["permissions"],
            created_at=user_dict["created_at"],
            last_login=user_dict.get("last_login")
        )

auth_manager = AuthManager()
