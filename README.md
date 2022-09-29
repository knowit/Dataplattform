# Dataplattform
This project is an internal initiative for Knowit Objectnet. The purpose of the project is manyfold. It should give hand-on experience on cloud solutions and serverless architecture and it aims to make data available for users of the data platform. 

The main architecture consists of [AWS Lambda](https://aws.amazon.com/lambda/)-functions serving for data ingestion and processing and [AWS S3](https://aws.amazon.com/s3/) as datalake storage. API's for data exploration is under development and schemas are auto-generated using [AWS Glue](https://aws.amazon.com/glue/) while querys can be done using [AWS Athena](https://aws.amazon.com/athena/).  

Currently the platform gathers data from several different datasources, both as scheduled event polls and web hook events. Amongst the supported datasources are [yr](yr.no), github-repos and the internal CV database for Knowit, CV Partner.  
### Dependecies
1. [python 3.7](https://www.python.org/downloads/)
2. [nodejs and npm](https://www.npmjs.com/get-npm)
3. [serverless](https://serverless.com/framework/docs/getting-started#install-via-npm): `npm install -g serverless`
4. [aws-cli](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
It is also highly recommended that you use a virtual environment or similar to manage pip packages and dependencies. 
To configure `aws-cli`, please contact an existing member of the team for credentials.

## Wiki
Members of the Dataplattform team can find useful information pertaining to the project on the [wiki](https://github.com/knowit/Dataplattform-issues/wiki).

## Running the services
The indvidual services are deployed to AWS using
`dataplattform deploy -s {PATHS TO SERVICES SEPARATED BY SPACE}` 
## Contributing
Contributing by adding a new datasource or other small improvements can be done by creating a pull request as local testing can be utilized and AWS connections mocked. For cloud testing one must be member of the Dataplattform team at Knowit Objectnet.

For more information about the CI/CD pipeline of this repo, see [Dataplattform: CI CD Pipeline](https://github.com/knowit/Dataplattform-issues/wiki/Dataplattform:-CI-CD-Pipeline)

### Protected branches
Branches that are not named using the `feature/` or `fix/` prefixes are automatically protected, meaning that it is not possible to push directly to these branches. Instead, one must create a pull request into these branches, and these pull requests must be approved by another contributor in order to enable merge. 

### Automatic testing
Lint checks and unit testing will be performed on every pull request.

### Automatic deployment

Everything merged into the `main` branch will be automatically deployed to the Dataplattform dev-environment.

To deploy the repository to the Dataplattform prod-environment, create a new release from the `main` branch. Its tag
name should be one minor version up from the previous release.

After a deployment is made, either by merging into `main` or by creatng a new release, you should always go to the
*Actions* tab to keep an eye on the deployment workflow, in case anything fails.

### Adding a new feature or fix
Every new feature or fix is created in it's own branch prefixed with `feature/{BRANCH_NAME}` or `fix/{BRANCH_NAME}`, accordingly, where the branch name is descriptive of it's intended purpose.

1. Check into main by running `git checkout main`, and pull the most recent changes by running `git pull origin main --rebase`.
2. Create your branch by running `git checkout -b feature/{BRANCH_NAME}` or `git checkout -b fix/{BRANCH_NAME}`.
3. Perform some change to the code and commit the changes to your local branch by running `git commit -m "{COMMIT_DESCRIPTION}"`. 
4. As a best practice, repeat step 3 for every atomic change to the code. This way, if you make a mistake, you can easily return to your last commit.
5. When your new feature or fix is complete you can push your local commits to a remote branch by running `git push --set-upstream origin feature/{BRANCH_NAME}` or `git push --set-upstream origin fix/{BRANCH_NAME}`
6. Create a pull request from your new branch into the `main` branch.
8. If any of the tests fail or if your pull request was not approved, revisit your code to make the required changes.
9. Once all tests have passed and your pull request has been approved you may merge the pull request into `main` by pressing `squash and merge`.
10. Your changes will be automatically deployed to the `dev` environment. Keep an eye on the deployment workflow in case it fails.
11. Delete your branch after the merge.


### Pushing to production
Once the `dev` environment is functional and stable, you may want to push all of the previous changes to the production environment. This is done by creating a new release.

1. Go to *Tags* -> *Releases*.
2. Look at the name of the newest release. You want your release name to be increased by one minor version.
3. Click *Draft new release*
4. Create a new tag with the new version.
5. Target should be `main`
6. Release title should be the same as the tag name
7. Click *Generate release notes*
8. Click *Publish release*
9. Go to the *Actions* tab and keep an eye on the deployment process.

## Github workflows

### Workflow scripts

To create the CI/CD pipeline, a set of bash-scripts has been used. These scripts, along with their unit tests, are all
within the `.workflow-scripts` directory and is only used within the Github workflows.

The BATS framework has been used for unit testing these scripts. If you have BATS installed on your local machine, the
tests may be run using the following command:
````
bats -r .workflow-scripts
````

### Workflows

#### Deploy Dataplattform

**File:** `.github/workflows/deploy.yml`

This workflow is ran every time code is pushed to the `main` branch, or whenever a new release is published.

When ran, this workflow looks at every changed file, and looks for `serverless.yml` files in any of the changed files'
parent directories. If a `serverless.yml` file is found, that service is added to a list of services to be deployed.

Lastly, the command `dataplattform deploy` is ran for every service that is to be deployed.


#### Lint Python

**File:** `.github/workflows/lint-python.yml`

If a Python file is changed in a pull-request, then this workflow runs Flake8 on every pyhton file in the project.

The Flake8 config in the file `.config/.flake8` is used.


#### Lint YAML

**File:** `.github/workflows/lint-yaml.yml`

If a YAML file is changed in a pull-request, then this workflow runs yamllint on every TAML file in the project.

The yamllint config in the file `.config/.yamllint` is used.


#### Test Python

**File:** `.github/workflows/test-python.yml`

This workflow is ran every time a pull-request is made to the `main` branch.

When ran, this workflow looks at every changed file, and looks for `tox.ini` files in any of the changed files'
parent directories. If a `tox.ini` file is found, that service is added to a list of services to be tested.

Lastly, the command `tox -r` is ran in every directory that is to be tested.


#### Test workflow scripts

**File:** `.github/workflows/test-workflow-scripts.yml`

This workflow is ran every time a pull-request is made to the `main` branch containing changes in the
`.workflow-scripts` directory.

When ran, this workflow runs BATS unit tests on all the BATS-files within the `.workflow-scripts` directory.
