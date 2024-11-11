from typing import Any, Type, TypeAlias, TypeVar, Union, cast, Protocol
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models import Manager, Model, QuerySet
from rest_framework.request import Request


# Get the actual User model
DjangoUser = get_user_model()

class UserManager(Protocol):
    def create_user(self, username: str, email: str, password: str) -> 'DjangoUserType': ...
    def create_superuser(self, username: str, email: str, password: str) -> 'DjangoUserType': ...
    def get(self, **kwargs: Any) -> 'DjangoUserType': ...
    def filter(self, **kwargs: Any) -> QuerySet['DjangoUserType']: ...
    def all(self) -> QuerySet['DjangoUserType']: ...

class DjangoUserType(AbstractUser, Protocol):
    objects: UserManager
    is_superuser: bool
    id: int
    username: str
    is_authenticated: bool

DjangoUserModel: Type[DjangoUserType] = cast(Type[DjangoUserType], get_user_model())

# Union type for all possible user types
UserType = Union[DjangoUserType, AnonymousUser]

# Type for authenticated Django user requests
class AuthRequest(Request):
    user: DjangoUserType

# Helper function to safely cast user to DjangoUserType
def get_auth_user(request: Request) -> DjangoUserType:
    if not request.user.is_authenticated:
        raise ValueError("User must be authenticated")
    return cast(DjangoUserType, request.user)

# QuerySet type helpers
ModelT = TypeVar("ModelT", bound=Model)
ModelQuerySet: TypeAlias = QuerySet[ModelT, Manager[ModelT]]
