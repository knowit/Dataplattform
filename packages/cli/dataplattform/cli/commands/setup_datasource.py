from argparse import ArgumentParser, Namespace
from importlib import import_module
from pkgutil import iter_modules


def init(parser: ArgumentParser):
    parser.add_argument('--datasource')
    parser.add_argument('--stage', default='dev')


def run(args: Namespace, _):
    def setup(setup_module: str, stage: str):
        module = import_module(f'dataplattform.cli.datasource.{setup_module}')
        getattr(module, 'setup')(stage)

    if args.datasource:
        print(f'setup {args.module}')
        setup(args.datasource, args.stage)
    else:
        import setup as setup_modules
        for setup_module in iter_modules(setup_modules.__path__):
            print(f'setup {setup_module.name}')
            setup(setup_module.name, args.stage)
