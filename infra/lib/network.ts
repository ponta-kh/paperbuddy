import * as ec2 from "aws-cdk-lib/aws-ec2";
import type * as ecs from "aws-cdk-lib/aws-ecs";
import type { Construct } from "constructs";

export interface NetworkResources {
    readonly vpc: ec2.Vpc;
}

export function createNetwork(scope: Construct): NetworkResources {
    const vpc = new ec2.Vpc(scope, "Vpc", {
        maxAzs: 2,
        natGateways: 0,
        subnetConfiguration: [
            {
                name: "Application",
                subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
                cidrMask: 24,
            },
        ],
    });

    return { vpc };
}

export function connectBackendToAwsServices(
    scope: Construct,
    network: NetworkResources,
    backendService: ecs.FargateService,
): void {
    const endpointSecurityGroup = new ec2.SecurityGroup(
        scope,
        "VpcEndpointSecurityGroup",
        {
            vpc: network.vpc,
            allowAllOutbound: false,
            description:
                "Allow HTTPS from the backend service to VPC endpoints",
        },
    );
    endpointSecurityGroup.connections.allowFrom(
        backendService,
        ec2.Port.tcp(443),
        "Allow backend HTTPS traffic",
    );

    const endpointSubnets = {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
    };
    const gatewayEndpoints = [
        network.vpc.addGatewayEndpoint("S3Endpoint", {
            service: ec2.GatewayVpcEndpointAwsService.S3,
            subnets: [endpointSubnets],
        }),
        network.vpc.addGatewayEndpoint("DynamoDbEndpoint", {
            service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            subnets: [endpointSubnets],
        }),
    ];
    const interfaceEndpointServices = [
        ec2.InterfaceVpcEndpointAwsService.ECR,
        ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
        ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        ec2.InterfaceVpcEndpointAwsService.COGNITO_IDP,
        ec2.InterfaceVpcEndpointAwsService.BEDROCK_AGENT_RUNTIME,
        ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
    ];
    const interfaceEndpoints = interfaceEndpointServices.map((service, index) =>
        network.vpc.addInterfaceEndpoint(`InterfaceEndpoint${index}`, {
            service,
            subnets: endpointSubnets,
            securityGroups: [endpointSecurityGroup],
        }),
    );
    backendService.node.addDependency(
        ...gatewayEndpoints,
        ...interfaceEndpoints,
    );
}
