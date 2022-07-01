
module.exports = serverless => {
    const stage = serverless.service.custom.stage;
    const service = serverless.service.service

    const commonStatement = [
        {
            'Effect': 'Allow',
            'Action': ['s3:GetBucketLocation', 's3:ListBucket', 's3:ListBucketMultipartUploads'],
            'Resource': [
                {'Fn::ImportValue': `${stage}-datalakeArn`}
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['athena:StartQueryExecution', 'athena:GetQueryExecution'],
            'Resource': [
                {'Fn::Join': [':', ['arn:aws:athena', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, 'workgroup/primary']]}
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['athena:ListDataCatalogs'],
            'Resource': ['*']
        },
        {
            'Effect': 'Allow',
            'Action': ['athena:ListTableMetadata', 'athena:ListDatabases'],
            'Resource': [
                {'Fn::Join': [':', ['arn:aws:athena', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, 'datacatalog/AwsDataCatalog']]},
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['dynamodb:Scan', 'dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:DeleteItem'],
            'Resource': [
                {'Fn::Join': [':', ['arn:aws:dynamodb', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, `table/${stage}_reports_table`]]},
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['sns:Publish'],
            "Resource": ["*"],
        }
    ]

    const accessStatement = (path, database) => ([
        {
            'Effect': 'Allow',
            'Action': ['s3:GetObject', 's3:PutObject', 's3:ListMultipartUploadParts', 's3:AbortMultipartUpload', 's3:DeleteObject'],
            'Resource': [
                {'Fn::Join': ['', [{'Fn::ImportValue': `${stage}-datalakeArn`}, `/data/${path}/athena-stage/*`]]}
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['s3:GetObject'],
            'Resource': [
                {'Fn::Join': ['', [{'Fn::ImportValue': `${stage}-datalakeArn`}, `/data/${path}/*`]]}
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['s3:GetObject', 's3:SelectObjectContent'],
            'Resource': [
                {'Fn::Join': ['', [{'Fn::ImportValue': `${stage}-datalakeArn`}, `/reports/${path}/*`]]}
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['glue:GetTable', 'glue:GetTables', 'glue:GetDatabase', 'glue:GetDatabases' ,'glue:GetPartitions'],
            'Resource': [
                {'Fn::Join': [':', ['arn:aws:glue', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, 'catalog']]},
                {'Fn::Join': [':', ['arn:aws:glue', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, `database/${stage}_${database}`]]},
                {'Fn::Join': [':', ['arn:aws:glue', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, `table/${stage}_${database}/*`]]},
            ]
        }
    ]);

    const accessTiers = {
        'level1': [
            ...commonStatement,
            ...accessStatement('level-1', 'level_1_database')
        ],
        'level2': [
            ...commonStatement,
            ...accessStatement('level-1', 'level_1_database'),
            ...accessStatement('level-2', 'level_2_database')
        ],
        'level3': [
            ...commonStatement,
            ...accessStatement('level-1', 'level_1_database'),
            ...accessStatement('level-2', 'level_2_database'),
            ...accessStatement('level-3', 'level_3_database')
        ],
        'level4': [
            ...commonStatement,
            ...accessStatement('level-1', 'level_1_database'),
            ...accessStatement('level-2', 'level_2_database'),
            ...accessStatement('level-3', 'level_3_database'),
            ...accessStatement('level-4', 'level_4_database')
        ]
    }

    const access = (level) => ({
        'PolicyName': `${stage}-AccessPolicy-${level}-${service}`,
        'PolicyDocument': {
            'Version': '2012-10-17',
            'Statement': accessTiers[level]      
        }
        
    });

    return {
        level1: [access('level1')],
        level2: [access('level2')],
        level3: [access('level3')],
        level4: [access('level4')]
    };
};