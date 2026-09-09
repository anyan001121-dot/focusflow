from focusflow.i18n import LANGUAGES, _STRINGS, _URGENCY_LABELS, t


def test_every_string_has_all_languages():
    for key, entry in _STRINGS.items():
        for lang in LANGUAGES:
            assert lang in entry, f"{key!r} missing {lang!r} translation"


def test_every_urgency_label_has_all_languages():
    for urgency, entry in _URGENCY_LABELS.items():
        for lang in LANGUAGES:
            assert lang in entry, f"urgency {urgency!r} missing {lang!r} translation"


def test_t_formats_placeholders():
    assert t("en", "focus_estimated", minutes=5) == "~5 min"
    assert t("zh", "focus_estimated", minutes=5) == "约 5 分钟"
