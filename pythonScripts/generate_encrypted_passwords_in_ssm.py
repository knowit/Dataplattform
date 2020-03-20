import boto3
from add_secret_to_ssm import add_parameter


def generatePassword(length):
    session = boto3.Session(profile_name="new")
    client = session.client('secretsmanager')

    response = client.get_random_password(
        PasswordLength=length,
        ExcludeNumbers=False,
        ExcludePunctuation=True,
        ExcludeUppercase=False,
        ExcludeLowercase=False,
        IncludeSpace=False,
        RequireEachIncludedType=False
    )

    finalName = add_parameter(response["RandomPassword"], "SecureString")

    return finalName


def main():

    name = generatePassword(64)
    print("Final name: " + name)


if __name__ == "__main__":
    main()
