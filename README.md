# Amazon CloudFront to Private Amazon API Gateway

This solution demonstrates how to securely expose a private Amazon API Gateway through Amazon CloudFront distribution using VPC origins. It provides a robust pattern for establishing secure communication between Amazon CloudFront and private Amazon API Gateway endpoints within your Amazon VPC, allowing access to private APIs without exposing them directly to the internet.

## Architecture Diagram

![Architecture Diagram](./architecture.png)

## Overview

This solution implements a secure architecture pattern with the following components:

1. **Private Amazon API Gateway** - A REST API deployed with private endpoint configuration
2. **VPC Endpoint for Amazon API Gateway** - Provides private connectivity to Amazon API Gateway from within your Amazon VPC
3. **Internal Application Load Balancer** - Deployed in private subnets, routing traffic to the private Amazon API Gateway via VPC endpoint
4. **Amazon CloudFront Distribution** - Uses VPC origin configuration to securely connect to the internal ALB
5. **Route53 DNS Configuration** - For custom domain name resolution
6. **End-to-end HTTPS** - Secured communication using ACM certificates

This architecture ensures that Amazon API Gateway endpoints remain completely private while still being securely accessible through Amazon CloudFront, providing benefits such as AWS Shield Advanced, geoblocking and TLSv1.3 support along with custom cipher suites.

## Getting Started

### Pre-requisites

* An [AWS account](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-creating.html)
* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with appropriate permissions
* A VPC with at least two private subnets
* A Route53 hosted zone for your domain
* Two ACM certificates:
  * One certificate in us-east-1 region for Amazon CloudFront
  * One certificate in the deployment region for ALB

### Deployment

1. Clone this repository to your local machine:

```bash
git clone https://github.com/aws-samples/sample-amazon-cloudfront-to-private-amazon-apigw.git  
cd sample-amazon-cloudfront-to-private-amazon-apigw
```

2. Deploy the SAM template:

```bash
sam build
sam deploy --guided
```

3. During the guided deployment, you will be prompted for the following parameters:

* **VPCId**: The ID of your VPC
* **PrivateSubnets**: Private subnets for ALB and Amazon VPC Endpoint deployment, separated by commas. (e.g. subnet-1111111111111111,subnet-22222222222222222)
* **Route53HostedZoneId**: ID of your Route53 hosted zone
* **Amazon CloudFrontCertificateARN**: ARN of the ACM certificate in the us-east-1 region
* **ALBCertificateARN**: ARN of the ACM certificate in the private ALB deployment region
* **Amazon CloudFrontDomainName**: Domain name for Amazon CloudFront distribution (must be covered by the ACM certificate)

### Testing the Deployment

Once deployment is complete, you can test your API using the Amazon CloudFront URL:

```bash
curl https://your-domain-name/
```

The expected response is:

```json
{"message": "Hello from API GW"}
```

## How It Works

1. **Request Flow:**
   * User requests reach the Amazon CloudFront distribution
   * Amazon CloudFront routes requests to the internal ALB using VPC origin configuration
   * ALB forwards requests to the Amazon API Gateway VPC Endpoint
   * VPC Endpoint connects to the private Amazon API Gateway
   * The response follows the reverse path

2. **Security Measures:**
   * Amazon API Gateway is configured as private and only accessible through the VPC Endpoint
   * Security groups control traffic between Amazon CloudFront distribution, ALB and VPC Endpoint
   * All connections use HTTPS with TLS 1.2+
   * Amazon API Gateway policy limits access to only the VPC Endpoint

3. **Custom Resource Logic:**
   * The solution includes Lambda function to:
     * Fetch private IPs from the VPC Endpoint for ALB target group configuration
     * Update security groups for proper communication between components

## Customization Options

* **Amazon API Gateway Configuration:** Modify the OpenAPI definition in the SAM template to add your own API resources and methods
* **Amazon CloudFront Settings:** Adjust cache policies, origin request policies, and security settings as needed
* **Security Groups:** Add additional rules to the security groups for more granular access control
* **WAF Integration:** Add an AWS WAF web ACL to the Amazon CloudFront distribution for additional protection

## Cleaning Up

To delete all deployed resources, run:

```bash
sam delete
```


## Security

See [CONTRIBUTING](./CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](./LICENSE) file.
