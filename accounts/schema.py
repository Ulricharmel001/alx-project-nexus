import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType

from .models import UserProfile

CustomUser = get_user_model()


class CustomUserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "date_joined",
            "is_active",
            "is_staff",
            "username",
        )


class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile
        fields = ("id", "user", "bio", "profile_picture", "phone_number", "address")


class Query(graphene.ObjectType):
    users = graphene.List(CustomUserType)
    user = graphene.Field(CustomUserType, id=graphene.ID(required=True))
    me = graphene.Field(CustomUserType)

    def resolve_users(self, info):
        return CustomUser.objects.all()

    def resolve_user(self, info, id):
        return CustomUser.objects.get(pk=id)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None


class CreateUser(graphene.Mutation):
    user = graphene.Field(CustomUserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)
        role = graphene.String(default_value="user")

    def mutate(self, info, email, first_name, last_name, password, role):
        user = CustomUser(
            email=email, first_name=first_name, last_name=last_name, role=role
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user, success=True, message="User created successfully")


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
