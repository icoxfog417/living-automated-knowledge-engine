import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambda_python from "@aws-cdk/aws-lambda-python-alpha";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import * as path from "path";

export interface LAKEAgentProps {
  targetBucket: s3.IBucket;
}

export class LAKEAgent extends Construct {
  public readonly lambdaFunction: lambda.Function;
  public readonly eventRule: events.Rule;

  constructor(scope: Construct, id: string, props: LAKEAgentProps) {
    super(scope, id);

    // Create log group with proper removal policy
    const logGroup = new logs.LogGroup(this, "MetadataGeneratorFunctionLog", {
      logGroupName: `/aws/lambda/lake-metadata-generator-${cdk.Names.uniqueId(
        this
      ).slice(-8)}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda function for metadata generation
    this.lambdaFunction = new lambda_python.PythonFunction(
      this,
      "MetadataGeneratorFunction",
      {
        functionName: `lake-metadata-generator-${cdk.Names.uniqueId(this).slice(
          -8
        )}`,
        runtime: lambda.Runtime.PYTHON_3_12,
        entry: path.join(__dirname, "../../lambda/metadata-generator"),
        index: "src/handler.py",
        handler: "lambda_handler",
        bundling: {
          bundlingFileAccess: cdk.BundlingFileAccess.VOLUME_COPY,
          assetExcludes: [".venv", "__pycache__", ".pytest_cache", "*.pyc"],
        },
        timeout: cdk.Duration.seconds(60),
        memorySize: 256,
        logGroup: logGroup,
        environment: {
          BUCKET_NAME: props.targetBucket.bucketName,
        },
      }
    );

    // Grant S3 read/write permissions to Lambda
    props.targetBucket.grantReadWrite(this.lambdaFunction);

    // Grant Bedrock permissions to Lambda
    this.lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      })
    );

    // EventBridge rule for S3 Object Created events
    this.eventRule = new events.Rule(this, "S3ObjectCreatedRule", {
      ruleName: `lake-s3-object-created-rule-${cdk.Names.uniqueId(this).slice(
        -8
      )}`,
      description:
        "Trigger Lambda when objects are uploaded to S3 (excluding .metadata.json files)",
      eventPattern: {
        source: ["aws.s3"],
        detailType: ["Object Created"],
        detail: {
          bucket: {
            name: [props.targetBucket.bucketName],
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
    this.eventRule.addTarget(
      new targets.LambdaFunction(this.lambdaFunction, {
        retryAttempts: 2,
      })
    );
  }
}
