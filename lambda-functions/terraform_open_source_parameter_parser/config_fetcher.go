package main

import (
	"fmt"
	"log"
	"strings"

	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/credentials/stscreds"
	"github.com/aws/aws-sdk-go/aws/session"
)

const LaunchRoleAccessDeniedErrorMessage = "Access denied while assuming launch role %s: %s"
const ArtifactFetchAccessDeniedErrorMessage = "Access denied while downloading artifact from %s: %s"
const UnzipFailureErrorMessage = "Artifact from %s is not a valid tar.gz file: %s"

type ConfigFetcher struct {
	s3Downloader *S3Downloader
}

func NewConfigFetcher(launchRoleArn string) (*ConfigFetcher, error) {
	s3Downloader, err := NewS3Downloader(retrieveConfigFetcherCreds(launchRoleArn))
	if err != nil {
		return &ConfigFetcher{},
		ParserAccessDeniedException{Message: fmt.Sprintf(LaunchRoleAccessDeniedErrorMessage, launchRoleArn, err.Error())}
	}

	return &ConfigFetcher{s3Downloader: s3Downloader}, nil
}

// Fetches the input file from artifact location and outputs as a map of the file's name to its contents in string format
func (c *ConfigFetcher) fetch(input TerraformOpenSourceParameterParserInput) (map[string]string, error) {
	bucket, key := resolveArtifactPath(input.Artifact.Path)

	configBytes, err := c.s3Downloader.download(bucket, key)
	if err != nil {
		return map[string]string{},
		ParserAccessDeniedException{Message: fmt.Sprintf(ArtifactFetchAccessDeniedErrorMessage, input.Artifact.Path, err.Error())}
	}

	fileMap, err := UnzipArchive(configBytes)
	if err != nil {
		return fileMap,
		ParserInvalidParameterException{Message: fmt.Sprintf(UnzipFailureErrorMessage, input.Artifact.Path, err.Error())}
	}

	return fileMap, nil
}

func retrieveConfigFetcherCreds(launchRoleArn string) *credentials.Credentials {
	// use default lambda execution role creds to retrieve configuration templates if launch role is not provided
	if launchRoleArn == "" {
		log.Print("Launch role is not provided. Using default ServiceCatalogTerraformOSParameterParserRole credentials to fetch artifact.")
		return credentials.NewEnvCredentials()
	} else {
		log.Printf("Using launch role %s credentials to fetch artifact.", launchRoleArn)
		return retrieveLaunchRoleCreds(launchRoleArn)
	}
}

// Assumes provided launchRoleArn and return its credentials
func retrieveLaunchRoleCreds(launchRoleArn string) *credentials.Credentials {
	sess := session.Must(session.NewSession())
	return stscreds.NewCredentials(sess, launchRoleArn)
}

// Resolves artifactPath to bucket and key
func resolveArtifactPath(artifactPath string) (string, string) {
	bucket := strings.Split(artifactPath, "/")[2]
	key := strings.SplitN(artifactPath, "/", 4)[3]
	return bucket, key
}
