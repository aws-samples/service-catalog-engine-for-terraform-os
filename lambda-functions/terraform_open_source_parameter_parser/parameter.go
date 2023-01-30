package main

// Parameter represents a single parsed variable from a Provisioning Artifact
type Parameter struct {
	Key string `json:"key"`
	DefaultValue string `json:"defaultValue"`
	Type string `json:"type"`
	Description string `json:"description"`
	IsNoEcho bool `json:"isNoEcho"`
}
