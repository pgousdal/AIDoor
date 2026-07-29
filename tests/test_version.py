from aidoor.version import __app_name__, __milepost__, __version__


class TestVersion:
    def test_version_is_0_2_1(self) -> None:
        assert __version__ == "0.2.1"

    def test_app_name(self) -> None:
        assert __app_name__ == "AIDoor"

    def test_milepost(self) -> None:
        assert __milepost__ == "M1 Local Ollama Chat"
