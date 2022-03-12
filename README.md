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

## 対応サービス

- `iam.roles.*.conf`
    - describe, create, update, delete
- `iam.roles.*.inlinePolicies.*`
    - describe, create, update, delete
- `iam.roles.*.attachedPolicies`
    - describe
- `iam.roles.*.assumeRolePolicy`
    - describe, create, update, delete
- `s3.buckets.*.location`
    - describe
- `s3.buckets.*.bucketPolicy`
    - describe
- `s3.buckets.*.publicAccessBlock`
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

getアクションでは入力のYAMLの内容をクラウドに確認しに行く。

### example 1

空のマッピング　`{}` はskwadonでは「不明」を表す特別な意味を持つ。

入力中の `{}` となっている箇所は1階層掘って詳細を取得しに行く。

Input

    elem: {}

Cloud

    elem:
        a: ...
        b: ...
        c: ...
        d: ...

Output

    elem:
        a: {}
        b: {}
        c: {}
        d: {}

skwadonで空のマッピング自体を `{"*": null}` と表現する。キーの `*` もskwadonでは特別な意味を持つ。

### example 2

要素の一部だけを書くと、その要素についてのみ情報を取得する。

Input

    elem:
        b: ...
        c: ...

Cloud

    elem:
        a: ...
        b: ...
        c: ...
        d: ...

Output

    elem:
        b: ...
        c: ...

### example 3

キーの `*` はskwadonでは特別な意味を持ち、

Input

    elem:
        b: ...
        c: ...
        '*': {}

上記の入力は

    elem:
        b: ...
        c: ...

と

    elem: {}

の組み合わせとなる。

Cloud

    items:
        a: ...
        b: ...
        c: ...
        d: ...

Output

    items:
        b: ...
        c: ...
        a: {}
        d: {}

## Rule of put action

putアクションでは入力のYAMLの内容をクラウドに設定しに行く。

出力は設定前のクラウドの状態でありgetアクションとほぼ同じ。 `{}` についてはgetアクションと異なり1階層掘ることをしない。

### example 1

Input

    elem: {}

Cloud before change

    elem:
        a: ...
        b: ...
        c: ...
        d: ...

Cloud after change (no change)

    elem:
        a: ...
        b: ...
        c: ...
        d: ...

Output

    elem: {}

### example 2

要素の一部だけを書くと、その要素についてのみ設定する。

Input

    elem:
        b: ...
        c: ...

Cloud before change

    elem:
        a: ...
        b: ...
        c: ...
        d: ...

Cloud after change

    elem:
        a: ...
        b: ... (changed)
        c: ... (changed)
        d: ...

Output

    elem:
        b: ... (before change)
        c: ... (before change)

### example 3

キーの `*` はskwadonでは特別な意味を持ち、以下ではbとc以外の要素を削除する意味になる。

Input

    elem:
        b: ...
        c: ...
        '*': null

Cloud before change

    elem:
        a: ...
        b: ...
        c: ...
        d: ...

Cloud after change

    elem:
        b: ... (changed)
        c: ... (changed)

Output

    elem:
        b: ... (before change)
        c: ... (before change)
        a: null
        d: null




## Installation

    $ pip install git+https://github.com/suzuki-navi/skwadon

## Development

    $ pip install -e .

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/licenses/MIT).

