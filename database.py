import time
from threading import Lock
from typing import Dict, Tuple, Optional

class LocalOTPStorage:
    def __init__(self):
        self._storage: Dict[str, Tuple[str, float]] = {}  # phone_number -> (otp, expiry_time)
        self._lock = Lock()
    
    def set_otp(self, phone_number: str, otp: str, expiry_seconds: int):
        """Store OTP with expiry time"""
        with self._lock:
            expiry_time = time.time() + expiry_seconds
            self._storage[phone_number] = (otp, expiry_time)
    
    def get_otp(self, phone_number: str) -> Optional[str]:
        """Get OTP for phone number if not expired"""
        with self._lock:
            if phone_number not in self._storage:
                return None
            
            otp, expiry_time = self._storage[phone_number]
            
            # Check if OTP has expired
            if time.time() > expiry_time:
                # Remove expired OTP
                del self._storage[phone_number]
                return None
            
            return otp
    
    def delete_otp(self, phone_number: str):
        """Delete OTP after successful verification"""
        with self._lock:
            if phone_number in self._storage:
                del self._storage[phone_number]
    
    def is_otp_exists(self, phone_number: str) -> bool:
        """Check if OTP exists and is not expired for phone number"""
        with self._lock:
            if phone_number not in self._storage:
                return False
            
            otp, expiry_time = self._storage[phone_number]
            
            # Check if OTP has expired
            if time.time() > expiry_time:
                # Remove expired OTP
                del self._storage[phone_number]
                return False
            
            return True
    
    def cleanup_expired(self):
        """Clean up expired OTPs (can be called periodically)"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (otp, expiry_time) in self._storage.items()
                if current_time > expiry_time
            ]
            for key in expired_keys:
                del self._storage[key]

# Global instance
otp_storage = LocalOTPStorage() 