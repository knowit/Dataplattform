
module.exports = serverless => {
    const stage = serverless.service.custom.stage;
    const service = serverless.service.service

    const commonStatement = [
        {
            'Effect': 'Allow',
            'Action': ['s3:GetObject'],
            'Resource': [
                {'Fn::Join': ['', [{'Fn::ImportValue': `${stage}-datalakeArn`}, '/query/*']]}
            ]
        },
        {
            'Effect': 'Allow',
            'Action': ['athena:StartQueryExecution', 'athena:GetQueryExecution'],
            'Resource': [
                {'Fn::Join': [':', ['arn:aws:athena', {'Ref': 'AWS::Region'}, {'Ref': 'AWS::AccountId'}, 'workgroup/primary']]}
            ]
        }
    ]

    const accessStatement = (path, database) => ([
        {
            'Effect': 'Allow',
            'Action': ['s3:GetObject'],
            'Resource': [
                {'Fn::Join': ['', [{'Fn::ImportValue': `${stage}-datalakeArn`}, `/data/${path}/*`]]}
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
        level3: [access('level3')]
    };
};