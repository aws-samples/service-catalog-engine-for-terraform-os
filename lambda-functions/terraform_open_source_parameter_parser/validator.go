package main

import (
	"fmt"
	"net/url"
	"reflect"

	"github.com/aws/aws-sdk-go/aws/arn"
)

const ArtifactKey = "Artifact"
const LaunchRoleArnKey = "LaunchRoleArn"
const ArtifactPathKey = "Artifact.Path"
const ArtifactTypeKey = "Artifact.Type"

const DefaultArtifactType = "AWS_S3"
const IamArnServiceKey = "iam"
const S3Scheme = "s3"

const RequiredKeyMissingOrEmptyErrorMessage = "%s is required and must be non empty"
const InvalidLaunchRoleArnSyntaxErrorMessage = "LaunchRoleArn %s is not a syntactically valid ARN"
const InvalidIamLaunchRoleArnErrorMessage = "LaunchRoleArn %s is not a valid iam ARN"
const InvalidArtifactTypeErrorMessage = "Artifact type %s is not supported, must be AWS_S3"
const InvalidArtifactPathErrorMessage = "Artifact path %s is not a valid S3 URI"

// ValidateInput - Validates TerraformOpenSourceParameterParserInput
// Returns a non nil error if an invalid input is provided
func ValidateInput(input TerraformOpenSourceParameterParserInput) error {
	// validate required keys exist in the input
	if err := validateRequiredKeysExist(input); err != nil {
		return err
	}

	// validate the format of LaunchRoleArn
	if err := validateLaunchRoleArnIsSyntacticallyCorrect(input.LaunchRoleArn); err != nil {
		return err
	}

	// validate the Artifact
	if err := validateArtifact(input.Artifact); err != nil {
		return err
	}

	return nil
}

func validateRequiredKeysExist(input TerraformOpenSourceParameterParserInput) error {
	if reflect.DeepEqual(input.Artifact, Artifact{}) {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(RequiredKeyMissingOrEmptyErrorMessage, ArtifactKey),
		}
	}

	if input.Artifact.Path == "" {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(RequiredKeyMissingOrEmptyErrorMessage, ArtifactPathKey),
		}
	}

	if input.Artifact.Type == "" {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(RequiredKeyMissingOrEmptyErrorMessage, ArtifactTypeKey),
		}
	}

	return nil
}

func validateLaunchRoleArnIsSyntacticallyCorrect(launchRoleArnString string) error {

	// skip validation if launch role is not provided
	if launchRoleArnString == "" {
		return nil
	}

	launchRoleArn, err := arn.Parse(launchRoleArnString)
	if err != nil {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(InvalidLaunchRoleArnSyntaxErrorMessage, launchRoleArnString),
		}
	}

	if launchRoleArn.Service != IamArnServiceKey {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(InvalidIamLaunchRoleArnErrorMessage, launchRoleArnString),
		}
	}

	return nil
}

func validateArtifact(artifact Artifact) error {
	if artifact.Type != DefaultArtifactType {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(InvalidArtifactTypeErrorMessage, artifact.Type),
		}
	}

	artifactUri, err := url.Parse(artifact.Path)
	if err != nil {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(InvalidArtifactPathErrorMessage, artifact.Path),
		}
	}

	if artifactUri.Scheme != S3Scheme || artifactUri.Host == "" || artifactUri.Path == "" {
		return ParserInvalidParameterException{
			Message: fmt.Sprintf(InvalidArtifactPathErrorMessage, artifact.Path),
		}
	}

	return nil
}
