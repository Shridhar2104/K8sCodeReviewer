package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

// ReviewComment represents a single code review comment
type ReviewComment struct {
	File     string `json:"file"`
	Line     int    `json:"line"`
	Content  string `json:"content"`
	Severity string `json:"severity"`
	Rule     string `json:"rule"`
}

// ReviewResult contains the results of a code review
type ReviewResult struct {
	Comments   []ReviewComment `json:"comments"`
	Summary    string          `json:"summary"`
	TokensUsed int             `json:"tokens_used"`
}

// ReviewOptions contains options for generating a code review
type ReviewOptions struct {
	MaxTokens    int      `json:"max_tokens,omitempty"`
	Temperature  float32  `json:"temperature,omitempty"`
	Language     string   `json:"language,omitempty"`
	SeverityLevels []string `json:"severity_levels,omitempty"`
	Rules        []string `json:"rules,omitempty"`
}

// ReviewRequest represents a request to the LLM service
type ReviewRequest struct {
	Diff    string        `json:"diff"`
	Options ReviewOptions `json:"options"`
}

// Client is the interface for interacting with the LLM service
type Client interface {
	ReviewCode(ctx context.Context, diff string, options ReviewOptions) (*ReviewResult, error)
}

// HTTPClient implements the Client interface using HTTP
type HTTPClient struct {
	endpoint   string
	apiKey     string
	httpClient *http.Client
}

// NewHTTPClient creates a new HTTP client for the LLM service
func NewHTTPClient(endpoint, apiKey string) *HTTPClient {
	return &HTTPClient{
		endpoint: endpoint,
		apiKey:   apiKey,
		httpClient: &http.Client{
			Timeout: 5 * time.Minute, // Code review might take a while
		},
	}
}

// ReviewCode sends a review request to the LLM service
func (c *HTTPClient) ReviewCode(ctx context.Context, diff string, options ReviewOptions) (*ReviewResult, error) {
	// Create the request body
	reqBody := ReviewRequest{
		Diff:    diff,
		Options: options,
	}

	// Marshal the request to JSON
	reqBytes, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("error marshaling request: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		c.endpoint,
		bytes.NewBuffer(reqBytes),
	)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.apiKey))
	}

	// Send the request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error sending request: %w", err)
	}
	defer resp.Body.Close()

	// Read the response body
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("error reading response: %w", err)
	}

	// Check for errors
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("error from LLM service: %s (status code: %d)", string(body), resp.StatusCode)
	}

	// Parse the response
	var result ReviewResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}

	return &result, nil
}