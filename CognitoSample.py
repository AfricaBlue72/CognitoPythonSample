#!/bin/env python3
import boto3
import json
import argparse
from datetime import datetime
import time
from CognitoUser import CognitoUser
import uuid

parser = argparse.ArgumentParser(description='Test de user login')
parser.add_argument('-u', '--userPool', metavar='userPool', type=str, required=True, help='The cognito user pool being used')
parser.add_argument('-c', '--client', metavar='client', type=str, required=True, help='The cognito client app')
parser.add_argument('-n', '--userName', metavar='userName', type=str, required=True, help='User name')
parser.add_argument('-p', '--password', metavar='password', type=str, required=True, help='Password')
parser.add_argument('-idp', '--identityPoolId', metavar='identityPoolId', type=str, required=True, help='The identity pool Id of the account you want to access resources in.')

parser.add_argument('-t', '--topicArn', metavar='topicArn', type=str, required=True, help='The ARN of the topic to place the events on')

args = parser.parse_args()

def main():
    print("starting")

    user = CognitoUser(
        username=args.userName, 
        password=args.password, 
        user_pool_id=args.userPool, 
        client_id=args.client, 
        identity_provider_id=args.identityPoolId)
        
    user.sign_in()
    
    temp_credentials = user.get_temporary_credentials()
    
    client = boto3.client('sns',
                          aws_access_key_id=temp_credentials['Credentials']['AccessKeyId'],
                          aws_secret_access_key=temp_credentials['Credentials']['SecretKey'],
                          aws_session_token=temp_credentials['Credentials']['SessionToken'])
                          
                          
    i = 0
    while True:
        i += 1
        message = {'datetime': datetime.now().__str__(), 'iteration': i} 
        attributes = {'messageId': str(uuid.uuid4()), 'iteration': i}
        
        # print(json.dumps(message))
        # print(json.dumps(attributes))
    
        if user.are_temporary_credentials_valid() is False:
            temp_credentials = user.get_temporary_credentials(True)
            
            client = boto3.client('sns',
                                  aws_access_key_id=temp_credentials['Credentials']['AccessKeyId'],
                                  aws_secret_access_key=temp_credentials['Credentials']['SecretKey'],
                                  aws_session_token=temp_credentials['Credentials']['SessionToken'])
        
        publish_message(client, 
                        args.topicArn,
                        json.dumps(message),
                        attributes)
        
        # time.sleep(60)
        break
    
    return


        
def publish_message(client, topicArn, message, attributes):

    try:
        att_dict = {}
        for key, value in attributes.items():
            if isinstance(value, str):
                att_dict[key] = {'DataType': 'String', 'StringValue': value}
            elif isinstance(value, bytes):
                att_dict[key] = {'DataType': 'Binary', 'BinaryValue': value}
                
        response = client.publish(TopicArn=topicArn,
                                  Message=message, 
                                  MessageAttributes=att_dict)
                                  
        message_id = response['MessageId']
        
        print(f'Message published: {message_id}')
    except Exception as e:
        exception_type = type(e).__name__
        print(exception_type)
        print(e)
    else:
        return message_id

if __name__ == "__main__":
    main()
    