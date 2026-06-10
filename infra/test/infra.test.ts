import * as path from "node:path";
import { Match, Template } from "aws-cdk-lib/assertions";
import * as cdk from "aws-cdk-lib/core";
import { describe, expect, test } from "vitest";
import { InfraStack } from "../lib/infra-stack";

describe("InfraStack", () => {
    const app = new cdk.App();
    const stack = new InfraStack(app, "TestStack", {
        stageName: "dev",
        frontendAssetPath: path.join(__dirname, "fixtures/frontend"),
    });
    const template = Template.fromStack(stack);

    test("creates the protected development chat table", () => {
        template.hasResourceProperties("AWS::DynamoDB::Table", {
            TableName: "paperbuddy-dev-chat",
            BillingMode: "PAY_PER_REQUEST",
            DeletionProtectionEnabled: true,
            PointInTimeRecoverySpecification: {
                PointInTimeRecoveryEnabled: true,
            },
            SSESpecification: {
                SSEEnabled: true,
            },
            KeySchema: [
                { AttributeName: "pk", KeyType: "HASH" },
                { AttributeName: "sk", KeyType: "RANGE" },
            ],
        });
        template.hasResource("AWS::DynamoDB::Table", {
            DeletionPolicy: "Retain",
            UpdateReplacePolicy: "Retain",
        });
    });

    test("creates gsi1 for listing chats by user", () => {
        template.hasResourceProperties("AWS::DynamoDB::Table", {
            GlobalSecondaryIndexes: Match.arrayWith([
                Match.objectLike({
                    IndexName: "gsi1",
                    KeySchema: [
                        { AttributeName: "gsi1pk", KeyType: "HASH" },
                        { AttributeName: "gsi1sk", KeyType: "RANGE" },
                    ],
                    Projection: {
                        ProjectionType: "INCLUDE",
                        NonKeyAttributes: [
                            "chat_id",
                            "title",
                            "created_at",
                            "last_updated_at",
                        ],
                    },
                }),
            ]),
        });
    });

    test("保護されたライブラリテーブルを作成する", () => {
        template.hasResourceProperties("AWS::DynamoDB::Table", {
            TableName: "paperbuddy-dev-library",
            BillingMode: "PAY_PER_REQUEST",
            DeletionProtectionEnabled: true,
            PointInTimeRecoverySpecification: {
                PointInTimeRecoveryEnabled: true,
            },
            KeySchema: [
                { AttributeName: "pk", KeyType: "HASH" },
                { AttributeName: "sk", KeyType: "RANGE" },
            ],
        });
    });

    test("非公開のフロントエンドバケットとRAG材料バケットを作成する", () => {
        template.resourceCountIs("AWS::S3::Bucket", 2);
        template.allResourcesProperties("AWS::S3::Bucket", {
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
        template.hasResourceProperties("AWS::S3::Bucket", {
            VersioningConfiguration: {
                Status: "Enabled",
            },
        });
    });

    test("creates private frontend and backend origins", () => {
        template.hasResourceProperties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {
                Scheme: "internal",
                Type: "application",
            },
        );
        template.hasResourceProperties("AWS::EC2::SecurityGroup", {
            SecurityGroupIngress: Match.arrayWith([
                Match.objectLike({
                    Description:
                        "Allow CloudFront VPC origin traffic inside the VPC",
                    FromPort: 80,
                    ToPort: 80,
                }),
            ]),
        });
        template.hasResourceProperties("AWS::ECS::Service", {
            DesiredCount: 1,
            LaunchType: "FARGATE",
            DeploymentConfiguration: Match.objectLike({
                DeploymentCircuitBreaker: {
                    Enable: true,
                    Rollback: true,
                },
                MinimumHealthyPercent: 100,
            }),
            NetworkConfiguration: {
                AwsvpcConfiguration: Match.objectLike({
                    AssignPublicIp: "DISABLED",
                }),
            },
        });
        const securityGroups = template.findResources(
            "AWS::EC2::SecurityGroup",
        );
        const ingressRules = Object.values(securityGroups).flatMap(
            (resource) => resource.Properties?.SecurityGroupIngress ?? [],
        );
        expect(ingressRules).not.toContainEqual(
            expect.objectContaining({
                CidrIp: "0.0.0.0/0",
                FromPort: 80,
                ToPort: 80,
            }),
        );

        const taskDefinitions = template.findResources(
            "AWS::ECS::TaskDefinition",
        );
        const environments = Object.values(taskDefinitions).flatMap(
            (resource) =>
                (resource.Properties?.ContainerDefinitions ?? []).flatMap(
                    (container: { Environment?: unknown[] }) =>
                        container.Environment ?? [],
                ),
        );
        expect(environments).toContainEqual({
            Name: "CHAT_INFRASTRUCTURE_MODE",
            Value: "aws",
        });
        expect(environments).toContainEqual({
            Name: "DYNAMODB_LIBRARY_TABLE_NAME",
            Value: expect.objectContaining({
                Ref: expect.stringMatching("LibraryTable"),
            }),
        });
    });

    test("NATとインターネット接続を作成せずVPC Endpointを使用する", () => {
        template.resourceCountIs("AWS::EC2::NatGateway", 0);
        template.resourceCountIs("AWS::EC2::EIP", 0);
        template.resourceCountIs("AWS::EC2::InternetGateway", 0);
        template.resourceCountIs("AWS::EC2::VPCGatewayAttachment", 0);
        template.resourceCountIs("AWS::EC2::VPCEndpoint", 7);

        const routes = template.findResources("AWS::EC2::Route");
        expect(Object.values(routes)).not.toContainEqual(
            expect.objectContaining({
                Properties: expect.objectContaining({
                    DestinationCidrBlock: "0.0.0.0/0",
                }),
            }),
        );

        const endpoints = template.findResources("AWS::EC2::VPCEndpoint");
        const serviceNameSuffixes = Object.values(endpoints).map((endpoint) =>
            endpoint.Properties?.ServiceName?.["Fn::Join"]?.[1]?.at(-1),
        );
        expect(serviceNameSuffixes).toEqual(
            expect.arrayContaining([
                ".s3",
                ".dynamodb",
                ".ecr.api",
                ".ecr.dkr",
                ".logs",
                ".bedrock-agent-runtime",
                ".bedrock-runtime",
            ]),
        );
    });

    test("routes frontend and api traffic through CloudFront", () => {
        template.hasResourceProperties("AWS::CloudFront::VpcOrigin", {
            VpcOriginEndpointConfig: Match.objectLike({
                OriginProtocolPolicy: "http-only",
            }),
        });
        template.hasResourceProperties("AWS::CloudFront::Distribution", {
            DistributionConfig: Match.objectLike({
                DefaultRootObject: "index.html",
                CacheBehaviors: Match.arrayWith([
                    Match.objectLike({
                        PathPattern: "/api/*",
                        ViewerProtocolPolicy: "redirect-to-https",
                    }),
                ]),
            }),
        });
    });

    test("grants the backend task required DynamoDB and Bedrock permissions", () => {
        template.hasResourceProperties("AWS::IAM::Policy", {
            PolicyDocument: {
                Statement: Match.arrayWith([
                    Match.objectLike({
                        Action: "dynamodb:Scan",
                        Effect: "Allow",
                    }),
                    Match.objectLike({
                        Action: Match.arrayWith([
                            "dynamodb:GetItem",
                            "dynamodb:BatchWriteItem",
                            "dynamodb:Query",
                            "dynamodb:TransactWriteItems",
                            "dynamodb:UpdateItem",
                        ]),
                        Effect: "Allow",
                    }),
                    Match.objectLike({
                        Action: "bedrock:RetrieveAndGenerate",
                        Effect: "Allow",
                    }),
                    Match.objectLike({
                        Action: "bedrock:InvokeModel",
                        Effect: "Allow",
                    }),
                ]),
            },
        });
    });
});
