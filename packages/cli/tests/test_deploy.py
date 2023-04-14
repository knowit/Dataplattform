from unittest.mock import patch
import dataplattform.cli.commands.deploy as commands
import pytest
import yaml
import os

mocked_yaml_files = {
    "test/file/1.yml": {
        "key1": "value1",
        "key2": "value2",
    },
    "services/infrastructure/test-service-1/serverless.yml": {
        "dataplattform": {
            "dependencies": [
                "../test-service-2",
                "../test-service-3",
                "../../utils/test-service-4"
            ],
            "hooks": [
                {
                    "name": "hook-name-1",
                    "trigger": "preDeploy",
                    "type": "invoke",
                    "value": "hook-value-1"
                },
                {
                    "name": "hook-name-2",
                    "trigger": "postDeploy",
                    "type": "command",
                    "value": "hook-value-2"
                }
            ]
        }
    },
    "services/infrastructure/test-service-2/serverless.yml": {
        "key2": "value2"
    },
    "services/infrastructure/test-service-3/serverless.yml": {
        "key3": "value3",
        "dataplattform": {
            "hooks": [
                {
                    "name": "hook-name-3",
                    "trigger": "some-invalid-trigger",
                    "type": "command",
                    "value": "hook-value-3"
                }
            ]
        }
    },
    "services/utils/test-service-4/serverless.yml": {
        "key4": "value4",
        "dataplattform": {
            "dependencies": {
                "../test-service-5"
            }
        }
    },
    "services/utils/test-service-5/serverless.yml": {
        "key5": "value5"
    },
    "services/utils/test-service-6/serverless.yml": {
        "key6": "value6",
        "dataplattform": {
            "dependencies": {
                "../../infrastructure/test-service-1",
                "../test-service-4"
            }
        }
    }
}


def mock_open(path: str, **kwargs) -> dict:
    if path in mocked_yaml_files.keys():
        return yaml.dump(mocked_yaml_files.get(path))
    else:
        raise FileNotFoundError("No such file or directory (mocked): " + path)


def mock_os_path_samefile(a, b):
    abspath_a = os.path.abspath(a)
    abspath_b = os.path.abspath(b)

    res_1 = a == b
    res_2 = abspath_a == abspath_b
    res_3 = abspath_a == os.path.relpath(os.path.join(abspath_a, b), os.curdir)
    res_4 = abspath_b == os.path.relpath(os.path.join(abspath_b, a), os.curdir)
    return res_1 or res_2 or res_3 or res_4


class MockOsScandiriterator:
    def __init__(self, path: str, name: str):
        self.path = '/'.join(list(filter(lambda x: x != ".", [path, name])))
        self.name = name

    def __str__(self):
        return self.path

    def is_file(self):
        for file in mocked_yaml_files:
            if mock_os_path_samefile(self.__str__(), file):
                return True
        return False


def mock_os_scandir(path: str) -> list:
    result = []

    def add_to_result(filename):
        if filename not in result:
            result.append(filename)

    p_normpath = os.path.normpath(path)
    for file in mocked_yaml_files.keys():
        f_normpath = os.path.normpath(file)
        f_list = list(filter(lambda x: x != "", f_normpath.split('/')))
        if p_normpath == ".":
            add_to_result(f_list[0])
        else:
            for i in range(1, len(f_list)):
                f_path = '/'.join(f_list[0: i])
                if mock_os_path_samefile(path, f_path):
                    add_to_result(f_list[i])

    return list(map(lambda x: MockOsScandiriterator(path, x), result))


def test_mock_os_scandir():
    assert list(map(lambda x: x.name, mock_os_scandir("."))) == ["test", "services"]
    assert list(map(lambda x: str(x), mock_os_scandir("."))) == ["test", "services"]
    assert list(map(lambda x: x.name, mock_os_scandir("services"))) == ["infrastructure", "utils"]
    assert list(map(lambda x: str(x), mock_os_scandir("services"))) == ["services/infrastructure", "services/utils"]
    assert list(map(lambda x: x.name, mock_os_scandir("services/infrastructure"))) == [
        "test-service-1", "test-service-2", "test-service-3"
    ]
    assert list(map(lambda x: str(x), mock_os_scandir("services/infrastructure"))) == [
        "services/infrastructure/test-service-1",
        "services/infrastructure/test-service-2",
        "services/infrastructure/test-service-3"
    ]
    assert list(map(lambda x: x.name, mock_os_scandir("services/infrastructure/test-service-1"))) == ["serverless.yml"]
    assert list(map(lambda x: str(x), mock_os_scandir("services/infrastructure/test-service-1"))) == [
        "services/infrastructure/test-service-1/serverless.yml"
    ]


def test_parse_yaml():
    filename = "test/file/1.yml"
    with patch('builtins.open', wraps=mock_open):
        assert commands.parse_yaml(filename) == mocked_yaml_files.get(filename)
        with pytest.raises(FileNotFoundError):
            commands.parse_yaml("non/existing/test/file.yml")


def test_resolve_dependencies():
    with patch('builtins.open', wraps=mock_open):
        with pytest.raises(FileNotFoundError):
            commands.parse_yaml("non/existing/test/file.yml")
        assert commands.resolve_dependencies(
            "services/infrastructure/test-service-1",
            "services/infrastructure/test-service-1/serverless.yml"
        ) == ['services/infrastructure/test-service-2',
              'services/infrastructure/test-service-3',
              'services/utils/test-service-4']


def test_contains_path():
    with patch('os.path.samefile', wraps=mock_os_path_samefile):
        assert commands.contains_path(["some/file/2",
                                       "some/file/../../some/file/../file/1/../1"],
                                      "some/file/1"
                                      )
        assert commands.contains_path([], "") is False
        assert commands.contains_path(["some/file/1", "file/2"], "some/file/2") is False


def test_remove_path():
    with patch('os.path.samefile', wraps=mock_os_path_samefile):
        path_list = ["some/file/1", "some/other/file/2", "another/file/3"]
        with pytest.raises(IndexError):
            commands.remove_path(path_list, "some/non/existing/file")
        commands.remove_path(path_list, "another/../another/file/3/../../file/3")
        assert path_list == ["some/file/1", "some/other/file/2"]


def test_search():
    with patch('builtins.open', wraps=mock_open):
        with patch('os.path.samefile', wraps=mock_os_path_samefile):
            with patch('os.scandir', wraps=mock_os_scandir):
                commands.search("services")
                assert sorted(commands.targets['services/infrastructure/test-service-1']) == [
                    'services/infrastructure/test-service-2',
                    'services/infrastructure/test-service-3',
                    'services/utils/test-service-4'
                ]
                assert commands.targets['services/infrastructure/test-service-2'] == []
                assert commands.targets['services/infrastructure/test-service-3'] == []
                assert commands.targets['services/utils/test-service-4'] == [
                    'services/utils/test-service-5'
                ]
                assert commands.targets['services/utils/test-service-5'] == []
                assert sorted(commands.targets['services/utils/test-service-6']) == [
                    'services/infrastructure/test-service-1',
                    'services/utils/test-service-4',
                ]


def test_topological_sort():
    with patch('builtins.open', wraps=mock_open):
        with patch('os.path.samefile', wraps=mock_os_path_samefile):
            with patch('os.scandir', wraps=mock_os_scandir):
                commands.search(".")
                assert commands.topological_sort(commands.targets) == [
                    'services/infrastructure/test-service-2',
                    'services/infrastructure/test-service-3',
                    'services/utils/test-service-5',
                    'services/utils/test-service-4',
                    'services/infrastructure/test-service-1',
                    'services/utils/test-service-6'
                ]


def test_validate_hook():
    commands.validate_hook({
        "name": "hook-name",
        "trigger": "preDeploy",
        "type": "invoke",
        "value": "hook-value"
    })
    commands.validate_hook({
        "name": "hook-name",
        "trigger": "postDeploy",
        "type": "command",
        "value": "hook-value"
    })
    with pytest.raises(Exception):
        commands.validate_hook({
            "name": "hook-name",
            "trigger": "some-invalid-trigger",
            "type": "command",
            "value": "hook-value"
        })
    with pytest.raises(Exception):
        commands.validate_hook({
            "name": "hook-name",
            "trigger": "postDeploy",
            "type": "some-invalid-type",
            "value": "hook-value"
        })
    with pytest.raises(Exception):
        commands.validate_hook({
            "name": "hook-name",
            "trigger": "postDeploy",
            "type": "invoke",
            "value": 123
        })
    with pytest.raises(Exception):
        commands.validate_hook({})


def test_get_hooks():
    with patch('builtins.open', wraps=mock_open):
        assert commands.get_hooks("services/infrastructure/test-service-1") == [
            {'name': 'hook-name-1', 'trigger': 'preDeploy', 'type': 'invoke', 'value': 'hook-value-1'},
            {'name': 'hook-name-2', 'trigger': 'postDeploy', 'type': 'command', 'value': 'hook-value-2'}]
        assert commands.get_hooks("services/infrastructure/test-service-2") == []
        with pytest.raises(Exception):
            commands.get_hooks("services/infrastructure/test-service-3")
