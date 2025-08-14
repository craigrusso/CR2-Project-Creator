"""Exception types used by the ingest subsystem."""


class IngestError(Exception):
    pass


class VerificationError(IngestError):
    pass


class CanceledError(IngestError):
    pass


