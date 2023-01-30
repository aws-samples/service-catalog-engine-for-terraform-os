package main

import (
	"os"
	"reflect"
	"testing"
)

func TestUnzipArchiveHappy(t *testing.T) {
	// setup
	const MockArtifactPath = "./test-artifacts/mock-artifact-with-subdirectories.tar.gz"
	expectedFileMap := make(map[string]string)
	expectedFileMap["main.tf"] = "main-contents"

	zipFile, err := os.ReadFile(MockArtifactPath)
	if err != nil {
		t.Errorf("Error opening test artifact %s", MockArtifactPath)
	}

	// act
	fileMap, err := UnzipArchive(zipFile)

	// assert
	if !reflect.DeepEqual(fileMap, expectedFileMap) {
		t.Errorf("fileMap %s is not as expected: %s", fileMap, expectedFileMap)
	}
}

func TestUnzipArchiveHappyWithDotSlashRootModuleFiles(t *testing.T) {
	// setup
	const MockArtifactPath = "./test-artifacts/mock-artifact-with-dot-slash-root-module-prefix-files.tar.gz"
	expectedFileMap := make(map[string]string)
	expectedFileMap["./main.tf"] = "main-contents"

	zipFile, err := os.ReadFile(MockArtifactPath)
	if err != nil {
		t.Errorf("Error opening test artifact %s", MockArtifactPath)
	}

	// act
	fileMap, err := UnzipArchive(zipFile)

	// assert
	if !reflect.DeepEqual(fileMap, expectedFileMap) {
		t.Errorf("fileMap %s is not as expected: %s", fileMap, expectedFileMap)
	}
}
