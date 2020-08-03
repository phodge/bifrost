from setuptools import setup


def _read_pyproject():
    from os.path import dirname, join

    import pytoml

    try:
        with open(join(dirname(__file__), 'pyproject.toml')) as f:
            pyproject = pytoml.load(f)
    except FileNotFoundError:
        # it looks like setuptools renames the file while it's working ... what a dirty hack job
        with open(join(dirname(__file__), 'pyproject.tmp')) as f:
            pyproject = pytoml.load(f)

    try:
        return pyproject['tool']['poetry']
    except KeyError:
        raise Exception("pyproject.toml is missing [tool.poetry] section")


def _flatten_dependency(packagename, spec):
    if packagename == 'python':
        return None

    if packagename == 'paradox-codegen':
        return 'paradox-codegen @ git+https://github.com/phodge/paradox.git@0.3.0#egg=paradox-codegen'  # noqa: E501

    # don't attempt to convert version specifiers
    return packagename


poetry = _read_pyproject()

setup(
    name=poetry['name'],
    version=poetry['version'],
    description=poetry['description'],
    packages=[
        entry['include']
        for entry in poetry['packages']
    ],
    install_requires=list(filter(None, [
        _flatten_dependency(packagename, spec)
        for packagename, spec in poetry['dependencies'].items()
    ]))
)
