import boto3
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional
from .models import MeterReading, User

class DBHandler:
    def __init__(self):
        # Try to get credentials from Streamlit secrets, fallback to env vars or default boto3 chain
        self.region = "eu-central-1" # Default, should be configurable
        
        if "AWS_ACCESS_KEY_ID" in st.secrets:
            self.dynamo = boto3.client(
                'dynamodb',
                region_name=st.secrets.get("AWS_DEFAULT_REGION", self.region),
                aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
            )
        else:
            self.dynamo = boto3.client('dynamodb', region_name=self.region)

        self.TABLE_NAME = 'meter_reading_bot'
        self.USER_TABLE_NAME = 'meter_reading_users'
        self.HASHKEY = 'chat_id_and_type'
        self.RANGEKEY = 'reading_date'

    # --- User Management ---
    def get_user(self, username: str) -> Optional[User]:
        try:
            response = self.dynamo.get_item(
                TableName=self.USER_TABLE_NAME,
                Key={'username': {'S': username}},
                ConsistentRead=True
            )
            if 'Item' in response:
                return User.from_dynamo_item(response['Item'])
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def create_user(self, user: User) -> bool:
        try:
            self.dynamo.put_item(
                TableName=self.USER_TABLE_NAME,
                Item=user.to_dynamo_item(),
                ConditionExpression='attribute_not_exists(username)'
            )
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def is_user_id_claimed(self, user_id: str) -> bool:
        """Checks if a user_id (e.g. a legacy Telegram chat_id) is already linked to an existing user account."""
        try:
            response = self.dynamo.scan(
                TableName=self.USER_TABLE_NAME,
                FilterExpression="user_id = :uid",
                ExpressionAttributeValues={':uid': {'S': str(user_id)}},
                ProjectionExpression="username"
            )
            return len(response.get('Items', [])) > 0
        except Exception as e:
            print(f"Error checking user_id claim: {e}")
            return True  # Fail closed for safety

    def legacy_chat_id_exists(self, chat_id: str) -> bool:
        """Checks if a legacy Telegram chat_id actually has a metadata entry in the main table."""
        try:
            response = self.dynamo.get_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(chat_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                }
            )
            return 'Item' in response
        except Exception as e:
            print(f"Error checking legacy chat_id: {e}")
            return False

    def increment_ai_quota(self, username: str, quota_month: str) -> bool:
        try:
            # Atomic counter update
            # We also set the month to ensure we are resetting if month changed (logic handled in caller usually, but let's be safe)
            # Actually, simpler: The caller checks the month. If month changed, we set to 1. If same month, we increment.
            # But DynamoDB 'ADD' is good for increment.
            
            self.dynamo.update_item(
                TableName=self.USER_TABLE_NAME,
                Key={'username': {'S': username}},
                UpdateExpression="SET ai_quota_used = ai_quota_used + :inc, quota_month = :qm",
                ExpressionAttributeValues={
                    ':inc': {'N': '1'},
                    ':qm': {'S': quota_month}
                }
            )
            return True
        except Exception as e:
            print(f"Error incrementing quota: {e}")
            return False
            
    def reset_ai_quota(self, username: str, quota_month: str) -> bool:
        try:
            self.dynamo.update_item(
                TableName=self.USER_TABLE_NAME,
                Key={'username': {'S': username}},
                UpdateExpression="SET ai_quota_used = :val, quota_month = :qm",
                ExpressionAttributeValues={
                    ':val': {'N': '1'}, # Start at 1 for the new request
                    ':qm': {'S': quota_month}
                }
            )
            return True
        except Exception as e:
            print(f"Error resetting quota: {e}")
            return False

    def update_user_stats(self, username: str) -> bool:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            self.dynamo.update_item(
                TableName=self.USER_TABLE_NAME,
                Key={'username': {'S': username}},
                UpdateExpression="SET last_login = :ll ADD login_count :inc",
                ExpressionAttributeValues={
                    ':ll': {'S': today},
                    ':inc': {'N': '1'}
                }
            )
            return True
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False

    # --- Meter Readings ---
    def get_readings(self, user_id: str, meter_type: str) -> List[MeterReading]:
        try:
            items = []
            query_kwargs = {
                'TableName': self.TABLE_NAME,
                'KeyConditionExpression': f"{self.HASHKEY} = :pk",
                'ExpressionAttributeValues': {
                    ':pk': {'S': f'{user_id}_{meter_type}'}
                }
            }
            while True:
                response = self.dynamo.query(**query_kwargs)
                items.extend(response.get('Items', []))
                last_key = response.get('LastEvaluatedKey')
                if not last_key:
                    break
                query_kwargs['ExclusiveStartKey'] = last_key

            readings = []
            for item in items:
                if item.get(self.RANGEKEY, {}).get('S') == 'metadata':
                    continue
                readings.append(MeterReading.from_dynamo_item(item, user_id))
            return readings
        except Exception as e:
            print(f"Error getting readings: {e}")
            return []

    def add_reading(self, user_id: str, reading: MeterReading) -> bool:
        try:
            self.dynamo.put_item(
                TableName=self.TABLE_NAME,
                Item=reading.to_dynamo_item(user_id)
            )
            return True
        except Exception as e:
            print(f"Error adding reading: {e}")
            return False

    def delete_reading(self, user_id: str, meter_type: str, date_str: str) -> bool:
        try:
            self.dynamo.delete_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': f'{user_id}_{meter_type}'},
                    self.RANGEKEY: {'S': date_str}
                }
            )
            return True
        except Exception as e:
            print(f"Error deleting reading: {e}")
            return False

    # --- Metadata / Configuration ---
    def get_user_metadata(self, user_id: str) -> Dict[str, Any]:
        """Fetches the entire metadata item for a user in a single DynamoDB call."""
        try:
            response = self.dynamo.get_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(user_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                }
            )
            item = response.get('Item', {})
            meter_types: List[str] = []
            if 'meter_types' in item:
                if 'L' in item['meter_types']:
                    meter_types = [x['S'] for x in item['meter_types']['L'] if 'S' in x]
                elif 'SS' in item['meter_types']:
                    meter_types = sorted(item['meter_types']['SS'])

            configs: Dict[str, Dict[str, str]] = {}
            for mt in meter_types:
                configs[mt] = {
                    'unit': item.get(f'unit_{mt}', {}).get('S', ''),
                    'eval_mode': item.get(f'eval_mode_{mt}', {}).get('S', 'difference'),
                    'title': item.get(f'title_{mt}', {}).get('S', '')
                }
            return {'meter_types': meter_types, 'configs': configs, 'raw': item}
        except Exception as e:
            print(f"Error getting user metadata: {e}")
            return {'meter_types': [], 'configs': {}, 'raw': {}}

    def get_meter_types(self, user_id: str) -> List[str]:
        return self.get_user_metadata(user_id)['meter_types']

    def update_meter_types(self, user_id: str, meter_types: List[str]) -> bool:
        # Convert to DynamoDB List format to preserve order
        dynamo_list = [{'S': mt} for mt in meter_types]
            
        try:
            self.dynamo.update_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(user_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                },
                UpdateExpression="SET meter_types = :mt",
                ExpressionAttributeValues={
                    ':mt': {'L': dynamo_list}
                }
            )
            return True
        except Exception as e:
            print(f"Error updating meter types: {e}")
            return False

    def get_meter_config(self, user_id: str, meter_type: str, config_key: str) -> Optional[str]:
        # config_key is 'unit', 'eval_mode', or 'title'
        # stored as unit_{meter_type} or title_{meter_type}
        full_key = f"{config_key}_{meter_type}"
        try:
            response = self.dynamo.get_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(user_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                }
            )
            if 'Item' in response:
                return response['Item'].get(full_key, {}).get('S')
            return None
        except Exception as e:
            print(f"Error getting config: {e}")
            return None

    def update_meter_config(self, user_id: str, meter_type: str, config_key: str, value: str) -> bool:
        full_key = f"{config_key}_{meter_type}"
        try:
            self.dynamo.update_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(user_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                },
                UpdateExpression="SET #k = :val",
                ExpressionAttributeNames={
                    '#k': full_key
                },
                ExpressionAttributeValues={
                    ':val': {'S': value}
                }
            )
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def delete_meter_category(self, user_id: str, meter_type: str, remaining_types: List[str]) -> bool:
        """Removes the category from metadata, cleans up its config keys, and deletes its readings."""
        dynamo_list = [{'S': mt} for mt in remaining_types]
        try:
            self.dynamo.update_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(user_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                },
                UpdateExpression="SET meter_types = :mt REMOVE #u, #em, #t",
                ExpressionAttributeNames={
                    '#u': f"unit_{meter_type}",
                    '#em': f"eval_mode_{meter_type}",
                    '#t': f"title_{meter_type}"
                },
                ExpressionAttributeValues={
                    ':mt': {'L': dynamo_list}
                }
            )
            readings = self.get_readings(user_id, meter_type)
            for r in readings:
                self.delete_reading(user_id, meter_type, r.reading_date)
            return True
        except Exception as e:
            print(f"Error deleting meter category: {e}")
            return False
