import graphene

from accounts.schema import Mutation as AccountsMutation
from accounts.schema import Query as AccountsQuery
from products.schema import Mutation as ProductsMutation
from products.schema import Query as ProductsQuery


class Query(AccountsQuery, ProductsQuery):
    pass


class Mutation(AccountsMutation, ProductsMutation):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
