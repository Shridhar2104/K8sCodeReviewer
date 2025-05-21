package git

import (
	"context"
)

// ReviewComment represents a comment to be posted to a Git provider
type ReviewComment struct {
	// File is the path to the file being commented on
	File string
	
	// Line is the line number to comment on
	Line int
	
	// Content is the text of the comment
	Content string
	
	// Severity is the severity level (critical, major, minor, suggestion)
	Severity string
	
	// Rule is the rule that triggered this comment
	Rule string
}

// Repository represents a Git repository
type Repository struct {
	// Owner is the owner/organization of the repository
	Owner string
	
	// Name is the name of the repository
	Name string
	
	// FullName is the full name (owner/name)
	FullName string
	
	// URL is the URL to the repository
	URL string
}

// PullRequest represents a Git pull request
type PullRequest struct {
	// Number is the PR number
	Number int
	
	// Title is the title of the PR
	Title string
	
	// BaseBranch is the target branch of the PR
	BaseBranch string
	
	// HeadBranch is the source branch of the PR
	HeadBranch string
	
	// URL is the URL to the PR
	URL string
}

// Client defines the interface for Git provider clients
type Client interface {
	// GetDiff gets the code diff for a pull request or commit
	GetDiff(ctx context.Context, owner, repo string, prNumber int, commitSHA string) (string, error)
	
	// PostReview posts review comments to a pull request
	PostReview(ctx context.Context, owner, repo string, prNumber int, comments []ReviewComment, summary string) (string, error)
	
	// GetRepositories gets the list of repositories for an organization or user
	GetRepositories(ctx context.Context, owner string) ([]Repository, error)
	
	// GetPullRequests gets the list of open pull requests for a repository
	GetPullRequests(ctx context.Context, owner, repo string) ([]PullRequest, error)
	
	// GetProviderName returns the name of the Git provider
	GetProviderName() string
}

// Factory creates Git clients based on provider type
type Factory struct {
	clients map[string]ClientConstructor
}

// ClientConstructor is a function that creates a Git client
type ClientConstructor func(tokenSource TokenSource) (Client, error)

// TokenSource provides authentication tokens for Git providers
type TokenSource interface {
	// Token returns the current token
	Token() (string, error)
}

// NewFactory creates a new Git client factory
func NewFactory() *Factory {
	return &Factory{
		clients: make(map[string]ClientConstructor),
	}
}

// Register registers a client constructor for a provider type
func (f *Factory) Register(providerType string, constructor ClientConstructor) {
	f.clients[providerType] = constructor
}

// Create creates a new Git client based on provider type
func (f *Factory) Create(providerType string, tokenSource TokenSource) (Client, error) {
	constructor, ok := f.clients[providerType]
	if !ok {
		return nil, ErrUnsupportedProvider
	}
	
	return constructor(tokenSource)
}

// StaticTokenSource is a simple token source that returns a static token
type StaticTokenSource struct {
	token string
}

// NewStaticTokenSource creates a new static token source
func NewStaticTokenSource(token string) *StaticTokenSource {
	return &StaticTokenSource{
		token: token,
	}
}

// Token implements TokenSource
func (s *StaticTokenSource) Token() (string, error) {
	return s.token, nil
}

// Error definitions
var (
	ErrUnsupportedProvider = NewError("unsupported git provider")
	ErrAuthenticationFailed = NewError("authentication failed")
	ErrResourceNotFound = NewError("resource not found")
	ErrPermissionDenied = NewError("permission denied")
	ErrInvalidRequest = NewError("invalid request")
)

// Error represents a git client error
type Error struct {
	Message string
}

// NewError creates a new git error
func NewError(message string) *Error {
	return &Error{
		Message: message,
	}
}

// Error implements the error interface
func (e *Error) Error() string {
	return e.Message
}