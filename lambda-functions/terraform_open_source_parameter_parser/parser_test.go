package main

import (
	"reflect"
	"testing"
)

const PrimaryFileName1 = "main.tf"
const PrimaryFileName2 = "variables.tf"
const OverrideFileName = "override.tf"
const ComprehensiveVariableFileName = "comprehensive_variables.tf"
const PrimaryFileContent1 = "provider \"aws\" {\n    region = \"us-east-1\"\n}\n\nvariable \"instance_name\" {\n    type = string\n    default = \"my_vm\"\n    validation {\n        condition = (\n            length(var.instance_name) > 4\n        )\n        error_message = \"The supplied instance_name should be at least 4 characters.\"\n    }\n}\n\nresource \"aws_instance\" \"my_vm\" {\n    ami = \"ami-0742b4e673072066f\"\n    instance_type = \"t3.micro\"\n    tags = {\n        Name = var.instance_name\n    }\n}\n\noutput \"vm_ip_addr\" {\n  value = aws_instance.my_vm.private_ip\n}\n"
const PrimaryFileContent2 = "provider \"aws\" {\n    region = \"us-east-1\"\n}\n\nvariable \"test_variable_number\" {\n    type = number\n    description = \"The variable in a number type\"\n    sensitive = true\n    nullable = true\n}\n\nvariable \"test_variable_complex_type\" {\n    type = object({\n        create_rg = bool\n        name      = string\n        location  = string\n    })\n    default = {\n        create_rg = true\n        name = \"default_name\"\n        location = \"default_location\"\n    }\n    description = \"The variable in a complex type\"\n}"
const OverrideFileContent = "variable \"instance_name\" {\n    type = string\n    default = \"name from override file\"\n}\n\nvariable \"test_variable_number\" {\n    type = string\n    description = \"The variable in a string type in override file\"\n    sensitive = false\n}\n\nvariable \"test_variable_complex_type\" {\n    sensitive = true\n}\n\nvariable \"new_variable_from_override\" {\n\ttype = string\n    description = \"A new variable\"\n    default = \"hello\"\n    sensitive = true\n}"
const ComprehensiveVariableFileContent = "provider \"aws\" {\n    region = \"us-east-1\"\n}\n\nvariable \"string_variable\" {\n    type = string\n    default = \"hello world\"\n}\n\nvariable \"number_variable\" {\n    type = number\n    default = 100\n}\n\nvariable \"bool_variable\" {\n    type = bool\n    default = true\n}\n\nvariable \"list_variable\" {\n    type = list(string)\n    default = [\"hello\", \"world\"]\n}\n\nvariable \"set_variable\" {\n    type = set(number)\n    default = [1, 2]\n}\n\nvariable \"map_variable\" {\n    type = map(string)\n    default = {\n        k1 = \"v1\"\n        k2 = \"v2\"\n        k3 = \"v3\"\n    }\n}\n\nvariable \"object_variable\" {\n    type = object({\n        create_rg = bool\n        name      = string\n        location  = string\n    })\n    default = {\n        create_rg = true\n        name = \"default_name\"\n        location = \"default_location\"\n    }\n}\n\nvariable \"tuple_variable\" {\n    type = tuple([string,string,bool])\n    default = [\"hello\",\"world\",false]\n}\n"

func TestParseParametersFromConfigurationHappy(t *testing.T) {
	// setup
	fileMap := make(map[string]string)
	fileMap[PrimaryFileName1] = PrimaryFileContent1
	fileMap[PrimaryFileName2] = PrimaryFileContent2

	expectedResultMap := make(map[string]*Parameter)

	expectedParameter1 := &Parameter{
		Key: "instance_name",
		DefaultValue: "my_vm",
		Type: "string",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter2 := &Parameter{
		Key: "test_variable_number",
		DefaultValue: "",
		Type: "number",
		Description: "The variable in a number type",
		IsNoEcho: true,
	}

	expectedParameter3 := &Parameter{
		Key: "test_variable_complex_type",
		DefaultValue: "{\"create_rg\":true,\"location\":\"default_location\",\"name\":\"default_name\"}",
		Type: "object({\n        create_rg = bool\n        name      = string\n        location  = string\n    })",
		Description: "The variable in a complex type",
		IsNoEcho: false,
	}

	expectedResultMap["instance_name"] = expectedParameter1
	expectedResultMap["test_variable_number"] = expectedParameter2
	expectedResultMap["test_variable_complex_type"] = expectedParameter3

	// act
	actualResult, err := ParseParametersFromConfiguration(fileMap)

	// assert
	if err != nil {
		t.Errorf("Unexpected error returned. %v", err)
	}

	// assert the number of parameters parsed is as expected
	if len(actualResult) != len(expectedResultMap) {
		t.Errorf("The number of parameters contained in the result is %v, not %v as expected", len(actualResult), len(expectedResultMap))
	}

	// assert the content of parsed parameters is as expected
	for _, actualParameter := range actualResult {
		expectedParameter, ok := expectedResultMap[actualParameter.Key]

		if ok {
			if !reflect.DeepEqual(actualParameter, expectedParameter) {
				t.Errorf("Parsed parameter with key %v is not the same as expected", actualParameter.Key)
			}
			delete(expectedResultMap, actualParameter.Key)
		} else {
			t.Errorf("Parsed parameter with key %v is not expected", actualParameter.Key)
		}
	}

	// assert all parameters were parsed
	if len(expectedResultMap) != 0 {
		t.Errorf("Not all expected parameters were parsed")
	}
}

func TestParseParametersFromConfigurationWithOverrideFilesHappy(t *testing.T) {
	// setup
	fileMap := make(map[string]string)
	fileMap[PrimaryFileName1] = PrimaryFileContent1
	fileMap[PrimaryFileName2] = PrimaryFileContent2
	fileMap[OverrideFileName] = OverrideFileContent

	expectedResultMap := make(map[string]*Parameter)

	expectedParameter1 := &Parameter{
		Key: "instance_name",
		DefaultValue: "name from override file",
		Type: "string",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter2 := &Parameter{
		Key: "test_variable_number",
		DefaultValue: "",
		Type: "string",
		Description: "The variable in a string type in override file",
		IsNoEcho: false,
	}

	expectedParameter3 := &Parameter{
		Key: "test_variable_complex_type",
		DefaultValue: "{\"create_rg\":true,\"location\":\"default_location\",\"name\":\"default_name\"}",
		Type: "object({\n        create_rg = bool\n        name      = string\n        location  = string\n    })",
		Description: "The variable in a complex type",
		IsNoEcho: true,
	}

	expectedParameter4 := &Parameter{
		Key: "new_variable_from_override",
		DefaultValue: "hello",
		Type: "string",
		Description: "A new variable",
		IsNoEcho: true,
	}

	expectedResultMap["instance_name"] = expectedParameter1
	expectedResultMap["test_variable_number"] = expectedParameter2
	expectedResultMap["test_variable_complex_type"] = expectedParameter3
	expectedResultMap["new_variable_from_override"] = expectedParameter4

	// act
	actualResult, err := ParseParametersFromConfiguration(fileMap)

	// assert
	if err != nil {
		t.Errorf("Unexpected error returned. %v", err)
	}


	// assert the number of parameters parsed is as expected
	if len(actualResult) != len(expectedResultMap) {
		t.Errorf("The number of parameters contained in the result is %v, not %v as expected", len(actualResult), len(expectedResultMap))
	}

	// assert the content of parsed parameters is as expected
	for _, actualParameter := range actualResult {
		expectedParameter, ok := expectedResultMap[actualParameter.Key]

		if ok {
			if !reflect.DeepEqual(actualParameter, expectedParameter) {
				t.Errorf("Parsed parameter with key %v is not the same as expected", actualParameter.Key)
			}
			delete(expectedResultMap, actualParameter.Key)
		} else {
			t.Errorf("Parsed parameter with key %v is not expected", actualParameter.Key)
		}
	}

	// assert all parameters were parsed
	if len(expectedResultMap) != 0 {
		t.Errorf("Not all expected parameters were parsed")
	}
}

func TestParseParametersFromConfigurationWithComprehensiveVariableFileHappy(t *testing.T) {
	// setup
	fileMap := make(map[string]string)
	fileMap[ComprehensiveVariableFileName] = ComprehensiveVariableFileContent

	expectedResultMap := make(map[string]*Parameter)

	expectedParameter1 := &Parameter{
		Key: "string_variable",
		DefaultValue: "hello world",
		Type: "string",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter2 := &Parameter{
		Key: "number_variable",
		DefaultValue: "100",
		Type: "number",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter3 := &Parameter{
		Key: "bool_variable",
		DefaultValue: "true",
		Type: "bool",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter4 := &Parameter{
		Key: "list_variable",
		DefaultValue: "[\"hello\",\"world\"]",
		Type: "list(string)",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter5 := &Parameter{
		Key: "set_variable",
		DefaultValue: "[1,2]",
		Type: "set(number)",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter6 := &Parameter{
		Key: "map_variable",
		DefaultValue: "{\"k1\":\"v1\",\"k2\":\"v2\",\"k3\":\"v3\"}",
		Type: "map(string)",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter7 := &Parameter{
		Key: "object_variable",
		DefaultValue: "{\"create_rg\":true,\"location\":\"default_location\",\"name\":\"default_name\"}",
		Type: "object({\n        create_rg = bool\n        name      = string\n        location  = string\n    })",
		Description: "",
		IsNoEcho: false,
	}

	expectedParameter8 := &Parameter{
		Key: "tuple_variable",
		DefaultValue: "[\"hello\",\"world\",false]",
		Type: "tuple([string,string,bool])",
		Description: "",
		IsNoEcho: false,
	}

	expectedResultMap["string_variable"] = expectedParameter1
	expectedResultMap["number_variable"] = expectedParameter2
	expectedResultMap["bool_variable"] = expectedParameter3
	expectedResultMap["list_variable"] = expectedParameter4
	expectedResultMap["set_variable"] = expectedParameter5
	expectedResultMap["map_variable"] = expectedParameter6
	expectedResultMap["object_variable"] = expectedParameter7
	expectedResultMap["tuple_variable"] = expectedParameter8

	// act
	actualResult, err := ParseParametersFromConfiguration(fileMap)

	// assert
	if err != nil {
		t.Errorf("Unexpected error returned. %v", err)
	}

	// assert the number of parameters parsed is as expected
	if len(actualResult) != len(expectedResultMap) {
		t.Errorf("The number of parameters contained in the result is %v, not %v as expected", len(actualResult), len(expectedResultMap))
	}

	// assert the content of parsed parameters is as expected
	for _, actualParameter := range actualResult {
		expectedParameter, ok := expectedResultMap[actualParameter.Key]

		if ok {
			if !reflect.DeepEqual(actualParameter, expectedParameter) {
				t.Errorf("Parsed parameter with key %v is not the same as expected", actualParameter.Key)
			}
			delete(expectedResultMap, actualParameter.Key)
		} else {
			t.Errorf("Parsed parameter with key %v is not expected", actualParameter.Key)
		}
	}

	// assert all parameters were parsed
	if len(expectedResultMap) != 0 {
		t.Errorf("Not all expected parameters were parsed")
	}
}

func TestParseParametersFromConfigurationWithNoFilesThrowsParserInvalidParameterException(t *testing.T) {
	// setup
	fileMap := make(map[string]string)
	expectedErrorMessage := "No .tf files found. Nothing to parse. Make sure the root directory of the Terraform open source configuration file contains the .tf files for the root module."

	// act
	_, err := ParseParametersFromConfiguration(fileMap)

	// assert
	if !reflect.DeepEqual(err, ParserInvalidParameterException{Message: expectedErrorMessage}) {
		t.Errorf("Validator did not throw ParserInvalidParameterException with expected error message")
	}
}
