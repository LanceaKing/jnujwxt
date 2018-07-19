from .utils import find_alert_msg


class JwxtException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg


class LoginError(JwxtException):
    pass


class CoursesError(JwxtException):
    pass


def alertable(error):
    def decorater(function):
        def alertable_function(*args, **kwargs):
            response = function(*args, **kwargs)
            msg = find_alert_msg(response.text)
            if msg:
                raise error(msg)
            return response
        return alertable_function
    return decorater
