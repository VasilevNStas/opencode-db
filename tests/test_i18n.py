from i18n import L, _, set_lang


class TestI18n:
    def test_default_lang_is_ru(self) -> None:
        from i18n import current_lang

        assert current_lang in ("ru", "en")

    def test_set_lang_en(self) -> None:
        set_lang("en")
        assert _("list.header.id") == "ID"

    def test_set_lang_ru(self) -> None:
        set_lang("ru")
        result = _("list.header.id")
        assert result == "ID"

    def test_unknown_key_returns_key(self) -> None:
        set_lang("en")
        assert _("nonexistent.key") == "nonexistent.key"

    def test_invalid_lang_ignored(self) -> None:
        set_lang("ru")
        set_lang("fr")
        assert _("list.header.id") == "ID"

    def test_formatting_with_kwargs(self) -> None:
        set_lang("ru")
        result = _("db.not_found", path="/test/path")
        assert "/test/path" in result

    def test_formatting_with_kwargs_en(self) -> None:
        set_lang("en")
        result = _("db.not_found", path="/test/path")
        assert "/test/path" in result

    def test_all_keys_have_both_langs(self) -> None:
        for key, translations in L.items():
            assert "ru" in translations, f"Key {key} missing 'ru'"
            assert "en" in translations, f"Key {key} missing 'en'"

    def test_lang_switch_roundtrip(self) -> None:
        set_lang("en")
        en_val = _("help.intro")
        set_lang("ru")
        ru_val = _("help.intro")
        assert en_val != ru_val
