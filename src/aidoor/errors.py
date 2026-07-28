class AIDoorError(Exception):
    pass


class ConfigurationError(AIDoorError):
    pass


class DropFileError(AIDoorError):
    pass


class UnsupportedCommunicationModeError(DropFileError):
    pass


class TerminalError(AIDoorError):
    pass
