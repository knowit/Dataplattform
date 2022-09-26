import copy
import os
import subprocess
import traceback
from argparse import ArgumentParser, Namespace
import yaml

targets = dict()

# Do not search these directories for serverless.yml files
ignore = [
    'node_modules',
    '.serverless',
    'tests',
    'dist',
    'templates'
]

# Pre-deployment commands upon detected config files
install_commands = dict({
    'requirements.txt': 'pip install -r requirements.txt',
    'package.json': 'npm install',
    'yarn.lock': 'yarn install --frozen-lockfile'
})


# Yaml-parser that will ignore Serverless tags
class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
    def ignore_unknown(self, node):
        return None


SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)


def parse_yaml(path: str) -> dict:
    try:
        return yaml.load(open(path), Loader=SafeLoaderIgnoreUnknown)
    except Exception as e:
        print("Failed to parse yaml file: " + path + "\n" + str(e))
        raise e


# Search a Dataplattform service for dependencies on other Dataplattform services
def resolve_dependencies(path: str, filename: str) -> list:
    config = parse_yaml(filename)
    if 'dataplattform' in config.keys() and 'dependencies' in config['dataplattform'].keys():
        result = []
        abspath = os.path.abspath(path)
        for relpath in config['dataplattform']['dependencies']:
            result.append(os.path.relpath(os.path.join(abspath, relpath), os.curdir))
        return result

    else:
        return []


# Check if a list of paths contain a path that refers to the same file
def contains_path(path_list: list, path: str) -> bool:
    i = 0
    while i < len(path_list):
        item = path_list[i]
        exists = False
        try:
            exists = os.path.samefile(item, path)
        except OSError as e:
            raise e
        finally:
            if exists:
                return True
            else:
                i += 1
    return False


# Remove any path from the list that refers to the same file
def remove_path(path_list: list, path: str) -> None:
    i = 0
    while i < len(path_list):
        item = path_list[i]
        if os.path.samefile(item, path):
            path_list.remove(item)
            return
        else:
            i += 1
    raise IndexError('Path list does not include element: ' + path + "\n" + str(path_list))


# Find all service directories
def search(target: str) -> None:
    for entry in os.scandir(target):
        if entry.is_file():
            if entry.name == 'serverless.yml' or entry.name == 'serverless.yaml':
                if not contains_path(list(targets), target):
                    targets[target] = resolve_dependencies(target, entry.path)
        elif entry.name not in ignore:
            search(entry.path)


# Sort services topologically by their dependencies
def topological_sort(source: dict) -> list:
    a = copy.deepcopy(source)
    keys_list = list(a)

    for path in keys_list:
        deps = a[path]
        rem = []
        for dep in deps:
            if not contains_path(keys_list, dep) and dep not in rem:
                rem.append(dep)
        for dep in rem:
            deps.remove(dep)
            print("Warning: Service " + path + " depends on a service that is not within the working directory: " + dep)

    keys_list.sort(key=lambda j: len(a[j]))

    result = []
    i = 0
    while i < len(keys_list):
        key = keys_list[i]
        if len(a[key]) == 0:
            i = 0
            result.append(key)
            keys_list.remove(key)
            a.pop(key)

            for k in keys_list:
                if contains_path(a[k], key):
                    remove_path(a[k], key)
            if len(keys_list) == 0:
                return result
        else:
            i += 1
    raise Exception('Dataplattform dependency graph has a cycle:\n' + str(keys_list))


def print_status(status: str = None) -> None:
    if status is not None:
        message = "\nDataplattform: " + status
        line = '\n' + ''.join(['-' * (len(message) - 1)])
        print("\n" + line + message + line)


def get_install_commands(path: str) -> list:
    commands = []
    for file in os.listdir(path):
        if file in install_commands.keys():
            commands.append(install_commands[file])
    return commands


def validate_hook(hook: dict) -> None:
    valid_triggers = ['preDeploy', 'postDeploy']
    valid_types = ['invoke', 'command']
    for key in ['name', 'trigger', 'type', 'value']:
        if key not in hook.keys():
            raise Exception("Hook key is missing: " + str(key))
        if not isinstance(hook[key], str):
            raise Exception("Hook property must be of type string: " + str(key) + "\nFound: " + str(type(hook[key])))
        if hook['trigger'] not in valid_triggers:
            raise Exception("Hook trigger must be one of " + str(valid_triggers) + "\nFound: " + str(hook['trigger']))
        if hook['type'] not in valid_types:
            raise Exception("Hook type must be one of " + str(valid_types) + "\nFound: " + str(hook['type']))


def get_hooks(path: str) -> list:
    config = parse_yaml(path + "/serverless.yml")
    if 'dataplattform' in config.keys() and 'hooks' in config['dataplattform'].keys():
        hooks = config['dataplattform']['hooks']
        for hook in hooks:
            validate_hook(hook)
        return hooks
    else:
        return []


def transform_hook(hook: dict, aws_profile: str, stage: str) -> str:
    header_str = 'echo "\n\nInvoking ' + hook['trigger'] + ' hook: ' + str(hook['name'] + ' " &&')
    footer_str = ' && echo ""'
    if hook['type'] == 'invoke':
        return header_str \
               + "sls invoke -f " + hook['value'] \
               + ((" --aws-profile " + aws_profile) if aws_profile is not None else "") \
               + ((" --stage " + stage) if stage is not None else "") \
               + footer_str
    elif hook['type'] == 'command':
        return header_str + hook['value'] + footer_str


def get_environment_commands(path: str, aws_profile: str = None, stage: str = None) -> list:
    return [
        'export SERVERLESS_STAGE="' + stage if stage is not None else 'dev' + '"',
        'export SERVERLESS_STAGE_FLAG="' + ('--stage ' + stage) if stage is not None else '' + '"',
        'export SERVERLESS_AWS_PROFILE_FLAG="'
        + (('--aws-profile ' + aws_profile) if aws_profile is not None else '') + '"'
    ]


def get_deployment_commands(path: str, aws_profile: str = None, stage: str = None) -> list:
    hooks = get_hooks(path)
    pre_deploy_hooks = list(filter(lambda hook: hook['trigger'] == 'preDeploy', hooks))
    post_deploy_hooks = list(filter(lambda hook: hook['trigger'] == 'postDeploy', hooks))

    commands = ['echo "\nDeploying service: ' + path + '"', 'cd ' + path]
    commands.extend(get_environment_commands(path, aws_profile, stage))
    commands.extend(list(map(lambda hook: transform_hook(hook, aws_profile, stage), pre_deploy_hooks)))
    commands.extend(get_install_commands(path))
    commands.append('sls deploy'
                    + ((" --aws-profile " + aws_profile) if aws_profile is not None else "")
                    + ((" --stage " + stage) if stage is not None else ""))
    commands.extend(list(map(lambda hook: transform_hook(hook, aws_profile, stage), post_deploy_hooks)))
    return commands


def get_remove_commands(path: str, aws_profile: str = None, stage: str = None) -> list:
    message = "Removing service: " + path
    commands = ['echo ' + message, 'cd ' + path]
    commands.extend(get_install_commands(path))
    commands.append('sls remove'
                    + ((" --aws-profile " + aws_profile) if aws_profile is not None else "")
                    + ((" --stage " + stage) if stage is not None else ""))
    return commands


def run_process_per_path(
        paths: list,
        get_cmd_func,
        start_message: str = None,
        failed_message: str = None,
        complete_message: str = None) -> None:
    print_status(start_message)
    success = True

    for path in paths:
        commands = get_cmd_func(path)
        try:
            retcode = subprocess.call(' && '.join(commands), shell=True)
            if retcode != 0:
                raise Exception(str("\nAn error occurred while running a subprocess at " + path) if len(path) > 0
                                else "\nAn error occurred while running a subprocess")

        except Exception as e:
            print(e)
            traceback.print_stack()
            success = False
            break

    print_status(complete_message if success else failed_message)


def init(parser: ArgumentParser):
    parser.add_argument('-s', '--services', default='.', type=str, nargs='*')
    parser.add_argument('-e', '--stage', default='dev', choices=['dev', 'test', 'prod'])
    parser.add_argument('-c', '--config-file', default=None, dest='config_file')
    parser.add_argument('-r', '--remove', default=False, action='store_true')
    parser.add_argument('-p', '--aws-profile', default=None, type=str, dest='aws_profile')
    parser.add_argument('-i', '--ignore', default='', type=str, nargs='*')


def run(args: Namespace, _):
    print("")
    for target in args.services:
        search(target)

    paths = topological_sort(targets)

    # Ignore provided services (if any)
    # Paths to ignore are assumed to be
    # provided without leading './'
    for item in args.ignore:
        try:
            remove_path(paths, item)
        except IndexError:
            print("Path list does not include element: " + item)

    if args.remove:
        paths.reverse()
        # Remove all specified services
        run_process_per_path(
            paths=paths,
            get_cmd_func=lambda path: get_remove_commands(path, args.aws_profile, args.stage),
            start_message="Starting service removal",
            failed_message="Service removal stopped",
            complete_message="Service removal complete"
        )

    else:
        if args.config_file is not None:
            # Configure specified SSM-parameters
            run_process_per_path(
                paths=[''],
                get_cmd_func=lambda path: ["dataplattform configure --config-file " + args.config_file],
                start_message="Configuring parameters",
                failed_message="Parameter configuraiton stopped",
                complete_message="Parameter configuration complete"
            )

        # Deploy all specified services
        run_process_per_path(
            paths=paths,
            get_cmd_func=lambda path: get_deployment_commands(path, args.aws_profile, args.stage),
            start_message="Starting service deployment",
            failed_message="Service deployment stopped",
            complete_message="Service deployment complete"
        )
