package main

import (
	"errors"
	"io"
	"reflect"
	"testing"

	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
	"github.com/stretchr/testify/mock"
)

const TestString = "hello world"
const TestBucketHappy = "testBucketHappy"
const TestBucketError = "testBucketError"
const TestObjectPath = "testObjectPath"
const S3ClientErrorMessage = "s3 client error"

type MockDownloader struct {
	mock.Mock
}

func (m *MockDownloader) Download(w io.WriterAt, input *s3.GetObjectInput, options ...func(*s3manager.Downloader)) (n int64, err error) {
	num, _ := w.WriteAt([]byte(TestString), 0)

	if *input.Bucket == TestBucketError {
		return 0, errors.New(S3ClientErrorMessage)
	}

	return int64(num), nil
}

func TestS3DownloaderDownloadHappy(t *testing.T) {
	// setup
	downloader := new(MockDownloader)
	s3Downloader := &S3Downloader{
		downloader: downloader,
	}
	expectedResult := []byte(TestString)

	// act
	actualResult, err := s3Downloader.download(TestBucketHappy, TestObjectPath)

	// assert
	if err != nil {
		t.Errorf("Unexpected error occurred")
	}

	if !reflect.DeepEqual(actualResult, expectedResult) {
		t.Errorf("Returned byte array is not the same as expected")
	}
}

func TestS3DownloaderDownloadClientError(t *testing.T) {
	// setup
	downloader := new(MockDownloader)
	s3Downloader := &S3Downloader{
		downloader: downloader,
	}

	// act
	_, err := s3Downloader.download(TestBucketError, TestObjectPath)

	// assert
	if err.Error() != S3ClientErrorMessage {
		t.Errorf("Error is not the same as expected")
	}
}
