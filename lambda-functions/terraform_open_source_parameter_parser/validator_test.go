package main

import (
	"fmt"
	"reflect"
	"testing"
)

func TestValidateInputHappy(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: TestArtifactType,
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}

	// act
	err := ValidateInput(input)

	// assert
	if err != nil {
		t.Errorf("Validation failed for happy path input")
	}
}

func TestValidateInputWithEmptyLaunchRoleHappy(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: TestArtifactType,
		},
		LaunchRoleArn: "",
	}

	// act
	err := ValidateInput(input)

	// assert
	if err != nil {
		t.Errorf("Validation failed for happy path input with empty launch role")
	}
}

func TestValidateInputWithEmptyArtifactThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{},
		LaunchRoleArn: TestLaunchRoleArn,
	}
	expectedErrorMessage := fmt.Sprintf(RequiredKeyMissingOrEmptyErrorMessage, ArtifactKey)

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithEmptyArtifactPathThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: "",
			Type: TestArtifactType,
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}
	expectedErrorMessage := fmt.Sprintf(RequiredKeyMissingOrEmptyErrorMessage, ArtifactPathKey)

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithEmptyArtifactTypeThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: "",
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}
	expectedErrorMessage := fmt.Sprintf(RequiredKeyMissingOrEmptyErrorMessage, ArtifactTypeKey)

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithSyntacticallyIncorrectArnThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: TestArtifactType,
		},
		LaunchRoleArn: "fakeArn",
	}
	expectedErrorMessage := fmt.Sprintf(InvalidLaunchRoleArnSyntaxErrorMessage, "fakeArn")

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithNonIamArnThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: TestArtifactType,
		},
		LaunchRoleArn: "arn:aws:sts::829064435212:role/SCLaunchRole",
	}
	expectedErrorMessage := fmt.Sprintf(InvalidIamLaunchRoleArnErrorMessage, "arn:aws:sts::829064435212:role/SCLaunchRole")

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithNonDefaultArtifactTypeThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: TestArtifactPath,
			Type: "fakeType",
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}
	expectedErrorMessage := fmt.Sprintf(InvalidArtifactTypeErrorMessage, "fakeType")

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithInvalidArtifactPathThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: "invalidPath",
			Type: TestArtifactType,
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}
	expectedErrorMessage := fmt.Sprintf(InvalidArtifactPathErrorMessage, "invalidPath")

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}

func TestValidateInputWithNoneS3ArtifactPathThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	input := TerraformOpenSourceParameterParserInput{
		Artifact: Artifact{
			Path: "https://terraform-configurations-cross-account-demo/product_with_override_var.tar.gz",
			Type: TestArtifactType,
		},
		LaunchRoleArn: TestLaunchRoleArn,
	}
	expectedErrorMessage := fmt.Sprintf(InvalidArtifactPathErrorMessage, "https://terraform-configurations-cross-account-demo/product_with_override_var.tar.gz")

	// act
	err := ValidateInput(input)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}
