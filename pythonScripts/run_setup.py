from importlib import import_module
from pkgutil import iter_modules


def setup(setup_module: str, stage: str):
    module = import_module(f'setup.{setup_module}')
    getattr(module, 'setup')(stage)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser('')
    parser.add_argument('--module')
    parser.add_argument('--stage', default='dev')
    args = parser.parse_args()

    if args.module:
        print(f'setup {args.module}')
        setup(args.module, args.stage)
    else:
        import setup as setup_modules
        for setup_module in iter_modules(setup_modules.__path__):
            print(f'setup {setup_module.name}')
            setup(setup_module.name, args.stage)
