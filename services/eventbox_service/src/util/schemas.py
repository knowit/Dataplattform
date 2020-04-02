from marshmallow import Schema, fields, post_load
# from .database import Event

class _EventSchema(Schema):
    id = fields.String()
    eventname = fields.String()
    creator = fields.String()
    start = fields.Float()
    end = fields.Float()
    eventcode = fields.String()
    active = fields.Boolean()

    # @post_load
    # def create_event(self, data, **kwargs):
    #     return Event(**data)

eventSchema = _EventSchema()