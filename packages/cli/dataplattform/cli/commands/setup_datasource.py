from argparse import ArgumentParser, Namespace
from importlib import import_module
from pkgutil import iter_modules


def init(parser: ArgumentParser):
    parser.add_argument('--datasource', required=False)
    parser.add_argument('--stage', default='dev')


def run(args: Namespace, _):
    def setup(setup_module: str, stage: str):
        module = import_module(f'dataplattform.cli.datasource.{setup_module}')
        getattr(module, 'setup')(stage)

    if args.datasource:
        print(f'setup {args.datasource}')
        setup(args.datasource, args.stage)
    else:
        import dataplattform.cli.datasource as datasource_modules
        for datasource_module in iter_modules(datasource_modules.__path__):
            print(f'setup {datasource_module.name}')
            setup(datasource_module.name, args.stage)
