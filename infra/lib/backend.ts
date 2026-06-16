import * as path from "node:path";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecrAssets from "aws-cdk-lib/aws-ecr-assets";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecsPatterns from "aws-cdk-lib/aws-ecs-patterns";
import * as iam from "aws-cdk-lib/aws-iam";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";
import type { AuthenticationResources } from "./authentication";
import type { DatabaseResources } from "./database";
import type { LlmResources } from "./llm";
import type { NetworkResources } from "./network";

export interface BackendResources {
    readonly backendService: ecsPatterns.ApplicationLoadBalancedFargateService;
}

export interface BackendProps {
    readonly assetPath?: string;
    readonly authentication: AuthenticationResources;
    readonly llm: LlmResources;
    readonly network: NetworkResources;
    readonly database: DatabaseResources;
}

export function createBackend(
    scope: Construct,
    props: BackendProps,
): BackendResources {
    const cluster = new ecs.Cluster(scope, "Cluster", {
        vpc: props.network.vpc,
        containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });
    const service = new ecsPatterns.ApplicationLoadBalancedFargateService(
        scope,
        "BackendService",
        {
            cluster,
            publicLoadBalancer: false,
            openListener: false,
            assignPublicIp: false,
            taskSubnets: {
                subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
            },
            cpu: 512,
            memoryLimitMiB: 1024,
            desiredCount: 1,
            minHealthyPercent: 100,
            circuitBreaker: {
                rollback: true,
            },
            runtimePlatform: {
                cpuArchitecture: ecs.CpuArchitecture.ARM64,
                operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
            },
            listenerPort: 80,
            taskImageOptions: {
                image: ecs.ContainerImage.fromAsset(
                    props.assetPath ?? path.join(__dirname, "../../backend"),
                    {
                        platform: ecrAssets.Platform.LINUX_ARM64,
                    },
                ),
                containerPort: 8000,
                environment: {
                    CHAT_INFRASTRUCTURE_MODE: "aws",
                    AWS_REGION: cdk.Stack.of(scope).region,
                    DYNAMODB_CHAT_TABLE_NAME:
                        props.database.chatTable.tableName,
                    DYNAMODB_LIBRARY_TABLE_NAME:
                        props.database.libraryTable.tableName,
                    BEDROCK_KNOWLEDGE_BASE_ID:
                        props.llm.knowledgeBase.attrKnowledgeBaseId,
                    BEDROCK_MODEL_ARN: props.llm.modelArn,
                    COGNITO_USER_POOL_ID:
                        props.authentication.userPool.userPoolId,
                    COGNITO_USER_POOL_CLIENT_ID:
                        props.authentication.userPoolClient.userPoolClientId,
                },
            },
        },
    );
    service.targetGroup.configureHealthCheck({
        path: "/api/health",
        healthyHttpCodes: "200",
    });
    const stack = cdk.Stack.of(scope);
    const cloudFrontOriginFacingPrefixList =
        cdk.Token.isUnresolved(stack.account) ||
        cdk.Token.isUnresolved(stack.region)
            ? ec2.PrefixList.fromPrefixListId(
                  scope,
                  "CloudFrontOriginFacingPrefixList",
                  "pl-cloudfront-origin-facing",
              )
            : ec2.PrefixList.fromLookup(
                  scope,
                  "CloudFrontOriginFacingPrefixList",
                  {
                      prefixListName:
                          "com.amazonaws.global.cloudfront.origin-facing",
                  },
              );
    service.loadBalancer.connections.allowFrom(
        cloudFrontOriginFacingPrefixList,
        ec2.Port.tcp(80),
        "Allow CloudFront origin-facing traffic",
    );

    service.taskDefinition.taskRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["dynamodb:Scan"],
            resources: [props.database.libraryTable.tableArn],
        }),
    );
    service.taskDefinition.taskRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: [
                "dynamodb:GetItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:Query",
                "dynamodb:TransactWriteItems",
                "dynamodb:UpdateItem",
            ],
            resources: [
                props.database.chatTable.tableArn,
                `${props.database.chatTable.tableArn}/index/gsi1`,
            ],
        }),
    );
    return { backendService: service };
}
