#!/bin/env python3
import boto3
import json
from datetime import datetime
from datetime import tzinfo
from pycognito import Cognito #pip install pycognito
from dateutil.tz import tzlocal

class CognitoUser:
    _cognitoUser = None
    _region = "eu-west-1"
    _credentials = None
    
    def __init__(
        self,
        username,
        password,
        user_pool_id,
        client_id,
        identity_provider_id
    ):
        self.username=username
        self.password=password
        self.user_pool_id=user_pool_id
        self.client_id=client_id
        self.identity_provider_id=identity_provider_id
        
        # Create a Cognito User Object. This object will log into Cognito and obtain OAuth2.0 tokens
        self._cognitoUser = Cognito(user_pool_id = self.user_pool_id,
                                    client_id = self.client_id,
                                    user_pool_region = self._region,
                                    username=self.username)
        
    def sign_in(self):
        print("Signing in")
        try:
            if self._cognitoUser is not None:
                self._cognitoUser.authenticate(self.password)
                
            print("Signed in")
        except Exception as e:
            exception_type = type(e).__name__
            print(exception_type)
            print(e)
            
        
    def get_open_id_token(self):
        try:
            self._cognitoUser.check_token()
            
            if self._cognitoUser is not None:
                return self._cognitoUser.id_token
            else:
                return None
        except Exception as e:
            print('\n' * 2)
            exception_type = type(e).__name__
            print(exception_type)
            print(e)
            print('\n' * 2)
            print('Resigning in: refresh token probably expired')
            print('\n' * 2)
            self.sign_in()

    def get_temporary_credentials(self, forceCreation = False):
        """
        In order to access resources in AWS accounts you need credentials.I
        These credentials are obtained with three things:
        1) A valid Id Token
        2) The provider that issued the Id Token
        3) A valid Identity Id for the account you need access to.
        """
        provider = f'cognito-idp.{self._region}.amazonaws.com/{self.user_pool_id}'
        open_id_token = self.get_open_id_token()
        
        if forceCreation is True or self.are_temporary_credentials_valid() is False:
            try:
                client = boto3.client('cognito-identity')
                # Create or get the Identity in the AWS account you want to access resources in (like SNS)                          
                identity_details = client.get_id( 
                    IdentityPoolId=self.identity_provider_id,
                    Logins={
                            provider: open_id_token
                        } )
                        
                identity_id = identity_details['IdentityId']
                
                # Get temporary credentials
                if open_id_token is not None and identity_id is not None:
                    
                    self._credentials = client.get_credentials_for_identity(
                        IdentityId=identity_id,
                        Logins={
                            provider: open_id_token
                        } )
            except Exception as e:
                exception_type = type(e).__name__
                print(exception_type)
                print(e)
                
        return self._credentials
    
    def are_temporary_credentials_valid(self):
        if self._credentials is None:
            return False
        
        expired = self._credentials['Credentials']['Expiration']
        now = datetime.now(tzlocal())

        #datetime.datetime(2021, 4, 13, 12, 2, 52, tzinfo=tzlocal())
        if now < expired:
            valid = True
        else:
            valid = False
            
        return valid
        