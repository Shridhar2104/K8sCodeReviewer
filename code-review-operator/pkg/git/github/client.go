package github

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"
	"time"

	"github.com/Shridhar2104/code-review-operator/pkg/git"
)

const (
	// DefaultAPIURL is the default GitHub API URL
	DefaultAPIURL = "https://api.github.com"
	
	// DefaultUserAgent is the default User-Agent for API requests
	DefaultUserAgent = "CodeReviewOperator/1.0"
)

// Client implements the git.Client interface for GitHub
type Client struct {
	client    *http.Client
	apiURL    string
	userAgent string
	token     git.TokenSource
}

// NewClient creates a new GitHub client
func NewClient(token git.TokenSource) (git.Client, error) {
	return &Client{
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		apiURL:    DefaultAPIURL,
		userAgent: DefaultUserAgent,
		token:     token,
	}, nil
}

// GetDiff gets the code diff for a pull request or commit
func (c *Client) GetDiff(ctx context.Context, owner, repo string, prNumber int, commitSHA string) (string, error) {
	var url string
	
	if prNumber > 0 {
		// Get diff for a pull request
		url = fmt.Sprintf("%s/repos/%s/%s/pulls/%d", c.apiURL, owner, repo, prNumber)
	} else if commitSHA != "" {
		// Get diff for a commit
		url = fmt.Sprintf("%s/repos/%s/%s/commits/%s", c.apiURL, owner, repo, commitSHA)
	} else {
		return "", fmt.Errorf("either prNumber or commitSHA must be provided")
	}
	
	// Create request
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return "", fmt.Errorf("error creating request: %w", err)
	}
	
	// Set headers for diff format
	req.Header.Set("Accept", "application/vnd.github.v3.diff")
	
	// Execute request
	diff, err := c.doRequest(req)
	if err != nil {
		return "", fmt.Errorf("error getting diff: %w", err)
	}
	
	return diff, nil
}

// PostReview posts review comments to a pull request
func (c *Client) PostReview(ctx context.Context, owner, repo string, prNumber int, comments []git.ReviewComment, summary string) (string, error) {
	// GitHub API requires a different format for review comments
	githubComments := make([]map[string]interface{}, 0, len(comments))
	
	for _, comment := range comments {
		githubComment := map[string]interface{}{
			"path": comment.File,
			"line": comment.Line,
			"body": formatCommentBody(comment),
		}
		githubComments = append(githubComments, githubComment)
	}
	
	// Create the review request body
	requestBody := map[string]interface{}{
		"commit_id": "", // Will be filled by API
		"body":      summary,
		"event":     "COMMENT", // Can be APPROVE, REQUEST_CHANGES, or COMMENT
		"comments":  githubComments,
	}
	
	// Marshal the request body
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("error marshaling review: %w", err)
	}
	
	// Create the request
	url := fmt.Sprintf("%s/repos/%s/%s/pulls/%d/reviews", c.apiURL, owner, repo, prNumber)
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("error creating request: %w", err)
	}
	
	// Execute the request
	response, err := c.doRequest(req)
	if err != nil {
		return "", fmt.Errorf("error posting review: %w", err)
	}
	
	// Parse the response to get the review URL
	var reviewResponse map[string]interface{}
	if err := json.Unmarshal([]byte(response), &reviewResponse); err != nil {
		return "", fmt.Errorf("error parsing response: %w", err)
	}
	
	// Return the HTML URL of the review
	if htmlURL, ok := reviewResponse["html_url"].(string); ok {
		return htmlURL, nil
	}
	
	// Return a generic URL if html_url is not found
	return fmt.Sprintf("https://github.com/%s/%s/pull/%d", owner, repo, prNumber), nil
}

// GetRepositories gets the list of repositories for an organization or user
func (c *Client) GetRepositories(ctx context.Context, owner string) ([]git.Repository, error) {
	// Determine if owner is an organization or user
	url := fmt.Sprintf("%s/users/%s/repos", c.apiURL, owner)
	
	// Create request
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}
	
	// Execute request
	response, err := c.doRequest(req)
	if err != nil {
		// Try as organization if user request fails
		url = fmt.Sprintf("%s/orgs/%s/repos", c.apiURL, owner)
		req, err = http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			return nil, fmt.Errorf("error creating request: %w", err)
		}
		
		response, err = c.doRequest(req)
		if err != nil {
			return nil, fmt.Errorf("error getting repositories: %w", err)
		}
	}
	
	// Parse the response
	var githubRepos []map[string]interface{}
	if err := json.Unmarshal([]byte(response), &githubRepos); err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}
	
	// Convert to our Repository type
	repos := make([]git.Repository, 0, len(githubRepos))
	for _, repo := range githubRepos {
		name, _ := repo["name"].(string)
		fullName, _ := repo["full_name"].(string)
		url, _ := repo["html_url"].(string)
		
		// Extract owner from full_name
		parts := strings.Split(fullName, "/")
		repoOwner := ""
		if len(parts) >= 2 {
			repoOwner = parts[0]
		}
		
		repos = append(repos, git.Repository{
			Owner:    repoOwner,
			Name:     name,
			FullName: fullName,
			URL:      url,
		})
	}
	
	return repos, nil
}

// GetPullRequests gets the list of open pull requests for a repository
func (c *Client) GetPullRequests(ctx context.Context, owner, repo string) ([]git.PullRequest, error) {
	url := fmt.Sprintf("%s/repos/%s/%s/pulls", c.apiURL, owner, repo)
	
	// Create request
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %w", err)
	}
	
	// Execute request
	response, err := c.doRequest(req)
	if err != nil {
		return nil, fmt.Errorf("error getting pull requests: %w", err)
	}
	
	// Parse the response
	var githubPRs []map[string]interface{}
	if err := json.Unmarshal([]byte(response), &githubPRs); err != nil {
		return nil, fmt.Errorf("error parsing response: %w", err)
	}
	
	// Convert to our PullRequest type
	prs := make([]git.PullRequest, 0, len(githubPRs))
	for _, pr := range githubPRs {
		number, _ := pr["number"].(float64)
		title, _ := pr["title"].(string)
		url, _ := pr["html_url"].(string)
		
		// Get base and head branches
		base, _ := pr["base"].(map[string]interface{})
		head, _ := pr["head"].(map[string]interface{})
		
		var baseBranch, headBranch string
		if base != nil {
			baseBranch, _ = base["ref"].(string)
		}
		if head != nil {
			headBranch, _ = head["ref"].(string)
		}
		
		prs = append(prs, git.PullRequest{
			Number:     int(number),
			Title:      title,
			BaseBranch: baseBranch,
			HeadBranch: headBranch,
			URL:        url,
		})
	}
	
	return prs, nil
}

// GetProviderName returns the name of the Git provider
func (c *Client) GetProviderName() string {
	return "github"
}

// doRequest executes an HTTP request with proper authentication
func (c *Client) doRequest(req *http.Request) (string, error) {
	// Set common headers
	req.Header.Set("User-Agent", c.userAgent)
	req.Header.Set("Accept", "application/json")
	
	// Set authentication token
	token, err := c.token.Token()
	if err != nil {
		return "", fmt.Errorf("error getting token: %w", err)
	}
	req.Header.Set("Authorization", fmt.Sprintf("token %s", token))
	
	// Execute request
	resp, err := c.client.Do(req)
	if err != nil {
		return "", fmt.Errorf("error executing request: %w", err)
	}
	defer resp.Body.Close()
	
	// Read response body
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading response: %w", err)
	}
	
	// Check for errors
	if resp.StatusCode >= 400 {
		switch resp.StatusCode {
		case http.StatusUnauthorized:
			return "", git.ErrAuthenticationFailed
		case http.StatusForbidden:
			return "", git.ErrPermissionDenied
		case http.StatusNotFound:
			return "", git.ErrResourceNotFound
		default:
			return "", fmt.Errorf("error from GitHub API: %s (status code: %d)", string(body), resp.StatusCode)
		}
	}
	
	return string(body), nil
}

// formatCommentBody formats a comment with severity and rule information
func formatCommentBody(comment git.ReviewComment) string {
	var prefix string
	
	switch comment.Severity {
	case "critical":
		prefix = "🚨 **CRITICAL**"
	case "major":
		prefix = "❌ **MAJOR**"
	case "minor":
		prefix = "⚠️ **MINOR**"
	case "suggestion":
		prefix = "💡 **SUGGESTION**"
	default:
		prefix = "**INFO**"
	}
	
	return fmt.Sprintf("%s (%s): %s", prefix, comment.Rule, comment.Content)
}