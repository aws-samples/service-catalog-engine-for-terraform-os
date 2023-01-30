package main

// Artifact represents the location of a Provisioning Artifact
type Artifact struct {
	Path string `json:"path"`
	Type string `json:"type"`
}
