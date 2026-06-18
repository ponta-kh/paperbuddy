import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";

export interface DatabaseResources {
    readonly chatTable: dynamodb.Table;
    readonly libraryTable: dynamodb.Table;
}

export function createDatabaseResources(
    scope: Construct,
    stageName: string,
): DatabaseResources {
    const chatTable = new dynamodb.Table(scope, "ChatTable", {
        tableName: `paperbuddy-${stageName}-chat`,
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
        nonKeyAttributes: ["chat_id", "title", "created_at", "last_updated_at"],
    });

    const libraryTable = new dynamodb.Table(scope, "LibraryTable", {
        tableName: `paperbuddy-${stageName}-library`,
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

    return {
        chatTable,
        libraryTable,
    };
}
