import click
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
from typing import Any
import webbrowser
import requests
import random
import hashlib
import string
import base64
from oauthlib.oauth2 import WebApplicationClient


class LocalHttpServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.authorization_code = ""


class LocalHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write("<script type=\"application/javascript\">window.close();</script>".encode("UTF-8"))

        parsed = parse.urlparse(self.path)
        qs = parse.parse_qs(parsed.query)

        self.server.authorization_code = qs["code"][0]


def login(config: dict[str, Any]) -> str:

    with LocalHttpServer(('', config["port"]), LocalHttpHandler) as httpd:
        client = WebApplicationClient(config["client_id"])

        code_verifier, code_challenge = generate_code()
        auth_uri = client.prepare_request_uri(
            config["auth_uri"],
            redirect_uri=config["redirect_uri"],
            scope=config["scopes"],
            state="doesntreallymatter",
            code_challenge=code_challenge,
            code_challenge_method="S256"
            )

        webbrowser.open_new(auth_uri)
        httpd.handle_request()
        auth_code = httpd.authorization_code

        data = {
            "code": auth_code,
            "client_id": config["client_id"],
            "grant_type": "authorization_code",
            "scopes": config["scopes"],
            "redirect_uri": config["redirect_uri"],
            "code_verifier": code_verifier
        }

        response = requests.post(config["token_uri"], data=data, verify=False)
        access_token = response.json()["access_token"]
        print("Logged in successfully")

        return access_token


def generate_code() -> tuple[str, str]:
    rand = random.SystemRandom()
    code_verifier = ''.join(rand.choices(string.ascii_letters + string.digits, k=128))

    code_sha_256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    b64 = base64.urlsafe_b64encode(code_sha_256)
    code_challenge = b64.decode('utf-8').replace('=', '')

    return (code_verifier, code_challenge)


def post(url, headers, data):
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(f"Post status code: {response.status_code}")
    if response.status_code != 200:
        print(response.text)
    return response


def delete(url, headers):
    response = requests.delete(url=url, headers=headers)
    print(f"Delete status code: {response.status_code}\n{response.text}")
    return response


def get_all_to_file(url, headers, env):
    response = requests.get(url=url, headers=headers)
    print(f"Get all status code: {response.status_code}")
    if response.status_code != 200:
        print(response.text)
        exit()
    data = response.json()
    print("\n")
    list = []
    name_map = {list.append({"name": item['name'], "queryString": item['queryString']}) for item in data}
    print(f"name_map: {name_map}\n")
    new_json_object = json.dumps(list, indent=4)
    print(f"{new_json_object}\n")
    with open(f'data/{env}.json', 'w') as fout:
        json.dump(list, fout, indent=4)
    return response


def get(url, headers, name):
    response = requests.get(url=url, headers=headers)
    print(f"Get status code: {response.status_code}")
    if response.status_code != 200:
        print(response.text)
    print("\n")
    list = []
    if response.status_code == 200:
        data = response.json()
        {list.append({"name": item['name'], "created": item['created'], "queryString": item['queryString']})
         for item in data if item['name'] == name}

    return list


def read_file(env):
    with open(f'data/{env}.json', 'r') as fin:
        return json.load(fin)


def find_file_name(content, name):
    found_item = [item['queryString'] for item in content if item['name'] == name]
    return found_item[0] if len(found_item) > 0 else None


def get_auth_bearer(oauth_url, token_url, port_for_listening, client_id):
    config = {
        "port": port_for_listening,
        "client_id": client_id,
        "redirect_uri": f"http://localhost:{port_for_listening}/oauth2-redirect.html",  # from the client in cognito
        "auth_uri": oauth_url,
        "token_uri": token_url,
        "scopes": ["openid"]  # [ "openid", "profile", "any_other_scope" ]
    }

    input_bearer = login(config)
    print(f"Bearer from login in browser: {input_bearer}")
    return input_bearer


def upload_report(name, api_url, headers, headers_post, content):
    item_db = get(url=api_url, headers=headers, name=name)
    item_query = find_file_name(content=content, name=name)
    if item_query is not None:
        print(f"Item query from file: {item_query}")
        print(f"Item in db: {item_db}")
        if len(item_db) > 0:
            print(f"{name} exists in databaase, deleting...")
            delete(url=f"{api_url}/{name}", headers=headers)
        else:
            print(f"{name} is not yet in server db...")

        data = {
            "name": f"{name}",
            "queryString": f"{item_query}"
        }
        print(f"Adding {name} to db: {data}")
        post(url=api_url, headers=headers_post, data=data)
    else:
        print(f"Name {name} isn't defined in file")


@click.command()
@click.option('report_name', '-r', default='_', help="Report name for update. Not necessary when using option -f.")
@click.option('--environment', '-e', default='d', help="Supported environments for upload to API are d and p.")
@click.option(
    '--update_file', '-f', default='n',
    help="Use -f y for overwriting local definition in file. The -e option directs for which environment.")
def main(report_name, environment, update_file):
    """
    A utility to upload a report. Some examples of usage:

    1) test -e d (uploads the report with name 'test' to dev)

    2) accountManager -e p (uploads the report with name 'accountManager' to prod)

    3) test (uploads the report with name 'test' to dev, since dev is default)

    4) -e d -f y (updates the json definition file for environment dev. If ever used,
    remove prefixes for database schema manually before using for upload.)

    5) -e d (uploads all reports defined for dev)

    The reports 'test' and 'accountManager' must be defined in the json file of their
    respective environments 'd' and 'p'. If no option is set, the default is 'd'.
    No report name is necessary for overwriting local file definitions, all will be
    overwritten with what is available online in the chosen environment.
    """

    api_stub_dev = "api.new-dev"
    api_stub_prod = "api.prod"
    api_stub_report = ".dataplattform.knowit.no/data/report"
    auth_stub_dev = "auth.new-dev"
    auth_stub_prod = "auth.prod"
    port_for_listening = 8080
    input_prod = environment
    if input_prod.upper() == "P":
        api_url = f"https://{api_stub_prod}{api_stub_report}"
        file_env = api_stub_prod
        auth_url = f"https://{auth_stub_prod}.dataplattform.knowit.no"
        oauth_url = auth_url + "/oauth2/authorize"
        token_url = auth_url + "/oauth2/token"
        client_id = "3oekolpaf721302coecel4orqi"
    elif input_prod.upper() == "D":
        api_url = f"https://{api_stub_dev}{api_stub_report}"
        file_env = api_stub_dev
        auth_url = f"https://{auth_stub_dev}.dataplattform.knowit.no"
        oauth_url = auth_url + "/oauth2/authorize"
        token_url = auth_url + "/oauth2/token"
        client_id = "1lmu69jtsh5l8dighvprmk7m8u"
    else:
        print("Undefined environment, exiting...")
        exit()

    input_bearer = get_auth_bearer(
        oauth_url=oauth_url,
        token_url=token_url,
        port_for_listening=port_for_listening,
        client_id=client_id
        )

    headers = {'Authorization': f'Bearer {input_bearer}', 'accept': 'application/json'}
    headers_post = {
        'Authorization': f'Bearer {input_bearer}',
        'accept': 'application/json',
        'Content-Type': 'application/json'
        }
    input_update_all = update_file
    if input_update_all.upper() == "Y":
        get_all_to_file(url=api_url, headers=headers, env=file_env)
        print(f"File {file_env}.json updated")
    elif report_name == '_':  # if _ then iterate through all report definitons in json file
        content = read_file(env=file_env)
        for item in content:
            upload_report(
                name=item['name'],
                api_url=api_url,
                headers=headers,
                headers_post=headers_post,
                content=content.copy()
                )
    else:
        content = read_file(env=file_env)
        upload_report(name=report_name, api_url=api_url, headers=headers, headers_post=headers_post, content=content)

    print("Update finished.")


if __name__ == "__main__":
    main()
