# skwadon

AWSのリソースの情報をYAMLで取得し、また設定できるツール。

IAM Roleの一覧を見る

    $ skwadon aws iam.roles
    AWSBackupDefaultServiceRole: {}
    AWSServiceRoleForAPIGateway: {}
    AWSServiceRoleForAWSCloud9: {}
    AWSServiceRoleForAmazonElasticsearchService: {}
    AWSServiceRoleForAmazonGuardDuty: {}
    ......

IAM Roleについてはこの項目にアクセスできる

    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway
    conf: {}
    inlinePolicies: {}
    attachedPolicies: {}
    assumeRolePolicy: {}

この中でassumeRolePolicyを見る

    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy
    Version: '2012-10-17'
    Statement:
    - Effect: Allow
      Principal:
        Service: ops.apigateway.amazonaws.com
      Action: sts:AssumeRole

assumeRolePolicyを編集する

    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy > policy.yml
    $ vi policy.yml
    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy put --diff > policy.yml
    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy put --confirm 1348 > policy.yml

## Usage

    $ skwadon [get] [-r] [--full] [--diff] [--repeat N] [aws [--profile AWS_PROFILE] [[-p] PATH]] [[-i] [-s] SRC_FILE] [< SRC_FILE]
    $ skwadon put [--dry-run] [aws [--profile AWS_PROFILE] [[-p] PATH] [[-s] SRC_FILE]] [< SRC_FILE]

![squirrel](image.jpg)

## 対応サービス

- `iam.roles.*.conf`
    - describe, create, update, delete
- `iam.roles.*.inlinePolicies.*`
    - describe, create, update, delete
- `iam.roles.*.attachedPolicies`
    - describe
- `iam.roles.*.assumeRolePolicy`
    - describe, create, update, delete
- `s3.buckets.*.conf`
    - describe
- `s3.buckets.*.bucketPolicy`
    - describe
- `stepfunctions.stateMachines.*.conf`
    - describe, update
- `stepfunctions.stateMachines.*.definition`
    - describe, update
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
- `redshift.clusters.*.conf`
    - describe
- `redshift.clusters.*.status`
    - describe
- `redshift.clusters.*.connection`
    - describe

まだいろいろ作りかけ。設計途上。

## Rule of get action

Input

- `{"*": null}` の箇所はマップの中のすべての要素を取得する
    - 再帰的に下の階層まで取得するかどうかは階層の仕様に依存

Output

- `{"*": null}` はほかに項目がないことを示す
- `{"foo": null}` はその名前の要素がないことを示す

## Rule of put action

Input

- `null` は削除することを示す
- `{"*": null}` の箇所はマップの中のすべての要素を削除する


## Installation

    $ pip install git+https://github.com/suzuki-navi/skwadon

## Development

    $ pip install -e .

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/licenses/MIT).

