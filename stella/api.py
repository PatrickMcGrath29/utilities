from __future__ import annotations

import json
import os
import secrets
from datetime import datetime

import boto3

dynamodb = boto3.resource('dynamodb')


def create(event, context):
    data = json.loads(event['body'])

    if 'alias' not in data or 'full_url' not in data:
        return invalid_request_response()

    # TODO: Handle overwriting and duplicates
    saved_alias = Alias(data['alias'], data['full_url']).save()
    return success_response(saved_alias)


def get(event, context):
    alias = Alias.get(event['pathParameters']['id'])

    if alias is None:
        return not_found_response()
    else:
        return success_response(alias)


def delete(event, context):
    alias = event['pathParameters']['id']
    secret_id = event['queryStringParameters'].get('secret_id')

    if secret_id is None:
        return invalid_request_response('A secret ID must be included.')

    success = Alias.delete(alias, secret_id)

    if success:
        return success_response({})
    else:
        return not_found_response()


def invalid_request_response(message=None):
    return {'statusCode': 400, 'message': message or 'Bad Request'}


def not_found_response():
    return {'statusCode': 404, 'message': 'Not Found'}


def success_response(body):
    return {'statusCode': 200, 'body': body}


class DynamoClient:
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)

    def get(self, keys: dict) -> dict:
        return self.table.get_item(Key=keys)

    def save(self, item: dict) -> dict:
        return self.table.put_item(Item=item)

    def delete(self, keys: dict) -> bool:
        return self.table.delete_item(Key=keys)


class Alias:
    TABLE_NAME = os.environ['STELLA_DYNAMODB_TABLE']

    def __init__(self, alias, full_url):
        self.alias = alias
        self.full_url = full_url

    def serialize(self) -> dict:
        return {
            'alias': self.alias,
            'full_url': self.full_url
        }

    def save(self) -> dict:
        alias = self.serialize().update({
            'secret_id': self.generate_secret_id(),
            'created_date': datetime.utcnow()
        })
        DynamoClient(self.TABLE_NAME).save(alias)
        return alias

    @classmethod
    def get(cls, alias: str) -> dict:
        response = DynamoClient(cls.TABLE_NAME).get({'id': alias})
        return response
        # return cls(response)

    @classmethod
    def delete(cls, alias: str, secret_id: str) -> bool:
        return DynamoClient(cls.TABLE_NAME).delete({'id': alias, 'secret_id': secret_id})

    @staticmethod
    def generate_secret_id():
        secrets.token_urlsafe(16)


# -- Model --
# database operations
# validation (serialization)

