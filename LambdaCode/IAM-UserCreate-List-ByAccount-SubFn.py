import json
import boto3
sts = boto3.client('sts')

tableName = 'IAM-user-permission-data'
def lambda_handler(event, context):
    accountID = event['accountID']
    print("event ",event)   
    userDefinedPolicies(accountID)
    return "Success"

def saveToDynamoDB(tableName,accountID,policy,action):
    print("Inside the saveToDynamoDB")
    print("tableName",tableName)
    print("accountID",accountID)
    print("policy",policy)
    print("action",action)
    
  
    dynamodbResource = boto3.resource('dynamodb', region_name='eu-central-1')
    
    table = dynamodbResource.Table(tableName)
    response = table.put_item(
    Item={
                'AccountID':accountID,
                'PolicyARN' :policy,
                'UserRoleDetails' :action
              })
              
def userDefinedPolicies(accountID):
    print("inside user defined policies")
    try:
        RoleArn='arn:aws:iam::' + accountID + ':role/Delegate-Merck-Automation'    
        assumedRoleObject = sts.assume_role(RoleArn=RoleArn,RoleSessionName="IAMSession")
        credentials = assumedRoleObject['Credentials']
        iamResoruce = boto3.resource('iam',aws_access_key_id = credentials['AccessKeyId'],aws_secret_access_key = credentials['SecretAccessKey'], aws_session_token = credentials['SessionToken'],)
    
        UserDefinedPolicies = getAllUserDefinedPolices(iamResoruce)
        #print("UserDefined Policies")
        for policy in UserDefinedPolicies:
            #print("policy",policy)
            policyObj = iamResoruce.Policy(policy)
            policy_version = iamResoruce.PolicyVersion(policyObj.arn,policyObj.default_version.version_id)
            #print("policy_version document",policy_version.document)
            #print("Policy document: ",policy_version.document['Statement'])
            #print("statement type: ",type(policy_version.document['Statement']))
            
            if(isinstance(policy_version.document['Statement'],list)):
                #print("statement is a list", type(policy_version.document['Statement']))
                if(isinstance(policy_version.document['Statement'][0]['Action'],list)):
                    for action in policy_version.document['Statement'][0]['Action']:
                        #print("Action is a list",action)
                        if(("iam:*" in action) or ("iam:Create*" in action) or  ("iam:CreateUser" in action) or ("*" == action)):
                            print("IAM User creation  Access ", action, "policy name ", policy)
                            ListUsersAndRoles(policyObj,policy,accountID)
                            break
                else:
                    #print("Action is a string",policy_version.document['Statement'][0]['Action'])
                    action = policy_version.document['Statement'][0]['Action']
                    if(("iam:*" in action) or ("iam:Create*" in action) or  ("iam:CreateUser" in action) or ("*" == action)):
                        print("IAM User creation  Access ", action , "policy name ", policy)
                        ListUsersAndRoles(policyObj,policy,accountID)
                        
            else:
                
                action = policy_version.document['Statement']['Action']
                #print("stmt is a dict Action",action)
                if(("iam:*" in action) or ("iam:Create*" in action) or  ("iam:CreateUser" in action) or ("*" == action)):
                    print("IAM Full Access ", action, "policy name ", policy)
                    ListUsersAndRoles(policyObj,policy,accountID)
        
        BuildInPolicies(iamResoruce,accountID)
        
        
    except Exception as e:
        print("Exception ",e," account id:",accountID)            
    #saveToDynamoDB(tableName,accountID,policy,action)
        
    return 'Hello from Lambda'
def BuildInPolicies(iamResoruce,accountID):
    print("Inside Buildin functions")
    #iamResoruce = boto3.resource('iam')
    policiesList = ["IAMFullAccess","AdministratorAccess"]
    
    for policy in policiesList:
        policyArn = "arn:aws:iam::aws:policy/"+policy
        policyObj = iamResoruce.Policy(policyArn)
        ListUsersAndRoles(policyObj,policy,accountID)
    
    
def ListUsersAndRoles(policyObj,policy,accountID):
    print("Found policies which has UserCreate Permissions")
    i=0
    j=0
    userObjs = ""
    roleObjs = ""
    userObj = policyObj.attached_users.all()
    for attached_user in userObj:
        if i==0:
            userObjs = userObjs +  ' user_' + attached_user.name
            i = i + 1
        else:
            userObjs = userObjs +  ', user_' + attached_user.name
            
    print('userObjs: ',userObjs)
       
    roleObj = policyObj.attached_roles.all()
        
    for attached_user in roleObj:
        if j==0 :
            roleObjs =  roleObjs +' role_' + attached_user.name
            j += 1
        else:
            roleObjs = roleObjs + ', role_' + attached_user.name
      
    print('roleObjs: ',roleObjs)
    if (userObjs == ""):
        result =  roleObjs
    else:
         result = userObjs + ' ; ' + roleObjs
    if(userObjs == "" and roleObjs == ""):
        print("No users or role found")
    else:    
        saveToDynamoDB(tableName,accountID,policy,result)
    
def getAllUserDefinedPolices(iamResoruce):

    UserDefinedPolicies = []
    
    for Policy in iamResoruce.policies.all():
        if("973242717452" in Policy.arn):
            #print(Policy.arn," is a userdefined policy ")
            UserDefinedPolicies.append(Policy.arn)
            
    return UserDefinedPolicies   
    
