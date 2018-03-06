from errors import AppError


class UserError(AppError):
    pass


class UserNotFound(UserError):
    code = 404


class InvalidState(UserError):
    code = 406
