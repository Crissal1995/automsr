# Base classes for both exceptions and errors
class AutomsrException(Exception):
    """Base class for exceptions obtained at runtime"""


class AutomsrError(Exception):
    """Base class for user errors"""


# Activity exceptions (Automsr exceptions)
class ActivityException(AutomsrException):
    """Base class for Activities exceptions"""


class CannotCompleteActivityException(ActivityException):
    """Exception raised when one or more activities
    cannot be completed"""


class NoDailyActivityFoundException(ActivityException):
    """Exception raised when daily activity was found"""


class LessThanSixDailyActivitiesFoundException(ActivityException):
    """Exception raised when daily activities are not six.
    Three are for daily set, three for tomorrow's set"""


# Automsr exceptions
class CannotRetrievePointsException(AutomsrException):
    """Exception raised when unable to retrieve
    current user's points"""


# Automsr exceptions
class CannotRetrieveDayStreakException(AutomsrException):
    """Exception raised when unable to retrieve
    current user's streak"""


# Automsr errors
class InvalidCredentialsError(AutomsrError):
    """Error class for invalid Credentials objects"""


class InvalidInputError(AutomsrError):
    """Base class for invalid input provided by user"""


class Detected2FAError(AutomsrError):
    """Exception raised when 2FA is detected"""


class EmailError(AutomsrError):
    """Base class for email errors"""


class MissingRecipientError(EmailError):
    """Error raised when no destination email is found"""


class MalformedSenderError(EmailError):
    """Error raised when a sender miss email and/or password"""


class AuthenticationError(EmailError):
    """Error raised when provided credentials are wrong"""


class ConfigurationError(EmailError):
    """Error raised when provided configuration is wrong"""


class MobileSearchError(AutomsrError):
    """Error class for Mobile search exceptions"""


class MobileSearchAvoidFreezeError(AutomsrError):
    """Error raised when mobile search is stopped to avoid freeze"""
