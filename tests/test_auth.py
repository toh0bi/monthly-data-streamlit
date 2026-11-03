from src.ui.auth import check_password, hash_password


class TestPasswordHashing:
    def test_round_trip(self):
        hashed = hash_password("secret123")
        assert check_password("secret123", hashed)

    def test_wrong_password_rejected(self):
        hashed = hash_password("secret123")
        assert not check_password("wrong-password", hashed)

    def test_unicode_password(self):
        hashed = hash_password("pässwörd-€üro")
        assert check_password("pässwörd-€üro", hashed)
        assert not check_password("passwort-euro", hashed)

    def test_hashes_are_salted(self):
        assert hash_password("secret123") != hash_password("secret123")

    def test_long_passwords_truncated_to_72_bytes(self):
        # bcrypt only considers the first 72 bytes; the app truncates explicitly
        # so hashing long passwords does not raise.
        base = "a" * 72
        hashed = hash_password(base + "tail-1")
        assert check_password(base + "tail-2", hashed)
        assert not check_password("a" * 71 + "b", hashed)
