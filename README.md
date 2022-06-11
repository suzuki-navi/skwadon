# skwadon

AWSのリソースの情報をYAMLで取得(get)し、また設定(put)するツール。

IAM Roleの一覧を見る

    $ skwadon aws iam.roles
    AWSBackupDefaultServiceRole: {}
    AWSServiceRoleForAPIGateway: {}
    AWSServiceRoleForAWSCloud9: {}
    AWSServiceRoleForAmazonElasticsearchService: {}
    AWSServiceRoleForAmazonGuardDuty: {}
    ......

IAM Roleの詳細を見る

    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway
    conf:
      Description: The Service Linked Role is used by Amazon API Gateway.
      MaxSessionDuration: 3600
    inlinePolicies: {}
    attachedPolicies:
      APIGatewayServiceRolePolicy: {}
    assumeRolePolicy:
      Version: '2012-10-17'
      Statement:
      - Effect: Allow
        Principal:
          Service: ops.apigateway.amazonaws.com
        Action: sts:AssumeRole

assumeRolePolicyを編集する

    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy > policy.yml
    $ vi policy.yml
    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy put --diff < policy.yml
    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy put --confirm 1348 < policy.yml

## Usage

    $ skwadon [get] [-r] [--full] [--diff] [--thats-all] [aws [--profile AWS_PROFILE] [[-p] PATH]] [[-i] [-s] SRC_FILE] [< SRC_FILE]
    $ skwadon put [--dry-run|--diff] [aws [--profile AWS_PROFILE] [[-p] PATH] [[-s] SRC_FILE]] [< SRC_FILE]

![squirrel](image.jpg)

## Supported Services

- `iam.roles.*.conf`
    - describe, create, update, delete
- `iam.roles.*.inlinePolicies.*`
    - describe, create, update, delete
- `iam.roles.*.attachedPolicies`
    - describe
- `iam.roles.*.assumeRolePolicy`
    - describe, create, update, delete
- `iam.groups.*.conf`
    - describe
- `iam.groups.*.inlinePolicies.*`
    - describe
- `iam.groups.*.attachedPolicies`
    - describe
- `iam.policies.*.conf`
    - describe
- `iam.policies.*.policy`
    - describe
- `iam.policies.*.tags`
    - describe
- `s3.buckets.*.conf`
    - describe
- `s3.buckets.*.bucketPolicy`
    - describe
- `s3.buckets.*.lifecyles`
    - describe, create, update, delete
- `lambda.functions.*.conf`
    - describe, create, update
- `lambda.functions.*.sources`
    - describe, create, update
- `stepfunctions.stateMachines.*.conf`
    - describe, create, update
- `stepfunctions.stateMachines.*.definition`
    - describe, create, update
- `glue.crawlers.*.conf`
    - describe, create, update, delete
- `glue.crawlers.*.status`
    - describe
- `glue.databases.*.conf`
    - describe
- `glue.databases.*.tables.*.conf`
    - describe, create, update
- `glue.databases.*.tables.*.columns`
    - describe, create, update
- `glue.jobs.*.conf`
    - describe, create, update
- `glue.jobs.*.source`
    - describe, create, update
- `glue.jobs.*.bookmark`
    - describe
- `glue.connections.*.conf`
    - describe, create, update
- `glue.connections.*.connection`
    - describe
- `glue.triggers.*.conf`
    - describe, create, update, delete
- `rds.instances.*.conf`
    - describe
- `rds.instances.*.status`
    - describe
- `rds.instances.*.all`
    - describe
- `redshift.clusters.*.conf`
    - describe
- `redshift.clusters.*.all`
    - describe
- `redshift.clusters.*.connection`
    - describe

まだいろいろ作りかけ。設計途上。

## Rule of get action

Input

- `'*': null` はマップの中のすべての要素を取得することを示す
    - 再帰的に下の階層まで取得するかどうかは階層の仕様に依存

Output

- `foo: null` はその名前の要素がないことを示す

## Rule of put action

Input

- `foo: null` はその要素を削除することを示す
- `'*': null` はマップの中の存在を明示した要素以外のすべての要素を削除することを示す

## Installation

    $ pip install git+https://github.com/suzuki-navi/skwadon

## Development

    $ pip install -e .

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/licenses/MIT).

