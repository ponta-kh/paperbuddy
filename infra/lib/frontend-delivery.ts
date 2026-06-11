import * as path from "node:path";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import type * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3Deployment from "aws-cdk-lib/aws-s3-deployment";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";
import type { AuthenticationResources } from "./authentication";

export interface FrontendDeliveryResources {
    readonly frontendBucket: s3.Bucket;
    readonly distribution: cloudfront.Distribution;
}

export interface FrontendDeliveryProps {
    readonly assetPath?: string;
    readonly authentication: AuthenticationResources;
    readonly backendLoadBalancer: elbv2.ApplicationLoadBalancer;
}

export function createFrontendDelivery(
    scope: Construct,
    props: FrontendDeliveryProps,
): FrontendDeliveryResources {
    const frontendBucket = new s3.Bucket(scope, "FrontendBucket", {
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        enforceSSL: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    const frontendOrigin =
        origins.S3BucketOrigin.withOriginAccessControl(frontendBucket);
    const backendOrigin = origins.VpcOrigin.withApplicationLoadBalancer(
        props.backendLoadBalancer,
        {
            protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            httpPort: 80,
        },
    );
    const distribution = new cloudfront.Distribution(scope, "Distribution", {
        defaultRootObject: "index.html",
        minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
        defaultBehavior: {
            origin: frontendOrigin,
            viewerProtocolPolicy:
                cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
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
    new s3Deployment.BucketDeployment(scope, "DeployFrontend", {
        destinationBucket: frontendBucket,
        sources: [
            s3Deployment.Source.asset(
                props.assetPath ?? path.join(__dirname, "../../frontend/dist"),
            ),
            s3Deployment.Source.jsonData("auth-config.json", {
                userPoolId: props.authentication.userPool.userPoolId,
                userPoolClientId:
                    props.authentication.userPoolClient.userPoolClientId,
            }),
        ],
        distribution,
        distributionPaths: ["/*"],
        prune: true,
    });

    return {
        frontendBucket,
        distribution,
    };
}
