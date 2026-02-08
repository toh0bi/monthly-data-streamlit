from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class MeterReading:
    meter_type: str
    meter_reading: float
    reading_date: str  # YYYY-MM-DD
    
    def to_dynamo_item(self, user_id: str) -> dict:
        return {
            'chat_id_and_type': {'S': f'{user_id}_{self.meter_type}'},
            'reading_date': {'S': self.reading_date},
            'meter_reading': {'N': str(self.meter_reading)}
        }

    @staticmethod
    def from_dynamo_item(item: dict, user_id: str) -> 'MeterReading':
        # chat_id_and_type is like "12345_electricity"
        # we might not need to parse it if we already know the type, but let's be safe
        full_key = item.get('chat_id_and_type', {}).get('S', '')
        meter_type = full_key.replace(f'{user_id}_', '')
        
        return MeterReading(
            meter_type=meter_type,
            meter_reading=float(item.get('meter_reading', {}).get('N', 0)),
            reading_date=item.get('reading_date', {}).get('S', '')
        )

@dataclass
class User:
    username: str
    user_id: str
    password_hash: str
    created_at: str
    ai_quota_used: int = 0
    quota_month: str = "" # YYYY-MM
    last_login: str = ""  # YYYY-MM-DD
    login_count: int = 0

    def to_dynamo_item(self) -> dict:
        return {
            'username': {'S': self.username},
            'user_id': {'S': self.user_id},
            'password_hash': {'S': self.password_hash},
            'created_at': {'S': self.created_at},
            'ai_quota_used': {'N': str(self.ai_quota_used)},
            'quota_month': {'S': self.quota_month},
            'last_login': {'S': self.last_login},
            'login_count': {'N': str(self.login_count)}
        }

    @staticmethod
    def from_dynamo_item(item: dict) -> 'User':
        return User(
            username=item.get('username', {}).get('S', ''),
            user_id=item.get('user_id', {}).get('S', ''),
            password_hash=item.get('password_hash', {}).get('S', ''),
            created_at=item.get('created_at', {}).get('S', ''),
            ai_quota_used=int(item.get('ai_quota_used', {}).get('N', 0)),
            quota_month=item.get('quota_month', {}).get('S', ''),
            last_login=item.get('last_login', {}).get('S', ''),
            login_count=int(item.get('login_count', {}).get('N', 0))
        )
