import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambda_python from "@aws-cdk/aws-lambda-python-alpha";
import * as iam from "aws-cdk-lib/aws-iam";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import * as path from "path";

export class LivingAutomatedKnowledgeEngineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 Bucket for data storage
    const dataBucket = new s3.Bucket(this, "DataBucket", {
      bucketName: `lake-data-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: false,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      eventBridgeEnabled: true,
    });

    // Lambda Function for metadata generation
    const metadataGeneratorFunction = new lambda_python.PythonFunction(
      this,
      "MetadataGeneratorFunction",
      {
        functionName: "lake-metadata-generator",
        runtime: lambda.Runtime.PYTHON_3_12,
        entry: path.join(__dirname, "../lambda/metadata-generator"),
        index: "src/handler.py",
        handler: "lambda_handler",
        bundling: {
          bundlingFileAccess: cdk.BundlingFileAccess.VOLUME_COPY,
        },
        timeout: cdk.Duration.seconds(60),
        memorySize: 256,
        environment: {
          BUCKET_NAME: dataBucket.bucketName,
        },
      }
    );

    // Grant S3 read/write permissions to Lambda
    dataBucket.grantReadWrite(metadataGeneratorFunction);

    // Grant Bedrock permissions to Lambda
    metadataGeneratorFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock:InvokeModel"],
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0`,
        ],
      })
    );

    // EventBridge Rule for S3 Object Created events
    const s3EventRule = new events.Rule(this, "S3ObjectCreatedRule", {
      ruleName: "lake-s3-object-created-rule",
      description:
        "Trigger Lambda when objects are uploaded to S3 (excluding .metadata.json files)",
      eventPattern: {
        source: ["aws.s3"],
        detailType: ["Object Created"],
        detail: {
          bucket: {
            name: [dataBucket.bucketName],
          },
          object: {
            key: [
              {
                "anything-but": {
                  suffix: ".metadata.json",
                },
              },
            ],
          },
        },
      },
    });

    // Add Lambda as target
    s3EventRule.addTarget(
      new targets.LambdaFunction(metadataGeneratorFunction, {
        retryAttempts: 2,
      })
    );

    // Output the bucket name and Lambda function ARN
    new cdk.CfnOutput(this, "DataBucketName", {
      value: dataBucket.bucketName,
      description: "S3 Bucket for data storage",
    });

    new cdk.CfnOutput(this, "MetadataGeneratorFunctionArn", {
      value: metadataGeneratorFunction.functionArn,
      description: "Lambda function ARN for metadata generation",
    });

    new cdk.CfnOutput(this, "S3EventRuleArn", {
      value: s3EventRule.ruleArn,
      description: "EventBridge Rule ARN for S3 object created events",
    });
  }
}
