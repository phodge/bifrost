# pylint: disable=unnecessary-lambda
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Union

from flask import Flask, session

from bifrostrpc import AuthFailure, BifrostRPCService
from tests.scenarios.pets import Pet

DEMO_SERVICE_ROOT = Path(__file__).parent

service = BifrostRPCService()


class NoLogin:
    pass


@dataclass
class SessionUser:
    username: str


def get_session_user() -> SessionUser:
    try:
        username = session['current_user']
    except KeyError:
        raise AuthFailure('Not logged in')

    return SessionUser(username)


service.addAuthType(NoLogin, lambda: NoLogin())
service.addAuthType(SessionUser, get_session_user)
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


@service.rpcmethod
def login(_: NoLogin, username: str, password: str) -> Union[Literal[True], str]:
    if username == 'neo' and password == 'trinity':
        session['current_user'] = 'the_one'
        return True

    if username == '':
        return 'Username was empty'

    if password == '':
        return 'Password was empty'

    return 'Invalid username or password'


@service.rpcmethod
def whoami(user: SessionUser) -> str:
    return user.username


@service.rpcmethod
def logout(_: NoLogin) -> None:
    session.pop('current_user', None)


# TODO: test adding a new scalar type
# TODO: test addInternalType()
# TODO: test addExternalType()


app = Flask('tests.demo_service')
app.register_blueprint(service.get_flask_blueprint('demo_service', 'tests.demo_service'))
# this is required for session usage
app.secret_key = 'unit_test_secret'
