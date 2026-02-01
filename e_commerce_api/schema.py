import graphene
from accounts.schema import Query as AccountsQuery, Mutation as AccountsMutation
from products.schema import Query as ProductsQuery, Mutation as ProductsMutation


class Query(AccountsQuery, ProductsQuery):
    pass


class Mutation(AccountsMutation, ProductsMutation):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)