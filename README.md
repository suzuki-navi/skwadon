# skwadon

AWSのリソースの情報をYAMLで取得し、また設定できるツール。

IAM RoleのAssume Role Policyを取得する例

    $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway.assumeRolePolicy
    Version: '2012-10-17'
    Statement:
    - Effect: Allow
      Principal:
        Service: ops.apigateway.amazonaws.com
      Action: sts:AssumeRole

## Usage

    $ skwadon [get] [-r] [--full] [--diff] [--repeat N] [aws [--profile AWS_PROFILE] [[-p] PATH]] [[-i] [-s] SRC_FILE] [< SRC_FILE]
    $ skwadon put [--dry-run] [aws [--profile AWS_PROFILE] [[-p] PATH] [[-s] SRC_FILE]] [< SRC_FILE]

## 対応サービス

- `iam`
    - `roles`
        - describe, create, update, delete
- `stepfunctions`
    - `stateMachines`
        - describe, update
- `glue`
    - `crawlers`
        - describe, create, update, delete
    - `databases`
        - describe
        - `tables`
            - describe
    - `jobs`
        - describe, create, update
- `redshift`
    - `clusters`
        - describe

まだいろいろ作りかけ。

## Installation

    $ pip install git+https://github.com/suzuki-navi/skwadon

## Development

    $ pip install -e .

## License

This project is licensed under the terms of the [MIT License](https://opensource.org/licenses/MIT).

