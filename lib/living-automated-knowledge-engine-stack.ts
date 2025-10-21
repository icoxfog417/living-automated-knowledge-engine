import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { LAKEAgent } from "./constructs/lake-agent";

export class LivingAutomatedKnowledgeEngineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Read configuration from cdk.json
    const lakeConfig = this.node.tryGetContext('lake') || {};
    const existingBucketName = lakeConfig.existingBucketName;

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

    new cdk.CfnOutput(this, "LAKEAgentFunctionArn", {
      value: lakeAgent.lambdaFunction.functionArn,
      description: "Lambda function ARN for metadata generation",
    });

    new cdk.CfnOutput(this, "LAKEAgentEventRuleArn", {
      value: lakeAgent.eventRule.ruleArn,
      description: "EventBridge Rule ARN for S3 object created events",
    });
  }
}
