from typing import Any, Protocol, Type, TypeAlias, TypeVar, cast, runtime_checkable

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet
from rest_framework.request import Request


# Get the actual User model
DjangoUser = get_user_model()


class UserManager(Protocol):
    def create_user(self, username: str, email: str, password: str) -> "UserType": ...

    def create_superuser(self, username: str, email: str, password: str) -> "UserType": ...

    def get(self, **kwargs: Any) -> "UserType": ...

    def filter(self, **kwargs: Any) -> QuerySet["UserType"]: ...

    def all(self) -> QuerySet["UserType"]: ...


@runtime_checkable
class DjangoUserType(Protocol):
    """Protocol defining the interface of our Django User"""

    objects: UserManager
    is_superuser: bool
    id: int
    username: str
    email: str
    is_authenticated: bool
    is_active: bool
    is_staff: bool
    date_joined: Any
    last_login: Any
    password: str

    def check_password(self, raw_password: str) -> bool: ...

    def set_password(self, raw_password: str) -> None: ...

    def save(self, *args: Any, **kwargs: Any) -> None: ...

    def get_username(self) -> str: ...


DjangoUserInstance = TypeVar("DjangoUserInstance", bound=AbstractBaseUser)
UserType: TypeAlias = DjangoUserInstance
DjangoUserModel: Type[DjangoUserType] = cast(Type[DjangoUserType], get_user_model())


# Type for authenticated Django user requests
class AuthRequest(Request):
    user: DjangoUserType


def get_auth_user(request: Request) -> DjangoUserType:
    if not request.user.is_authenticated:
        from rest_framework.exceptions import NotAuthenticated

        raise NotAuthenticated()
    return cast(DjangoUserType, request.user)


def get_user(request: Request) -> UserType:
    return cast(UserType, request.user)
