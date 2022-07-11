from pydantic import BaseModel

class Message(BaseModel):
    value: str

message_json = {'value': 'hello word!'}

message = Message(**message_json)

print(f'pydantic says, "message.value"')
