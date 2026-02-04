import boto3
from boto3.dynamodb.conditions import Key
import os
import streamlit as st
from typing import List, Optional
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
                Key={'username': {'S': username}}
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

    # --- Meter Readings ---
    def get_readings(self, user_id: str, meter_type: str) -> List[MeterReading]:
        key_condition = Key(self.HASHKEY).eq(f'{user_id}_{meter_type}')
        
        # We need to use the Table resource for easier querying with Key objects, 
        # or construct the low-level query. Let's use low-level for consistency with client.
        try:
            response = self.dynamo.query(
                TableName=self.TABLE_NAME,
                KeyConditionExpression=f"{self.HASHKEY} = :pk",
                ExpressionAttributeValues={
                    ':pk': {'S': f'{user_id}_{meter_type}'}
                }
            )
            items = response.get('Items', [])
            # Filter out metadata if any (though metadata usually has 'metadata' as range key)
            # Our readings have dates as range key.
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
    def get_meter_types(self, user_id: str) -> List[str]:
        try:
            response = self.dynamo.get_item(
                TableName=self.TABLE_NAME,
                Key={
                    self.HASHKEY: {'S': str(user_id)},
                    self.RANGEKEY: {'S': 'metadata'}
                }
            )
            if 'Item' in response:
                item = response['Item']
                if 'meter_types' in item:
                    # Handle List (L) - preserves order
                    if 'L' in item['meter_types']:
                        return [x['S'] for x in item['meter_types']['L']]
                    # Handle Set (SS) - legacy fallback, sorted
                    elif 'SS' in item['meter_types']:
                        return sorted(item['meter_types']['SS'])
            return []
        except Exception as e:
            print(f"Error getting meter types: {e}")
            return []

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
        # config_key is 'unit' or 'title'
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
