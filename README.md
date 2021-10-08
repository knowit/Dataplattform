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
`sls deploy --stage {STAGE}` where `dev` is the only currently supported stage.  
## Contributing
Contributing by adding a new datasource or other small improvements can be done by creating a pull request as local testing can be utilized and AWS connections mocked. For cloud testing one must be member of the Dataplattform team at Knowit Objectnet.

### Protected branches
Branches that are not named using the `feature/` or `fix/` prefixes are automatically protected, meaning that it is not possible to push directly to these branches. Instead, one must create a pull request into these branches, and these pull requests must be approved by another contributor in order to enable merge. 

### Automatic testing
Lint checks and unit testing will be performed on every pull request.

### Automatic deployment
The `develop` and `master` branches are connected to Dataplattform's `dev` and `prod` environments, accordingly. This means that changes to a service will be automatically deployed once the changes are pushed to either of these branches. 

For example, if any changes made within the `services/ingestion/activeDirectory` folder is pushed to `develop`, then the `activeDirectory` service will be automatically redeployed to the `dev` environment.

### Adding a new feature or fix
Every new feature or fix is created in it's own branch prefixed with `feature/{BRANCH_NAME}` or `fix/{BRANCH_NAME}`, accordingly, where the branch name is descriptive of it's intended purpose.

1. Check into develop by running `git checkout develop`, and pull the most recent changes by running `git pull origin develop --rebase`.
2. Create your branch by running `git checkout -b feature/{BRANCH_NAME}` or `git checkout -b fix/{BRANCH_NAME}`.
3. Perform some change to the code and commit the changes to your local branch by running `git commit -m "{COMMIT_DESCRIPTION}"`. 
4. As a best practice, repeat step 3 for every atomic change to the code. This way, if you make a mistake, you can easily return to your last commit.
5. When your new feature or fix is complete you can push your local commits to a remote branch by running `git push --set-upstream origin feature/{BRANCH_NAME}` or `git push --set-upstream origin fix/{BRANCH_NAME}`
6. Create a pull request from your new branch into the `develop` branch.
8. If any of the tests fail or if your pull request was not approved, revisit your code to make the required changes.
9. Once all tests have passed and your pull request has been approved you may merge the pull request into `develop` by pressing `squash and merge`.
10. Your changes will be automatically deployed to the `dev` environment if the appropriate `github actions` are present.
11. Delete your branch after the merge.


### Pushing to production
Once the `dev` environment is functional and stable, you may want to push all of the previous changes to the production environment. This is done by merging it to the `master` branch.

1. Create a pull request from `develop` into `master`.
2. If the pull request is not approved or if any of the tests fail you may need to add the appropriate fixes. See the previous subsection.
3. Once the tests are passed and the pull request is approved you may merge the changes into `master` by pressing `squash and merge`.
4. The changes will be automatically deployed to the `prod` environment if the appropriate `github actions` are present.



