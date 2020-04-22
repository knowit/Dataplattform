from pypika.queries import (
    QueryBuilder as BaseQueryBuilder,
    Query as BaseQuery)


class QueryBuilder(BaseQueryBuilder):
    def execute(self, engine):
        return engine.execute(self)


class Query(BaseQuery):
    @classmethod
    def _builder(cls, **kwargs):
        return QueryBuilder(**kwargs)
