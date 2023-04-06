package main

import (
	"github.com/aws/aws-lambda-go/lambda"
)

type TerraformOpenSourceParameterParserInput struct {
	Artifact Artifact `json:"artifact"`
	LaunchRoleArn string `json:"launchRoleArn"`
}

type TerraformOpenSourceParameterParserResponse struct {
	Parameters []*Parameter `json:"parameters"`
}

func main() {
	lambda.Start(HandleRequest)
}

func HandleRequest(event TerraformOpenSourceParameterParserInput) (TerraformOpenSourceParameterParserResponse, error) {
	if err := ValidateInput(event); err != nil {
		return TerraformOpenSourceParameterParserResponse{}, err
	}

	configFetcher, configFetcherErr := NewConfigFetcher(event.LaunchRoleArn)
	if configFetcherErr != nil {
		return TerraformOpenSourceParameterParserResponse{}, configFetcherErr
	}

	fileMap, fileMapErr := configFetcher.fetch(event)
	if fileMapErr != nil {
		return TerraformOpenSourceParameterParserResponse{}, fileMapErr
	}

	parameters, parseParametersErr := ParseParametersFromConfiguration(fileMap)
	return TerraformOpenSourceParameterParserResponse{Parameters: parameters}, parseParametersErr
}
