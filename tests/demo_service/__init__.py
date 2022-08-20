from typing import NewType

from flask import Flask

from bifrostrpc import BifrostRPCService

service = BifrostRPCService()

class NoLogin:
    pass


service.addAuthType(NoLogin, lambda: NoLogin())


@service.rpcmethod
def get_reversed(_: NoLogin, input_: str) -> str:
    return input_[::-1]


app = Flask('tests.demo_service')
app.register_blueprint(service.get_flask_blueprint('demo_service', 'tests.demo_service'))
