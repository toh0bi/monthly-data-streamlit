from src.data.models import MeterReading, User


class TestMeterReading:
    def test_to_dynamo_item(self):
        reading = MeterReading(meter_type="electricity", meter_reading=1234.5, reading_date="2024-01-15")
        item = reading.to_dynamo_item(user_id="42")

        assert item == {
            'chat_id_and_type': {'S': '42_electricity'},
            'reading_date': {'S': '2024-01-15'},
            'meter_reading': {'N': '1234.5'},
        }

    def test_round_trip(self):
        original = MeterReading(meter_type="water", meter_reading=99.9, reading_date="2023-12-31")
        item = original.to_dynamo_item(user_id="user-1")
        restored = MeterReading.from_dynamo_item(item, user_id="user-1")

        assert restored == original

    def test_from_dynamo_item_strips_only_prefix(self):
        # Meter type containing an underscore must survive the prefix strip
        original = MeterReading(meter_type="heat_pump", meter_reading=10.0, reading_date="2024-06-01")
        item = original.to_dynamo_item(user_id="7")
        restored = MeterReading.from_dynamo_item(item, user_id="7")

        assert restored.meter_type == "heat_pump"

    def test_from_dynamo_item_missing_fields(self):
        restored = MeterReading.from_dynamo_item({}, user_id="42")

        assert restored.meter_type == ""
        assert restored.meter_reading == 0.0
        assert restored.reading_date == ""


class TestUser:
    def _make_user(self) -> User:
        return User(
            username="alice",
            user_id="uuid-123",
            password_hash="$2b$12$hash",
            created_at="2024-01-01T00:00:00",
            ai_quota_used=3,
            quota_month="2024-01",
            last_login="2024-01-15",
            login_count=7,
        )

    def test_round_trip(self):
        original = self._make_user()
        restored = User.from_dynamo_item(original.to_dynamo_item())

        assert restored == original

    def test_from_dynamo_item_defaults(self):
        # Legacy items may lack quota/login fields
        item = {
            'username': {'S': 'bob'},
            'user_id': {'S': '123'},
            'password_hash': {'S': 'hash'},
            'created_at': {'S': '2023-01-01T00:00:00'},
        }
        restored = User.from_dynamo_item(item)

        assert restored.username == 'bob'
        assert restored.ai_quota_used == 0
        assert restored.quota_month == ''
        assert restored.last_login == ''
        assert restored.login_count == 0
