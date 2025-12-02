"""
Git-Aura: Main Entry Point
Orchestrates data fetching, normalization, and aura generation.
"""

import os
import sys
import argparse
import hashlib
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from src.data_loader import load_github_stats, GitHubStats
from src.generative_engine import AuraGenerator
from src.renderer import render_aura


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StatsNormalizer:
    """
    Normalizes GitHub statistics to values suitable for aura generation.
    Uses sigmoid and logarithmic scaling to handle outliers.
    """
    
    # Reference values for normalization (based on typical GitHub activity)
    REF_COMMITS = 500       # Median-ish yearly commits for active devs
    REF_STREAK = 30         # 30-day streak is notable
    MAX_COMMITS = 5000      # Cap for extremely active users
    MAX_STREAK = 365        # Maximum streak is a year
    
    @staticmethod
    def sigmoid(x: float, midpoint: float = 0.5, steepness: float = 10.0) -> float:
        """
        Sigmoid function for smooth normalization.
        
        Args:
            x: Input value (0-1 range expected).
            midpoint: X value where output is 0.5.
            steepness: How sharp the transition is.
            
        Returns:
            Normalized value between 0 and 1.
        """
        return 1 / (1 + np.exp(-steepness * (x - midpoint)))
    
    @staticmethod
    def log_scale(value: float, reference: float, max_val: float) -> float:
        """
        Logarithmic scaling for handling wide value ranges.
        
        Args:
            value: Raw value to normalize.
            reference: Reference value for scaling.
            max_val: Maximum expected value.
            
        Returns:
            Normalized value between 0 and 1.
        """
        if value <= 0:
            return 0.0
        
        # Log scale with reference point
        log_val = np.log1p(value) / np.log1p(max_val)
        return min(1.0, log_val)
    
    def normalize_density(self, total_commits: int) -> float:
        """
        Normalize commit count to density value.
        Uses logarithmic scaling: ρ = log(total_commits)
        
        Args:
            total_commits: Total commits in last 12 months.
            
        Returns:
            Density value between 0 and 1.
        """
        return self.log_scale(total_commits, self.REF_COMMITS, self.MAX_COMMITS)
    
    def normalize_intensity(self, max_streak: int) -> float:
        """
        Normalize streak to intensity/glow value.
        
        Args:
            max_streak: Maximum consecutive days with commits.
            
        Returns:
            Intensity value between 0 and 1.
        """
        raw = max_streak / self.MAX_STREAK
        # Apply sigmoid for smoother distribution
        return self.sigmoid(raw, midpoint=0.15, steepness=8.0)
    
    def calculate_chaos_factor(self, time_distribution: dict) -> float:
        """
        Calculate chaos factor from commit time distribution.
        High variance in commit times = high chaos.
        
        Args:
            time_distribution: Dict with morning/afternoon/evening/night counts.
            
        Returns:
            Chaos factor between 0 and 1.
        """
        counts = [
            time_distribution.get("morning", 0),
            time_distribution.get("afternoon", 0),
            time_distribution.get("evening", 0),
            time_distribution.get("night", 0)
        ]
        
        total = sum(counts)
        if total == 0:
            return 0.5  # Default to medium chaos
        
        # Normalize to proportions
        proportions = [c / total for c in counts]
        
        # Calculate entropy (measure of randomness)
        # High entropy = uniform distribution = high chaos
        entropy = 0.0
        for p in proportions:
            if p > 0:
                entropy -= p * np.log2(p)
        
        # Max entropy for 4 categories is log2(4) = 2
        max_entropy = 2.0
        normalized_entropy = entropy / max_entropy
        
        # Map to chaos: uniform distribution (high entropy) = high chaos
        # Concentrated distribution (low entropy) = low chaos (smooth curves)
        return normalized_entropy
    
    def normalize_stats(self, stats: GitHubStats) -> dict:
        """
        Normalize all stats for aura generation.
        
        Args:
            stats: Raw GitHub statistics.
            
        Returns:
            Dict with normalized values.
        """
        return {
            "density": self.normalize_density(stats["total_commits"]),
            "intensity": self.normalize_intensity(stats["max_streak"]),
            "chaos_factor": self.calculate_chaos_factor(stats["commit_time_distribution"]),
            "seed": stats["user_id"],
            "languages": stats["top_languages"]
        }


def generate_aura(
    username: str,
    token: Optional[str] = None,
    output_path: str = "aura.svg",
    width: int = 800,
    height: int = 800,
    animate: bool = True
) -> str:
    """
    Generate an aura SVG for a GitHub user.
    
    Args:
        username: GitHub username.
        token: GitHub token (falls back to GITHUB_TOKEN env var).
        output_path: Output SVG path.
        width: SVG width.
        height: SVG height.
        animate: Whether to add animation.
        
    Returns:
        Path to generated SVG.
    """
    logger.info(f"Generating aura for user: {username}")
    
    # Step 1: Fetch GitHub stats
    logger.info("Fetching GitHub statistics...")
    try:
        stats = load_github_stats(username, token)
        logger.info(f"Fetched stats: {stats['total_commits']} commits, "
                   f"{stats['max_streak']} day streak, "
                   f"{len(stats['top_languages'])} languages")
    except Exception as e:
        logger.error(f"Failed to fetch GitHub stats: {e}")
        raise
    
    # Step 2: Normalize stats
    logger.info("Normalizing statistics...")
    normalizer = StatsNormalizer()
    normalized = normalizer.normalize_stats(stats)
    
    logger.info(f"Normalized values - Density: {normalized['density']:.3f}, "
               f"Intensity: {normalized['intensity']:.3f}, "
               f"Chaos: {normalized['chaos_factor']:.3f}")
    
    # Step 3: Generate particle paths
    logger.info("Generating particle flow field...")
    generator = AuraGenerator(
        width=width,
        height=height,
        seed=normalized["seed"]
    )
    
    paths = generator.generate(
        density=normalized["density"],
        chaos_factor=normalized["chaos_factor"],
        simulation_steps=150
    )
    logger.info(f"Generated {len(paths)} particle paths")
    
    # Step 4: Render SVG
    logger.info("Rendering SVG...")
    output_file = render_aura(
        paths_with_opacity=paths,
        languages=normalized["languages"],
        glow_intensity=normalized["intensity"],
        output_path=output_path,
        width=width,
        height=height,
        animate=animate
    )
    
    logger.info(f"Aura saved to: {output_file}")
    return output_file


def get_file_hash(filepath: str) -> Optional[str]:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        filepath: Path to file.
        
    Returns:
        Hex digest of file hash, or None if file doesn't exist.
    """
    if not os.path.exists(filepath):
        return None
    
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Git-Aura: Generate artistic GitHub activity visualizations"
    )
    parser.add_argument(
        "username",
        nargs="?",
        help="GitHub username (defaults to GITHUB_ACTOR env var)"
    )
    parser.add_argument(
        "-o", "--output",
        default="aura.svg",
        help="Output SVG path (default: aura.svg)"
    )
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=800,
        help="SVG width in pixels (default: 800)"
    )
    parser.add_argument(
        "-H", "--height",
        type=int,
        default=800,
        help="SVG height in pixels (default: 800)"
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable SVG animation"
    )
    parser.add_argument(
        "--check-changes",
        action="store_true",
        help="Only output if file content changed (for CI)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get username from args or environment
    username = args.username or os.environ.get("GITHUB_ACTOR")
    if not username:
        logger.error("Username required. Provide as argument or set GITHUB_ACTOR env var.")
        sys.exit(1)
    
    # Get token from environment
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN environment variable required.")
        sys.exit(1)
    
    # Get hash of existing file for change detection
    old_hash = None
    if args.check_changes:
        old_hash = get_file_hash(args.output)
    
    try:
        # Generate aura
        output_file = generate_aura(
            username=username,
            token=token,
            output_path=args.output,
            width=args.width,
            height=args.height,
            animate=not args.no_animation
        )
        
        # Check if file changed
        if args.check_changes:
            new_hash = get_file_hash(output_file)
            if old_hash == new_hash:
                logger.info("No changes detected in generated aura.")
                # Signal no changes via exit code
                print("AURA_CHANGED=false")
            else:
                logger.info("Aura content changed.")
                print("AURA_CHANGED=true")
        
        logger.info("Aura generation complete!")
        
    except Exception as e:
        logger.error(f"Aura generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
