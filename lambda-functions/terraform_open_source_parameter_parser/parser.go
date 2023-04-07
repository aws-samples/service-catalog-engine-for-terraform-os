package main

import (
	"encoding/json"
	"log"
	"strconv"
	"strings"

	"github.com/hashicorp/hcl/v2/hclparse"
	"github.com/hashicorp/terraform-config-inspect/tfconfig"
)

const PrimaryModuleName = "PrimaryModule"
const OverrideModuleName = "OverrideModule"
const OverrideFileSuffix = "override.tf"
const NoFilesToParseExceptionMessage = "No .tf files found. Nothing to parse. Make sure the root directory of the Terraform open source configuration file contains the .tf files for the root module."

// ParseParametersFromConfiguration - Takes Terraform configuration represented as a map from file name to string contents
// parses out the variable blocks and returns slice of Parameter pointers
func ParseParametersFromConfiguration(fileMap map[string]string) ([]*Parameter, error) {
	if len(fileMap) == 0 {
		return nil, ParserInvalidParameterException{
			Message: NoFilesToParseExceptionMessage,
		}
	}

	primaryFileMap, overrideFileMap := bisectFileMap(fileMap)

	primaryParameterMap := parseParameterMapFromFileMap(primaryFileMap, PrimaryModuleName)
	overrideParameterMap := parseParameterMapFromFileMap(overrideFileMap, OverrideModuleName)
	parameters := mergeParameterMaps(primaryParameterMap, overrideParameterMap)

	return parameters, nil
}

// bisects the original file map into primaryFileMap and overrideFileMap
func bisectFileMap(fileMap map[string]string) (map[string]string, map[string]string) {
	primaryFileMap := make(map[string]string)
	overrideFileMap := make(map[string]string)

	if fileMap == nil || len(fileMap) == 0 {
		return primaryFileMap, overrideFileMap
	}

	for fileName, fileContents := range fileMap {
		if strings.HasSuffix(fileName, OverrideFileSuffix) {
			log.Printf("Identified override file: %s", fileName)
			overrideFileMap[fileName] = fileContents
		} else {
			log.Printf("Identified primary file: %s", fileName)
			primaryFileMap[fileName] = fileContents
		}
	}

	return primaryFileMap, overrideFileMap
}

// parses parameter map from provided file map and TF module
func parseParameterMapFromFileMap(fileMap map[string]string, moduleName string) map[string]*Parameter {
	parameterMap := make(map[string]*Parameter)

	parser := hclparse.NewParser()
	mod := tfconfig.NewModule(moduleName)

	if fileMap == nil || len(fileMap) == 0 {
		return parameterMap
	}

	for fileName, fileContents := range fileMap {
		log.Printf("Parsing file %s as HCL", fileName)
		file, _ := parser.ParseHCL([]byte(fileContents), fileName)
		if file == nil {
			log.Panicf("Failed to parse file %s as HCL", fileName)
			continue
		}
		tfconfig.LoadModuleFromFile(file, mod)
	}

	for _, variable := range mod.Variables {
		var defaultValue string

		if variable.Default == nil {
			defaultValue = ""
		} else {
			defaultValueJson, _ := json.Marshal(variable.Default)
			defaultValueJsonUnquoted, err := strconv.Unquote(string(defaultValueJson))
			// err indicates that there was no quotation mark in defaultValueJson
			// return defaultValueJson string in that case
			if err != nil {
				defaultValue = string(defaultValueJson)
			} else {
				defaultValue = defaultValueJsonUnquoted
			}
		}

		parameterMap[variable.Name] = &Parameter{
			Key: variable.Name,
			DefaultValue: defaultValue,
			Type: variable.Type,
			Description: variable.Description,
			IsNoEcho: variable.Sensitive,
		}
	}
	return parameterMap
}

// merges primary parameter map and override parameter map into a single list of parameters
func mergeParameterMaps(primaryParameterMap map[string]*Parameter, overrideParameterMap map[string]*Parameter) []*Parameter {
	var parameters []*Parameter

	if overrideParameterMap != nil && len(overrideParameterMap) != 0 {
		for key, overrideParameter := range overrideParameterMap {
			primaryParameter, ok := primaryParameterMap[key]
			if ok {
				mergedParameter := mergeParameters(primaryParameter, overrideParameter)
				parameters = append(parameters, mergedParameter)
			} else {
				parameters = append(parameters, overrideParameter)
			}
		}
	}

	if primaryParameterMap != nil && len(primaryParameterMap) != 0 {
		for key, primaryParameter := range primaryParameterMap {
			_, ok := overrideParameterMap[key]
			if !ok {
				parameters = append(parameters, primaryParameter)
			}
		}
	}

	return parameters
}

// merges the primary parameter with the override parameter into a single parameter
func mergeParameters(primaryParameter *Parameter, overrideParameter *Parameter) *Parameter {
	mergedParameter := &Parameter{}

	mergedParameter.Key = primaryParameter.Key

	if overrideParameter.DefaultValue == "" {
		mergedParameter.DefaultValue = primaryParameter.DefaultValue
	} else {
		mergedParameter.DefaultValue = overrideParameter.DefaultValue
	}

	if overrideParameter.Type == "" {
		mergedParameter.Type = primaryParameter.Type
	} else {
		mergedParameter.Type = overrideParameter.Type
	}

	if overrideParameter.Description == "" {
		mergedParameter.Description = primaryParameter.Description
	} else {
		mergedParameter.Description = overrideParameter.Description
	}

	mergedParameter.IsNoEcho = overrideParameter.IsNoEcho

	return mergedParameter
}
