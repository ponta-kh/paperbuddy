import * as path from "node:path";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecsPatterns from "aws-cdk-lib/aws-ecs-patterns";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3Deployment from "aws-cdk-lib/aws-s3-deployment";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";

export interface InfraStackProps extends cdk.StackProps {
    readonly stageName: string;
    readonly frontendAssetPath?: string;
    readonly backendAssetPath?: string;
}

export class InfraStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: InfraStackProps) {
        super(scope, id, props);

        const chatTable = new dynamodb.Table(this, "ChatTable", {
            tableName: `paperbuddy-${props.stageName}-chat`,
            partitionKey: {
                name: "pk",
                type: dynamodb.AttributeType.STRING,
            },
            sortKey: {
                name: "sk",
                type: dynamodb.AttributeType.STRING,
            },
            billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption: dynamodb.TableEncryption.AWS_MANAGED,
            pointInTimeRecoverySpecification: {
                pointInTimeRecoveryEnabled: true,
            },
            deletionProtection: true,
            removalPolicy: cdk.RemovalPolicy.RETAIN,
        });

        chatTable.addGlobalSecondaryIndex({
            indexName: "gsi1",
            partitionKey: {
                name: "gsi1pk",
                type: dynamodb.AttributeType.STRING,
            },
            sortKey: {
                name: "gsi1sk",
                type: dynamodb.AttributeType.STRING,
            },
            projectionType: dynamodb.ProjectionType.INCLUDE,
            nonKeyAttributes: [
                "chat_id",
                "title",
                "created_at",
                "last_updated_at",
            ],
        });

        const knowledgeBaseId = new cdk.CfnParameter(
            this,
            "BedrockKnowledgeBaseId",
            {
                type: "String",
                description: "Bedrock Knowledge Base ID used by the backend",
            },
        );
        const modelArn = new cdk.CfnParameter(this, "BedrockModelArn", {
            type: "String",
            description: "Bedrock model ARN used by the backend",
        });

        const vpc = new ec2.Vpc(this, "Vpc", {
            maxAzs: 2,
            natGateways: 1,
            subnetConfiguration: [
                {
                    name: "Public",
                    subnetType: ec2.SubnetType.PUBLIC,
                    cidrMask: 24,
                },
                {
                    name: "Application",
                    subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidrMask: 24,
                },
            ],
        });

        const cluster = new ecs.Cluster(this, "Cluster", {
            vpc,
            containerInsightsV2: ecs.ContainerInsights.ENABLED,
        });
        const backendService =
            new ecsPatterns.ApplicationLoadBalancedFargateService(
                this,
                "BackendService",
                {
                    cluster,
                    publicLoadBalancer: false,
                    openListener: false,
                    assignPublicIp: false,
                    taskSubnets: {
                        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    },
                    cpu: 512,
                    memoryLimitMiB: 1024,
                    desiredCount: 1,
                    minHealthyPercent: 100,
                    circuitBreaker: {
                        rollback: true,
                    },
                    listenerPort: 80,
                    taskImageOptions: {
                        image: ecs.ContainerImage.fromAsset(
                            props.backendAssetPath ??
                                path.join(__dirname, "../../backend"),
                        ),
                        containerPort: 8000,
                        environment: {
                            CHAT_INFRASTRUCTURE_MODE: "aws",
                            AWS_REGION: this.region,
                            DYNAMODB_CHAT_TABLE_NAME: chatTable.tableName,
                            BEDROCK_KNOWLEDGE_BASE_ID:
                                knowledgeBaseId.valueAsString,
                            BEDROCK_MODEL_ARN: modelArn.valueAsString,
                        },
                    },
                },
            );
        backendService.targetGroup.configureHealthCheck({
            path: "/api/health",
            healthyHttpCodes: "200",
        });
        backendService.loadBalancer.connections.allowFrom(
            ec2.Peer.ipv4(vpc.vpcCidrBlock),
            ec2.Port.tcp(80),
            "Allow CloudFront VPC origin traffic inside the VPC",
        );

        backendService.taskDefinition.taskRole.addToPrincipalPolicy(
            new iam.PolicyStatement({
                actions: [
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:TransactWriteItems",
                ],
                resources: [
                    chatTable.tableArn,
                    `${chatTable.tableArn}/index/gsi1`,
                ],
            }),
        );
        backendService.taskDefinition.taskRole.addToPrincipalPolicy(
            new iam.PolicyStatement({
                actions: ["bedrock:RetrieveAndGenerate"],
                resources: ["*"],
            }),
        );
        backendService.taskDefinition.taskRole.addToPrincipalPolicy(
            new iam.PolicyStatement({
                actions: ["bedrock:InvokeModel"],
                resources: [modelArn.valueAsString],
            }),
        );

        const frontendBucket = new s3.Bucket(this, "FrontendBucket", {
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
            encryption: s3.BucketEncryption.S3_MANAGED,
            enforceSSL: true,
            removalPolicy: cdk.RemovalPolicy.RETAIN,
        });
        const frontendOrigin =
            origins.S3BucketOrigin.withOriginAccessControl(frontendBucket);
        const backendOrigin = origins.VpcOrigin.withApplicationLoadBalancer(
            backendService.loadBalancer,
            {
                protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                httpPort: 80,
            },
        );
        const distribution = new cloudfront.Distribution(this, "Distribution", {
            defaultRootObject: "index.html",
            minimumProtocolVersion:
                cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            defaultBehavior: {
                origin: frontendOrigin,
                viewerProtocolPolicy:
                    cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowedMethods:
                    cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress: true,
            },
            additionalBehaviors: {
                "/api/*": {
                    origin: backendOrigin,
                    viewerProtocolPolicy:
                        cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
                    cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
                    originRequestPolicy:
                        cloudfront.OriginRequestPolicy
                            .ALL_VIEWER_EXCEPT_HOST_HEADER,
                    compress: true,
                },
            },
        });
        new s3Deployment.BucketDeployment(this, "DeployFrontend", {
            destinationBucket: frontendBucket,
            sources: [
                s3Deployment.Source.asset(
                    props.frontendAssetPath ??
                        path.join(__dirname, "../../frontend/dist"),
                ),
            ],
            distribution,
            distributionPaths: ["/*"],
            prune: true,
        });

        new cdk.CfnOutput(this, "ChatTableName", {
            value: chatTable.tableName,
        });
        new cdk.CfnOutput(this, "ChatTableArn", {
            value: chatTable.tableArn,
        });
        new cdk.CfnOutput(this, "FrontendBucketName", {
            value: frontendBucket.bucketName,
        });
        new cdk.CfnOutput(this, "DistributionDomainName", {
            value: distribution.distributionDomainName,
        });
    }
}
