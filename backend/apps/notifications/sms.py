class SmsConfigurationError(RuntimeError):
    pass


class SmsBackend:
    """Provider-neutral SMS contract; provider-specific transports implement this interface."""

    def send_sms(self, recipient, message, *, context=None):
        raise NotImplementedError


class UnconfiguredSmsBackend(SmsBackend):
    def send_sms(self, recipient, message, *, context=None):
        raise SmsConfigurationError("SMS provider transport is not configured")
