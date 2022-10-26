from typing import List

from flask import Flask

from bifrostrpc import BifrostRPCService
from tests.scenarios.pets import Pet

service = BifrostRPCService()


class NoLogin:
    pass


service.addAuthType(NoLogin, lambda: NoLogin())
service.addDataclass(Pet)


@service.rpcmethod
def get_reversed(_: NoLogin, input_: str) -> str:
    return input_[::-1]


@service.rpcmethod
def get_pets(_: NoLogin) -> List[Pet]:
    return [
            Pet(name="Basil", species="dog", age=7),
            Pet(name="Billy", species="dog", age=10),
    ]


app = Flask('tests.demo_service')
app.register_blueprint(service.get_flask_blueprint('demo_service', 'tests.demo_service'))
