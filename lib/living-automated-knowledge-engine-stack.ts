import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { LAKEAgent } from "./constructs/lake-agent";
import { LAKEEmailProcessor } from "./constructs/lake-email-processor";

export class LivingAutomatedKnowledgeEngineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Read configuration from cdk.json
    const lakeConfig = this.node.tryGetContext('lake') || {};
    const existingBucketName = lakeConfig.existingBucketName;
    const emailDomain = lakeConfig.emailDomain;
    const allowedDomains = lakeConfig.allowedDomains || [];

    let targetBucket: s3.IBucket;

    if (existingBucketName) {
      // Use existing bucket
      targetBucket = s3.Bucket.fromBucketName(
        this, "ExistingBucket", 
        existingBucketName
      );
    } else {
      // Create new bucket
      targetBucket = new s3.Bucket(this, "DataBucket", {
        bucketName: `lake-data-${this.account}-${this.region}`,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        autoDeleteObjects: false,
        versioned: true,
        encryption: s3.BucketEncryption.S3_MANAGED,
        eventBridgeEnabled: true,
      });
    }

    // Attach LAKE Agent to the bucket
    const lakeAgent = new LAKEAgent(this, "LAKEAgent", {
      targetBucket
    });

    // Add email processor if email domain is configured
    let emailProcessor: LAKEEmailProcessor | undefined;
    if (emailDomain) {
      emailProcessor = new LAKEEmailProcessor(this, "LAKEEmailProcessor", {
        dataBucket: targetBucket,
        emailDomain: emailDomain,
        allowedDomains: allowedDomains,
      });
    }

    new cdk.CfnOutput(this, "LAKEAgentFunctionArn", {
      value: lakeAgent.lambdaFunction.functionArn,
      description: "Lambda function ARN for metadata generation",
    });

    new cdk.CfnOutput(this, "LAKEAgentEventRuleArn", {
      value: lakeAgent.eventRule.ruleArn,
      description: "EventBridge Rule ARN for S3 object created events",
    });

    if (emailProcessor) {
      new cdk.CfnOutput(this, "LAKEEmailProcessorFunctionArn", {
        value: emailProcessor.emailProcessorFunction.functionArn,
        description: "Lambda function ARN for email processing",
      });

      new cdk.CfnOutput(this, "LAKEEmailBucketName", {
        value: emailProcessor.emailBucket.bucketName,
        description: "S3 bucket name for email storage",
      });

      new cdk.CfnOutput(this, "LAKEUploadEmailAddress", {
        value: `upload@${emailDomain}`,
        description: "Email address for document uploads",
      });

      new cdk.CfnOutput(this, "LAKEReportsEmailAddress", {
        value: `reports@${emailDomain}`,
        description: "Email address for metadata reports",
      });
    }
  }
}
