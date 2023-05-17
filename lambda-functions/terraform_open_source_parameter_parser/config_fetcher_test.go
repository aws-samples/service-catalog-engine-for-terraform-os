package main

import (
	"errors"
	"io"
	"os"
	"reflect"
	"testing"

	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
	"github.com/stretchr/testify/mock"
)

const TestArtifactPath = "s3://terraform-configurations-cross-account-demo/product_with_override_var.tar.gz"
const TestArtifactType = "AWS_S3"
const TestLaunchRoleArn = "arn:aws:iam::829064435212:role/SCLaunchRole"
const TestS3BucketArtifactPath = "../../sample-provisioning-artifacts/s3bucket.tar.gz"
const TestS3BucketArtifactFileName = "main.tf"
const TestS3BucketArtifactFileContent = "\"bucket_name\" {\n  type = string\n}\nprovider \"aws\" {\n}\nresource \"aws_s3_bucket\" \"bucket\" {\n  bucket = var.bucket_name\n}\noutput regional_domain_name {\n  value = aws_s3_bucket.bucket.bucket_regional_domain_name\n}"

type MockS3Downloader struct {
	mock.Mock
}

func (m *MockS3Downloader) Download(w io.WriterAt, input *s3.GetObjectInput, options ...func(*s3manager.Downloader)) (n int64, err error) {
	if *input.Bucket != "terraform-configurations-cross-account-demo" || *input.Key != "product_with_override_var.tar.gz" {
		return 0, errors.New(S3ClientErrorMessage)
	}

	b, _ := os.ReadFile(TestS3BucketArtifactPath)
	numBytes, _ := w.WriteAt(b, 0)
	return int64(numBytes), nil
}

func TestConfigFetcherFetchHappy(t *testing.T) {
	// setup
	downloader := new(MockS3Downloader)
	s3Downloader := &S3Downloader{
		downloader: downloader,
	}
	configFetcher := &ConfigFetcher{
		s3Downloader: s3Downloader,
	}
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: TestArtifactType,
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}

	// act
	fileMap, err := configFetcher.fetch(input)

	// assert
	if err != nil {
		t.Errorf("Unexpected error occured")
	}

	fileContent, ok := fileMap[TestS3BucketArtifactFileName]
	if !ok {
		t.Errorf("Expected file %s was not parsed", TestS3BucketArtifactFileName)
	}

	if reflect.DeepEqual(fileContent, TestS3BucketArtifactFileContent) {
		t.Errorf("File content for %s is not as expected", TestS3BucketArtifactFileName)
	}
}

func TestConfigFetcherFetchWithEmptyLaunchRoleHappy(t *testing.T) {
	// setup
	downloader := new(MockS3Downloader)
	s3Downloader := &S3Downloader{
		downloader: downloader,
	}
	configFetcher := &ConfigFetcher{
		s3Downloader: s3Downloader,
	}
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: TestArtifactType,
		},
		LaunchRoleArn: "",
	}

	// act
	fileMap, err := configFetcher.fetch(input)

	// assert
	if err != nil {
		t.Errorf("Unexpected error occured")
	}

	fileContent, ok := fileMap[TestS3BucketArtifactFileName]
	if !ok {
		t.Errorf("Expected file %s was not parsed", TestS3BucketArtifactFileName)
	}

	if reflect.DeepEqual(fileContent, TestS3BucketArtifactFileContent) {
		t.Errorf("File content for %s is not as expected", TestS3BucketArtifactFileName)
	}
}
