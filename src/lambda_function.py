import cfnresponse
import json
import boto3

ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    print('REQUEST RECEIVED:\n' + json.dumps(event))
    responseData = {}

    # Handle Delete requests
    if event['RequestType'] == 'Delete':
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        return

    # Handle Create or Update requests
    if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
        try:
            resource_props = event['ResourceProperties']
            
            # Check if NetworkInterfaceIds are provided
            if 'NetworkInterfaceIds' in resource_props:
                network_interface_ids = resource_props['NetworkInterfaceIds']
                ip_data = fetch_interface_ips(network_interface_ids)
                responseData.update(ip_data)
                print("Retrieved network interface IPs:", responseData)
            
            # Check if VpcId and SecurityGroupId are provided
            if 'VpcId' in resource_props and 'SecurityGroupId' in resource_props:
                vpc_id = resource_props['VpcId']
                security_group_id = resource_props['SecurityGroupId']
                sg_data = update_security_groups(vpc_id, security_group_id)
                responseData.update(sg_data)
                print("Updated security groups:", sg_data)
            
            # Send success response back to CloudFormation
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

        except Exception as e:
            # Send failure response to CloudFormation with the error message
            error_data = {'error': str(e)}
            print(f"Error: {str(e)}")
            cfnresponse.send(event, context, cfnresponse.FAILED, error_data)
            return

def fetch_interface_ips(network_interface_ids):
    """
    Fetch private IPs for given network interface IDs using ec2 client
    Returns a dictionary with keys IP0, IP1, etc. and values as the private IPs
    """
    responseData = {}
    
    # Use describe_network_interfaces instead of the resource approach
    response = ec2_client.describe_network_interfaces(
        NetworkInterfaceIds=network_interface_ids
    )
    
    for index, interface in enumerate(response['NetworkInterfaces']):
        responseData[f'IP{index}'] = interface['PrivateIpAddress']
    
    return responseData

def get_cloudfront_prefix_list_id():
    """
    Get the CloudFront prefix list ID for the current region
    """
    response = ec2_client.describe_managed_prefix_lists(
        Filters=[
            {
                'Name': 'prefix-list-name',
                'Values': ['com.amazonaws.global.cloudfront.origin-facing']
            }
        ]
    )
    
    if not response['PrefixLists']:
        raise Exception("CloudFront prefix list not found in this region")
    
    prefix_list_id = response['PrefixLists'][0]['PrefixListId']
    print(f"Found CloudFront prefix list ID: {prefix_list_id}")
    
    return prefix_list_id

def update_security_groups(vpc_id, security_group_id):
    """
    Update security groups based on VPC ID and Security Group ID
    1. Find CloudFront-VPCOrigins-Service-SG in the specified VPC
    2. Add inbound rule to the provided security group allowing traffic from the CloudFront SG
    3. Add inbound rule to the CloudFront SG allowing traffic from the dynamic CloudFront prefix list
    """
    responseData = {}
    
    # Find CloudFront SG by name and VPC ID
    response = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'group-name', 'Values': ['CloudFront-VPCOrigins-Service-SG']},
            {'Name': 'vpc-id', 'Values': [vpc_id]}
        ]
    )
    
    if not response['SecurityGroups']:
        raise Exception(f"CloudFront Security Group not found in VPC {vpc_id}")
    
    cloudfront_sg_id = response['SecurityGroups'][0]['GroupId']
    responseData['CloudFrontSecurityGroupId'] = cloudfront_sg_id
    
    # Add inbound rule to the provided security group to allow traffic from CloudFront SG
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',  
                    'FromPort': 443,     
                    'ToPort': 443,  
                    'UserIdGroupPairs': [{'GroupId': cloudfront_sg_id}]
                }
            ]
        )
    except ec2_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print(f"Rule already exists in security group {security_group_id}")
        else:
            raise
    
    # Get the dynamic CloudFront prefix list ID for the current region
    cloudfront_prefix_id = get_cloudfront_prefix_list_id()
    responseData['CloudFrontPrefixListId'] = cloudfront_prefix_id
    
    # Add inbound rule to the CloudFront SG to allow traffic from prefix list
    try:
        ec2_client.authorize_security_group_ingress(
            GroupId=cloudfront_sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',  
                    'FromPort': 443,      
                    'ToPort': 443,        
                    'PrefixListIds': [{'PrefixListId': cloudfront_prefix_id}]
                }
            ]
        )
    except ec2_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidPermission.Duplicate':
            print(f"Rule already exists in security group {cloudfront_sg_id}")
        else:
            raise
    
    return responseData