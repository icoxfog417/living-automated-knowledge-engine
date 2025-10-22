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

export interface MetadataAnalyticsAgentProps {
  targetBucket: s3.IBucket;
  schedule?: events.Schedule;
}

export class MetadataAnalyticsAgent extends Construct {
  public readonly lambdaFunction: lambda.Function;
  public readonly scheduledRule: events.Rule;

  constructor(
    scope: Construct,
    id: string,
    props: MetadataAnalyticsAgentProps
  ) {
    super(scope, id);

    // Default schedule: daily at 1:00 AM UTC
    const schedule =
      props.schedule ||
      events.Schedule.cron({
        minute: "0",
        hour: "1",
        day: "*",
        month: "*",
        year: "*",
      });

    // Create log group with proper removal policy
    const logGroup = new logs.LogGroup(this, "MetadataAnalyticsFunctionLog", {
      logGroupName: `/aws/lambda/lake-metadata-analytics-${cdk.Names.uniqueId(
        this
      ).slice(-8)}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda function for metadata analytics
    this.lambdaFunction = new lambda_python.PythonFunction(
      this,
      "MetadataAnalyticsFunction",
      {
        functionName: `lake-metadata-analytics-${cdk.Names.uniqueId(this).slice(
          -8
        )}`,
        runtime: lambda.Runtime.PYTHON_3_12,
        entry: path.join(__dirname, "../../lambda/metadata-analytics"),
        index: "src/handler.py",
        handler: "lambda_handler",
        bundling: {
          bundlingFileAccess: cdk.BundlingFileAccess.VOLUME_COPY,
          assetExcludes: [
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "*.pyc",
            ".coverage",
            ".ruff_cache",
            "tests",
            "example.py",
          ],
        },
        timeout: cdk.Duration.minutes(15),
        memorySize: 1536, // Increased for AI agent operations with CodeInterpreter
        logGroup: logGroup,
        environment: {
          BUCKET_NAME: props.targetBucket.bucketName,
        },
      }
    );

    // Grant S3 read and write permissions to Lambda
    props.targetBucket.grantRead(this.lambdaFunction);
    props.targetBucket.grantPut(this.lambdaFunction);

    // Grant Bedrock permissions for AI agent operations
    this.lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // Grant Bedrock AgentCore permissions for CodeInterpreter tool
    this.lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:CreateKnowledgeBase",
          "bedrock:CreateAgent",
          "bedrock:CreateAgentActionGroup",
          "bedrock:InvokeAgent",
          "bedrock:PrepareAgent",
        ],
        resources: ["*"],
      })
    );

    // CloudWatch Events rule for scheduled execution
    this.scheduledRule = new events.Rule(this, "ScheduledAnalyticsRule", {
      ruleName: `lake-metadata-analytics-schedule-${cdk.Names.uniqueId(
        this
      ).slice(-8)}`,
      description:
        "Trigger metadata analytics Lambda function on a schedule (daily analysis of previous 24 hours)",
      schedule: schedule,
    });

    // Add Lambda as target
    this.scheduledRule.addTarget(
      new targets.LambdaFunction(this.lambdaFunction, {
        retryAttempts: 2,
      })
    );
  }
}
