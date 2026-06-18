import * as cognito from "aws-cdk-lib/aws-cognito";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";

export interface AuthenticationResources {
    readonly userPool: cognito.UserPool;
    readonly userPoolClient: cognito.UserPoolClient;
}

export function createAuthenticationResources(
    scope: Construct,
    stageName: string,
): AuthenticationResources {
    const userPool = new cognito.UserPool(scope, "UserPool", {
        userPoolName: `paperbuddy-${stageName}`,
        selfSignUpEnabled: true,
        signInAliases: {
            email: true,
        },
        autoVerify: {
            email: true,
        },
        accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
        passwordPolicy: {
            minLength: 12,
            requireDigits: true,
            requireLowercase: true,
            requireSymbols: true,
            requireUppercase: true,
        },
        removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    const userPoolClient = userPool.addClient("WebClient", {
        userPoolClientName: `paperbuddy-${stageName}-web`,
        generateSecret: false,
        authFlows: {
            userSrp: true,
        },
        preventUserExistenceErrors: true,
        accessTokenValidity: cdk.Duration.hours(1),
        idTokenValidity: cdk.Duration.hours(1),
        refreshTokenValidity: cdk.Duration.days(30),
    });

    return {
        userPool,
        userPoolClient,
    };
}
