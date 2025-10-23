import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambda_python from "@aws-cdk/aws-lambda-python-alpha";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as ses from "aws-cdk-lib/aws-ses";
import * as ses_actions from "aws-cdk-lib/aws-ses-actions";
import { Construct } from "constructs";
import * as path from "path";

export interface LAKEEmailProcessorProps {
  dataBucket: s3.IBucket;
  emailDomain: string;
  allowedDomains: string[];
}

export class LAKEEmailProcessor extends Construct {
  public readonly emailBucket: s3.Bucket;
  public readonly emailProcessorFunction: lambda.Function;
  public readonly uploadReceiptRule: ses.ReceiptRule;
  public readonly reportsReceiptRule: ses.ReceiptRule;

  constructor(scope: Construct, id: string, props: LAKEEmailProcessorProps) {
    super(scope, id);

    const uniqueId = cdk.Names.uniqueId(this).slice(-8);

    // Create S3 bucket for email storage
    this.emailBucket = new s3.Bucket(this, "EmailBucket", {
      bucketName: `lake-email-${uniqueId}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      versioned: false,
      encryption: s3.BucketEncryption.S3_MANAGED,
      eventBridgeEnabled: true,
      lifecycleRules: [
        {
          id: "EmailLifecycle",
          enabled: true,
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30),
            },
          ],
          expiration: cdk.Duration.days(90),
        },
      ],
    });

    // Create log group for email processor
    const logGroup = new logs.LogGroup(this, "EmailProcessorFunctionLog", {
      logGroupName: `/aws/lambda/lake-email-processor-${uniqueId}`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda function for email processing
    this.emailProcessorFunction = new lambda_python.PythonFunction(
      this,
      "EmailProcessorFunction",
      {
        functionName: `lake-email-processor-${uniqueId}`,
        runtime: lambda.Runtime.PYTHON_3_12,
        entry: path.join(__dirname, "../../lambda/email-processor"),
        index: "src/handler.py",
        handler: "lambda_handler",
        bundling: {
          bundlingFileAccess: cdk.BundlingFileAccess.VOLUME_COPY,
          assetExcludes: [".venv", "__pycache__", ".pytest_cache", "*.pyc"],
        },
        timeout: cdk.Duration.seconds(300),
        memorySize: 512,
        logGroup: logGroup,
        environment: {
          EMAIL_BUCKET_NAME: this.emailBucket.bucketName,
          DATA_BUCKET_NAME: props.dataBucket.bucketName,
          EMAIL_DOMAIN: props.emailDomain,
          ALLOWED_DOMAINS: props.allowedDomains.join(","),
        },
      }
    );

    // Grant permissions to email processor
    this.emailBucket.grantReadWrite(this.emailProcessorFunction);
    props.dataBucket.grantReadWrite(this.emailProcessorFunction);

    // Grant SES permissions
    this.emailProcessorFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "ses:SendEmail",
          "ses:SendRawEmail",
          "ses:SendTemplatedEmail",
        ],
        resources: ["*"],
      })
    );

    // EventBridge rule for email processing
    const emailEventRule = new events.Rule(this, "EmailProcessingRule", {
      ruleName: `lake-email-processing-rule-${uniqueId}`,
      description: "Trigger Lambda when emails are received in S3",
      eventPattern: {
        source: ["aws.s3"],
        detailType: ["Object Created"],
        detail: {
          bucket: {
            name: [this.emailBucket.bucketName],
          },
          object: {
            key: [
              {
                prefix: "inbound/",
              },
            ],
          },
        },
      },
    });

    emailEventRule.addTarget(
      new targets.LambdaFunction(this.emailProcessorFunction, {
        retryAttempts: 2,
      })
    );

    // Create SES receipt rule set
    const ruleSet = new ses.ReceiptRuleSet(this, "LAKEEmailRuleSet", {
      receiptRuleSetName: `lake-email-rules-${uniqueId}`,
    });

    // Receipt rule for upload emails
    this.uploadReceiptRule = new ses.ReceiptRule(this, "UploadReceiptRule", {
      ruleSet: ruleSet,
      recipients: [`upload@${props.emailDomain}`],
      actions: [
        new ses_actions.S3({
          bucket: this.emailBucket,
          objectKeyPrefix: "inbound/upload/",
        }),
      ],
    });

    // Receipt rule for reports emails
    this.reportsReceiptRule = new ses.ReceiptRule(this, "ReportsReceiptRule", {
      ruleSet: ruleSet,
      recipients: [`reports@${props.emailDomain}`],
      actions: [
        new ses_actions.S3({
          bucket: this.emailBucket,
          objectKeyPrefix: "inbound/reports/",
        }),
      ],
    });
  }
}
