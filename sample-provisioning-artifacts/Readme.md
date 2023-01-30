# Terraform Reference Engine Sample Provisioning Artifacts

This directory contains sample provisioning artifacts that can be used to test a deployment of the Terraform Reference Engine.

## Simple S3 Bucket

File: s3bucket.tar.gz

### Provisioning Parameters

* bucket_name

### Resources

* A simple S3 bucket with default settings

### Launch Role Permissions

The following permissions are required in the product's launch role in order to provision, update, terminate and tag.

* S3 permissions to manage a bucket's lifecycle
* S3 permissions to tag a bucket. This allows the engine to set its tracer tag on the resource. The tracer tag is used by Service Catalog to identify the resources belonging to the provisioned product.
* Resource group and tagging permissions: This is required for every launch role on a terraform open source product. Service Catalog requires these permissions to apply system and user tags to the resources.

Example:

```
            Statement:
              - Effect: Allow
                Action: 
                  - s3:CreateBucket*
                  - s3:DeleteBucket*
                  - s3:Get*
                  - s3:List*
                  - s3:PutBucketTagging
                Resource: "arn:aws:s3:::*"
              - Effect: Allow
                Action: 
                  - resource-groups:CreateGroup
                  - resource-groups:ListGroupResources
                Resource: "*"
              - Effect: Allow
                Action: 
                  - tag:GetResources
                  - tag:GetTagKeys
                  - tag:GetTagValues
                  - tag:TagResources
                  - tag:UntagResources
                Resource: "*"
```

## S3 Bucket and Notification Topic Using Modules

File: s3website-module.tar.gz

This provisioning artifact is an example of using Terraform modules. It contains a local module for S3 resources and a remote module for SNS resources.

### Provisioning Parameters

* bucket_name
* topic_name


### Resources

* A simple S3 bucket with default settings
* A website configuration on the bucket
* A simple SNS topic with default settings
* A bucket notification configuration for the bucket and topic

### Launch Role Permissions

The following permissions are required in the product's launch role in order to provision, update, terminate, and tag.

* S3 permissions to manage a bucket's lifecycle, including website and notification configuration
* SNS permissions to manage a topic's lifecycle
* S3 and SNS permissions to tag resources. This allows the engine to set its tracer tag on the resources. The tracer tag is used by Service Catalog to identify the resources belonging to the provisioned product.
* Resource group and tagging permissions: This is required for every launch role on a terraform open source product. Service Catalog requires these permissions to apply system and user tags to the resources.

Example:

```
            Statement:
              - Effect: Allow
                Action: 
                  - s3:CreateBucket*
                  - s3:DeleteBucket*
                  - s3:Get*
                  - s3:List*
                  - s3:PutBucketNotification
                  - s3:PutBucketWebsite
                  - s3:PutBucketTagging
                Resource: "arn:aws:s3:::*"
              - Effect: Allow
                Action: 
                  - sns:CreateTopic
                  - sns:DeleteTopic
                  - sns:GetTopicAttributes
                  - sns:SetTopicAttributes
                  - sns:ListTagsForResource
                  - sns:TagResource
                Resource: "*"
              - Effect: Allow
                Action: 
                  - resource-groups:CreateGroup
                  - resource-groups:ListGroupResources
                Resource: "*"
              - Effect: Allow
                Action: 
                  - tag:GetResources
                  - tag:GetTagKeys
                  - tag:GetTagValues
                  - tag:TagResources
                  - tag:UntagResources
                Resource: "*"
```
