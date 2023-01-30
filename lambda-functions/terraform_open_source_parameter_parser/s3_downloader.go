package main

import (
	"io"
	"log"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
)

type Downloader interface {
	Download(w io.WriterAt, input *s3.GetObjectInput, options ...func(*s3manager.Downloader)) (n int64, err error)
}

type S3Downloader struct {
	downloader Downloader
}

func NewS3Downloader(creds *credentials.Credentials) (*S3Downloader, error) {
	// create a new AWS session with provided credentials
	sess, err := session.NewSession(&aws.Config{Credentials: creds})
	if err != nil {
		return &S3Downloader{}, err
	}

	// create a new downloader using above session
	return &S3Downloader{downloader: s3manager.NewDownloader(sess)}, nil
}

// Downloads artifact from specified S3 bucket and objectPath in a byte array
func (client *S3Downloader) download(bucket string, objectPath string) ([]byte, error) {
	// open byte array as download target
	buff := &aws.WriteAtBuffer{}

	// download to buffer
	log.Printf("Downloading %s from bucket %s", objectPath, bucket)
	numBytes, err := client.downloader.Download(buff,
		&s3.GetObjectInput{
			Bucket: aws.String(bucket),
			Key:    aws.String(objectPath),
		},
	)
	if err != nil {
		return []byte{}, err
	}

	log.Printf("Downloaded %d bytes", numBytes)
	return buff.Bytes(), nil
}
