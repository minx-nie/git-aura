"""
Git-Aura: Data Loader Module
Fetches GitHub user statistics via GraphQL API.
"""

import os
import requests
from typing import TypedDict, Optional
from datetime import datetime, timedelta


class LanguageData(TypedDict):
    """Represents a programming language with usage stats."""
    name: str
    color: str
    usage_count: int


class CommitTimeDistribution(TypedDict):
    """Distribution of commits across time periods."""
    morning: int   # 6:00 - 12:00
    afternoon: int # 12:00 - 18:00
    evening: int   # 18:00 - 24:00
    night: int     # 0:00 - 6:00


class GitHubStats(TypedDict):
    """Complete GitHub statistics for aura generation."""
    username: str
    user_id: int
    total_commits: int
    max_streak: int
    top_languages: list[LanguageData]
    commit_time_distribution: CommitTimeDistribution


class GitHubDataLoader:
    """Fetches and processes GitHub user data via GraphQL API."""
    
    GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
    
    def __init__(self, token: str):
        """
        Initialize the data loader.
        
        Args:
            token: GitHub Personal Access Token with read:user scope.
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def _execute_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """
        Execute a GraphQL query against GitHub API.
        
        Args:
            query: GraphQL query string.
            variables: Optional variables for the query.
            
        Returns:
            JSON response data.
            
        Raises:
            requests.RequestException: On API errors.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = requests.post(
            self.GRAPHQL_ENDPOINT,
            json=payload,
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        if "errors" in data:
            raise ValueError(f"GraphQL errors: {data['errors']}")
            
        return data["data"]
    
    def fetch_user_stats(self, username: str) -> GitHubStats:
        """
        Fetch comprehensive GitHub statistics for a user.
        
        Args:
            username: GitHub username to fetch stats for.
            
        Returns:
            GitHubStats containing all metrics for aura generation.
        """
        # Calculate date range for last 12 months
        now = datetime.utcnow()
        one_year_ago = now - timedelta(days=365)
        from_date = one_year_ago.strftime("%Y-%m-%dT00:00:00Z")
        to_date = now.strftime("%Y-%m-%dT23:59:59Z")
        
        query = """
        query($username: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $username) {
                id
                databaseId
                contributionsCollection(from: $from, to: $to) {
                    totalCommitContributions
                    contributionCalendar {
                        weeks {
                            contributionDays {
                                contributionCount
                                date
                            }
                        }
                    }
                }
                repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}) {
                    nodes {
                        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                            edges {
                                size
                                node {
                                    name
                                    color
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "username": username,
            "from": from_date,
            "to": to_date
        }
        
        data = self._execute_query(query, variables)
        user_data = data["user"]
        
        # Extract basic stats
        total_commits = user_data["contributionsCollection"]["totalCommitContributions"]
        user_id = user_data["databaseId"]
        
        # Calculate max streak from contribution calendar
        max_streak = self._calculate_max_streak(
            user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
        )
        
        # Aggregate language usage across repositories
        top_languages = self._aggregate_languages(user_data["repositories"]["nodes"])
        
        # Fetch commit time distribution (requires separate query for commit details)
        commit_time_distribution = self._fetch_commit_time_distribution(username, from_date, to_date)
        
        return GitHubStats(
            username=username,
            user_id=user_id,
            total_commits=total_commits,
            max_streak=max_streak,
            top_languages=top_languages[:3],  # Top 3 languages
            commit_time_distribution=commit_time_distribution
        )
    
    def _calculate_max_streak(self, weeks: list[dict]) -> int:
        """
        Calculate the maximum consecutive days with contributions.
        
        Args:
            weeks: List of week data from contribution calendar.
            
        Returns:
            Maximum streak length in days.
        """
        all_days = []
        for week in weeks:
            for day in week["contributionDays"]:
                all_days.append(day["contributionCount"] > 0)
        
        max_streak = 0
        current_streak = 0
        
        for has_contribution in all_days:
            if has_contribution:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
                
        return max_streak
    
    def _aggregate_languages(self, repositories: list[dict]) -> list[LanguageData]:
        """
        Aggregate language usage across all repositories.
        
        Args:
            repositories: List of repository data with language edges.
            
        Returns:
            Sorted list of languages by usage count.
        """
        language_totals: dict[str, dict] = {}
        
        for repo in repositories:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                color = edge["node"]["color"] or "#858585"  # Default gray if no color
                size = edge["size"]
                
                if name not in language_totals:
                    language_totals[name] = {"name": name, "color": color, "usage_count": 0}
                language_totals[name]["usage_count"] += size
        
        # Sort by usage count descending
        sorted_languages = sorted(
            language_totals.values(),
            key=lambda x: x["usage_count"],
            reverse=True
        )
        
        return [LanguageData(**lang) for lang in sorted_languages]
    
    def _fetch_commit_time_distribution(
        self, 
        username: str, 
        from_date: str, 
        to_date: str
    ) -> CommitTimeDistribution:
        """
        Fetch commit time distribution by analyzing recent commits.
        
        Note: This is an approximation based on available GraphQL data.
        For precise commit times, REST API would be needed per-repository.
        
        Args:
            username: GitHub username.
            from_date: Start date ISO string.
            to_date: End date ISO string.
            
        Returns:
            Distribution of commits across time periods.
        """
        # GraphQL doesn't directly expose commit timestamps
        # We'll use a heuristic based on contribution patterns
        # For a production system, you'd iterate through repos and commits
        
        query = """
        query($username: String!, $from: DateTime!, $to: DateTime!) {
            user(login: $username) {
                contributionsCollection(from: $from, to: $to) {
                    commitContributionsByRepository(maxRepositories: 10) {
                        repository {
                            name
                            defaultBranchRef {
                                target {
                                    ... on Commit {
                                        history(first: 50) {
                                            nodes {
                                                committedDate
                                                author {
                                                    user {
                                                        login
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "username": username,
            "from": from_date,
            "to": to_date
        }
        
        distribution = CommitTimeDistribution(
            morning=0,
            afternoon=0,
            evening=0,
            night=0
        )
        
        try:
            data = self._execute_query(query, variables)
            repos = data["user"]["contributionsCollection"]["commitContributionsByRepository"]
            
            for repo_data in repos:
                branch_ref = repo_data["repository"].get("defaultBranchRef")
                if not branch_ref or not branch_ref.get("target"):
                    continue
                    
                commits = branch_ref["target"].get("history", {}).get("nodes", [])
                
                for commit in commits:
                    # Filter commits by the target user
                    author = commit.get("author", {}).get("user")
                    if not author or author.get("login", "").lower() != username.lower():
                        continue
                        
                    committed_date = commit.get("committedDate", "")
                    if not committed_date:
                        continue
                        
                    # Parse hour from ISO timestamp
                    try:
                        dt = datetime.fromisoformat(committed_date.replace("Z", "+00:00"))
                        hour = dt.hour
                        
                        if 6 <= hour < 12:
                            distribution["morning"] += 1
                        elif 12 <= hour < 18:
                            distribution["afternoon"] += 1
                        elif 18 <= hour < 24:
                            distribution["evening"] += 1
                        else:
                            distribution["night"] += 1
                    except (ValueError, AttributeError):
                        continue
                        
        except Exception:
            # If we can't get commit times, use default even distribution
            distribution = CommitTimeDistribution(
                morning=25,
                afternoon=25,
                evening=25,
                night=25
            )
            
        # Ensure we have some data even if all zeros
        total = sum(distribution.values())
        if total == 0:
            distribution = CommitTimeDistribution(
                morning=25,
                afternoon=25,
                evening=25,
                night=25
            )
            
        return distribution


def load_github_stats(username: str, token: Optional[str] = None) -> GitHubStats:
    """
    Convenience function to load GitHub stats.
    
    Args:
        username: GitHub username to fetch stats for.
        token: Optional GitHub token. Falls back to GITHUB_TOKEN env var.
        
    Returns:
        GitHubStats for aura generation.
        
    Raises:
        ValueError: If no token is provided or found in environment.
    """
    if token is None:
        token = os.environ.get("GITHUB_TOKEN")
        
    if not token:
        raise ValueError(
            "GitHub token required. Set GITHUB_TOKEN environment variable "
            "or pass token parameter."
        )
    
    loader = GitHubDataLoader(token)
    return loader.fetch_user_stats(username)
