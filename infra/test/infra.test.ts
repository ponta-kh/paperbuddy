import * as path from 'node:path';
import * as cdk from 'aws-cdk-lib/core';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { InfraStack } from '../lib/infra-stack';

describe('InfraStack', () => {
  const app = new cdk.App();
  const stack = new InfraStack(app, 'TestStack', {
    stageName: 'dev',
    frontendAssetPath: path.join(__dirname, 'fixtures/frontend'),
  });
  const template = Template.fromStack(stack);

  test('creates the protected development chat table', () => {
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      TableName: 'paperbuddy-dev-chat',
      BillingMode: 'PAY_PER_REQUEST',
      DeletionProtectionEnabled: true,
      PointInTimeRecoverySpecification: {
        PointInTimeRecoveryEnabled: true,
      },
      SSESpecification: {
        SSEEnabled: true,
      },
      KeySchema: [
        { AttributeName: 'pk', KeyType: 'HASH' },
        { AttributeName: 'sk', KeyType: 'RANGE' },
      ],
    });
    template.hasResource('AWS::DynamoDB::Table', {
      DeletionPolicy: 'Retain',
      UpdateReplacePolicy: 'Retain',
    });
  });

  test('creates gsi1 for listing chats by user', () => {
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      GlobalSecondaryIndexes: Match.arrayWith([
        Match.objectLike({
          IndexName: 'gsi1',
          KeySchema: [
            { AttributeName: 'gsi1pk', KeyType: 'HASH' },
            { AttributeName: 'gsi1sk', KeyType: 'RANGE' },
          ],
          Projection: {
            ProjectionType: 'INCLUDE',
            NonKeyAttributes: ['chat_id', 'title', 'created_at', 'last_updated_at'],
          },
        }),
      ]),
    });
  });

  test('creates private frontend and backend origins', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketEncryption: {
        ServerSideEncryptionConfiguration: Match.anyValue(),
      },
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true,
      },
    });
    template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', {
      Scheme: 'internal',
      Type: 'application',
    });
    template.hasResourceProperties('AWS::EC2::SecurityGroup', {
      SecurityGroupIngress: Match.arrayWith([
        Match.objectLike({
          Description: 'Allow CloudFront VPC origin traffic inside the VPC',
          FromPort: 80,
          ToPort: 80,
        }),
      ]),
    });
    template.hasResourceProperties('AWS::ECS::Service', {
      DesiredCount: 1,
      LaunchType: 'FARGATE',
      DeploymentConfiguration: Match.objectLike({
        DeploymentCircuitBreaker: {
          Enable: true,
          Rollback: true,
        },
        MinimumHealthyPercent: 100,
      }),
      NetworkConfiguration: {
        AwsvpcConfiguration: Match.objectLike({
          AssignPublicIp: 'DISABLED',
        }),
      },
    });

    const securityGroups = template.findResources('AWS::EC2::SecurityGroup');
    const ingressRules = Object.values(securityGroups).flatMap(
      (resource) => resource.Properties?.SecurityGroupIngress ?? [],
    );
    expect(ingressRules).not.toContainEqual(
      expect.objectContaining({
        CidrIp: '0.0.0.0/0',
        FromPort: 80,
        ToPort: 80,
      }),
    );
  });

  test('routes frontend and api traffic through CloudFront', () => {
    template.hasResourceProperties('AWS::CloudFront::VpcOrigin', {
      VpcOriginEndpointConfig: Match.objectLike({
        OriginProtocolPolicy: 'http-only',
      }),
    });
    template.hasResourceProperties('AWS::CloudFront::Distribution', {
      DistributionConfig: Match.objectLike({
        DefaultRootObject: 'index.html',
        CacheBehaviors: Match.arrayWith([
          Match.objectLike({
            PathPattern: '/api/*',
            ViewerProtocolPolicy: 'redirect-to-https',
          }),
        ]),
      }),
    });
  });

  test('grants the backend task required DynamoDB and Bedrock permissions', () => {
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: ['dynamodb:GetItem', 'dynamodb:Query', 'dynamodb:TransactWriteItems'],
            Effect: 'Allow',
          }),
          Match.objectLike({
            Action: 'bedrock:RetrieveAndGenerate',
            Effect: 'Allow',
          }),
          Match.objectLike({
            Action: 'bedrock:InvokeModel',
            Effect: 'Allow',
          }),
        ]),
      },
    });
  });
});
