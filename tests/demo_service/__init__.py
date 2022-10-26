from typing import Dict, List

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


@service.rpcmethod
def check_pets(_: NoLogin, pets: Dict[str, Pet]) -> str:
    try:
        basil = pets['basil']
    except KeyError:
        return "Basil is missing"

    try:
        billy = pets['billy']
    except KeyError:
        return "Billy is missing"

    if basil.name != 'Basil':
        return f"pets['basil'] has wrong name {basil.name!r}"

    if billy.name != 'Billy':
        return f"pets['billy'] has wrong name {billy.name!r}"

    return "pets_ok!"


app = Flask('tests.demo_service')
app.register_blueprint(service.get_flask_blueprint('demo_service', 'tests.demo_service'))
