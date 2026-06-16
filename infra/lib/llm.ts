import * as bedrock from "aws-cdk-lib/aws-bedrock";
import * as iam from "aws-cdk-lib/aws-iam";
import * as opensearchserverless from "aws-cdk-lib/aws-opensearchserverless";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";

const DATA_SOURCE_PREFIX = "documents/";
const EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0";
const EMBEDDING_VECTOR_DIMENSION = 1024;
const VECTOR_INDEX_NAME = "bedrock-knowledge-base";
const VECTOR_FIELD_NAME = "bedrock-knowledge-base-default-vector";
const TEXT_FIELD_NAME = "AMAZON_BEDROCK_TEXT_CHUNK";
const METADATA_FIELD_NAME = "AMAZON_BEDROCK_METADATA";

export interface LlmResources {
    readonly dataSource: bedrock.CfnDataSource;
    readonly knowledgeBase: bedrock.CfnKnowledgeBase;
    readonly modelArn: string;
    readonly ragSourceBucket: s3.Bucket;
}

export function createLlmResources(
    scope: Construct,
    stageName: string,
    generationModelArn: string,
): LlmResources {
    const stack = cdk.Stack.of(scope);
    const ragSourceBucket = createRagSourceBucket(scope);
    const modelArn = generationModelArn;
    const embeddingModelArn = stack.formatArn({
        service: "bedrock",
        region: stack.region,
        account: "",
        resource: "foundation-model",
        resourceName: EMBEDDING_MODEL_ID,
    });
    const knowledgeBaseRole = createKnowledgeBaseRole(
        scope,
        embeddingModelArn,
        ragSourceBucket,
    );
    const vectorStore = createVectorStore(scope, stageName, knowledgeBaseRole);
    const knowledgeBase = new bedrock.CfnKnowledgeBase(scope, "KnowledgeBase", {
        name: `paperbuddy-${stageName}`,
        description: `PaperBuddy ${stageName} knowledge base`,
        roleArn: knowledgeBaseRole.roleArn,
        knowledgeBaseConfiguration: {
            type: "VECTOR",
            vectorKnowledgeBaseConfiguration: {
                embeddingModelArn,
            },
        },
        storageConfiguration: {
            type: "OPENSEARCH_SERVERLESS",
            opensearchServerlessConfiguration: {
                collectionArn: vectorStore.collection.attrArn,
                vectorIndexName: VECTOR_INDEX_NAME,
                fieldMapping: {
                    vectorField: VECTOR_FIELD_NAME,
                    textField: TEXT_FIELD_NAME,
                    metadataField: METADATA_FIELD_NAME,
                },
            },
        },
    });
    knowledgeBase.node.addDependency(knowledgeBaseRole, vectorStore.index);

    const dataSource = new bedrock.CfnDataSource(
        scope,
        "KnowledgeBaseDataSource",
        {
            name: `paperbuddy-${stageName}-s3`,
            description: `PaperBuddy ${stageName} RAG source documents`,
            knowledgeBaseId: knowledgeBase.attrKnowledgeBaseId,
            dataDeletionPolicy: "RETAIN",
            dataSourceConfiguration: {
                type: "S3",
                s3Configuration: {
                    bucketArn: ragSourceBucket.bucketArn,
                    inclusionPrefixes: [DATA_SOURCE_PREFIX],
                },
            },
        },
    );
    dataSource.node.addDependency(knowledgeBase);

    return {
        dataSource,
        knowledgeBase,
        modelArn,
        ragSourceBucket,
    };
}

export function grantBackendBedrockAccess(
    taskRole: iam.IRole,
    llm: LlmResources,
): void {
    taskRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["bedrock:RetrieveAndGenerate"],
            resources: ["*"],
        }),
    );
    taskRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["bedrock:InvokeModel"],
            resources: [llm.modelArn],
        }),
    );
}

function createRagSourceBucket(scope: Construct): s3.Bucket {
    return new s3.Bucket(scope, "RagSourceBucket", {
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        enforceSSL: true,
        versioned: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
}

function createKnowledgeBaseRole(
    scope: Construct,
    embeddingModelArn: string,
    ragSourceBucket: s3.Bucket,
): iam.Role {
    const stack = cdk.Stack.of(scope);
    const role = new iam.Role(scope, "KnowledgeBaseRole", {
        assumedBy: new iam.ServicePrincipal("bedrock.amazonaws.com", {
            conditions: {
                StringEquals: {
                    "aws:SourceAccount": stack.account,
                },
                ArnLike: {
                    "aws:SourceArn": stack.formatArn({
                        service: "bedrock",
                        resource: "knowledge-base",
                        resourceName: "*",
                    }),
                },
            },
        }),
    });
    role.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["bedrock:InvokeModel"],
            resources: [embeddingModelArn],
        }),
    );
    ragSourceBucket.grantRead(role, `${DATA_SOURCE_PREFIX}*`);
    return role;
}

function createVectorStore(
    scope: Construct,
    stageName: string,
    knowledgeBaseRole: iam.Role,
): {
    readonly collection: opensearchserverless.CfnCollection;
    readonly index: opensearchserverless.CfnIndex;
} {
    const stack = cdk.Stack.of(scope);
    const bootstrapQualifier = stack.synthesizer.bootstrapQualifier;
    if (!bootstrapQualifier) {
        throw new Error("CDK bootstrap qualifierを取得できません");
    }
    const cloudFormationExecutionRoleArn = stack.formatArn({
        service: "iam",
        region: "",
        resource: "role",
        resourceName: `cdk-${bootstrapQualifier}-cfn-exec-role-${stack.account}-${stack.region}`,
    });
    const collectionName = `paperbuddy-${stageName}-kb`;
    const encryptionPolicy = new opensearchserverless.CfnSecurityPolicy(
        scope,
        "KnowledgeBaseVectorEncryptionPolicy",
        {
            name: `${collectionName}-encryption`,
            type: "encryption",
            policy: JSON.stringify({
                Rules: [
                    {
                        ResourceType: "collection",
                        Resource: [`collection/${collectionName}`],
                    },
                ],
                AWSOwnedKey: true,
            }),
        },
    );
    const networkPolicy = new opensearchserverless.CfnSecurityPolicy(
        scope,
        "KnowledgeBaseVectorNetworkPolicy",
        {
            name: `${collectionName}-network`,
            type: "network",
            policy: JSON.stringify([
                {
                    Rules: [
                        {
                            ResourceType: "collection",
                            Resource: [`collection/${collectionName}`],
                        },
                    ],
                    AllowFromPublic: true,
                },
            ]),
        },
    );
    const collection = new opensearchserverless.CfnCollection(
        scope,
        "KnowledgeBaseVectorCollection",
        {
            name: collectionName,
            type: "VECTORSEARCH",
            standbyReplicas: "DISABLED",
            description: `PaperBuddy ${stageName} knowledge base vectors`,
        },
    );
    collection.addDependency(encryptionPolicy);
    collection.addDependency(networkPolicy);

    knowledgeBaseRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["aoss:APIAccessAll"],
            resources: [collection.attrArn],
        }),
    );
    const accessPolicy = new opensearchserverless.CfnAccessPolicy(
        scope,
        "KnowledgeBaseVectorAccessPolicy",
        {
            name: `${collectionName}-access`,
            type: "data",
            policy: JSON.stringify([
                {
                    Rules: [
                        {
                            ResourceType: "collection",
                            Resource: [`collection/${collectionName}`],
                            Permission: [
                                "aoss:CreateCollectionItems",
                                "aoss:DescribeCollectionItems",
                                "aoss:UpdateCollectionItems",
                            ],
                        },
                        {
                            ResourceType: "index",
                            Resource: [`index/${collectionName}/*`],
                            Permission: [
                                "aoss:CreateIndex",
                                "aoss:DeleteIndex",
                                "aoss:DescribeIndex",
                                "aoss:ReadDocument",
                                "aoss:UpdateIndex",
                                "aoss:WriteDocument",
                            ],
                        },
                    ],
                    Principal: [
                        knowledgeBaseRole.roleArn,
                        cloudFormationExecutionRoleArn,
                    ],
                },
            ]),
        },
    );
    const index = new opensearchserverless.CfnIndex(
        scope,
        "KnowledgeBaseVectorIndex",
        {
            collectionEndpoint: collection.attrCollectionEndpoint,
            indexName: VECTOR_INDEX_NAME,
            settings: {
                index: {
                    knn: true,
                },
            },
            mappings: {
                properties: {
                    [VECTOR_FIELD_NAME]: {
                        type: "knn_vector",
                        dimension: EMBEDDING_VECTOR_DIMENSION,
                        method: {
                            name: "hnsw",
                            engine: "faiss",
                            spaceType: "l2",
                        },
                    },
                    [TEXT_FIELD_NAME]: {
                        type: "text",
                        index: true,
                    },
                    [METADATA_FIELD_NAME]: {
                        type: "text",
                        index: false,
                    },
                },
            },
        },
    );
    index.addDependency(collection);
    index.addDependency(accessPolicy);

    return {
        collection,
        index,
    };
}
