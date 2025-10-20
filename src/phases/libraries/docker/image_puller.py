#!/usr/bin/env python3
"""
ImagePuller Unit

Pull Docker images with progress tracking
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import subprocess

logger = logging.getLogger(__name__)


@dataclass
class PullResult:
    """Result of image pull operation"""

    success: bool
    image: str
    already_exists: bool = False
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            if self.already_exists:
                return f"✅ Image already exists: {self.image}"
            return f"✅ Pulled image: {self.image}"
        return f"❌ Failed to pull {self.image}: {self.error}"


class ImagePuller:
    """
    Pull Docker images with proper error handling and progress
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ImagePuller.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def pull(self, image: str, quiet: bool = False) -> PullResult:
        """
        Pull a Docker image.

        Args:
            image: Image name (e.g., 'nginx:latest', 'python:3.11')
            quiet: Suppress progress output

        Returns:
            PullResult with pull status

        Example:
            puller = ImagePuller()
            result = puller.pull('nginx:latest')
            if result.success:
                print("Image ready!")
        """
        logger.info(f"Pulling image: {image}")

        try:
            # Build docker pull command
            cmd = ["docker", "pull"]
            if quiet:
                cmd.append("-q")
            cmd.append(image)

            # Execute pull
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for large images
                check=False,
            )

            if result.returncode == 0:
                # Check if already up to date
                already_exists = (
                    "up to date" in result.stdout.lower()
                    or "up-to-date" in result.stdout.lower()
                )

                if already_exists:
                    logger.info(f"✅ Image already up to date: {image}")
                else:
                    logger.info(f"✅ Successfully pulled: {image}")

                return PullResult(
                    success=True, image=image, already_exists=already_exists
                )
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"❌ Failed to pull {image}: {error_msg}")
                return PullResult(success=False, image=image, error=error_msg)

        except subprocess.TimeoutExpired:
            error_msg = "Pull timeout (600s exceeded)"
            logger.error(f"❌ {error_msg} for {image}")
            return PullResult(success=False, image=image, error=error_msg)
        except FileNotFoundError:
            error_msg = "docker command not found - is Docker installed?"
            logger.error(f"❌ {error_msg}")
            return PullResult(success=False, image=image, error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return PullResult(success=False, image=image, error=error_msg)

    def pull_multiple(
        self, images: List[str], quiet: bool = False
    ) -> Dict[str, PullResult]:
        """
        Pull multiple Docker images.

        Args:
            images: List of image names
            quiet: Suppress progress output

        Returns:
            Dict mapping image names to PullResults

        Example:
            puller = ImagePuller()
            results = puller.pull_multiple(['nginx:latest', 'python:3.11'])
            all_success = all(r.success for r in results.values())
        """
        logger.info(f"Pulling {len(images)} images")

        results = {}
        for image in images:
            results[image] = self.pull(image, quiet=quiet)

        successful = sum(1 for r in results.values() if r.success)
        logger.info(f"✅ Pull complete: {successful}/{len(images)} successful")

        return results

    def check_image_exists(self, image: str) -> bool:
        """
        Check if an image exists locally.

        Args:
            image: Image name

        Returns:
            True if image exists locally, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image],
                capture_output=True,
                timeout=10,
                check=False,
            )
            exists = result.returncode == 0

            if exists:
                logger.debug(f"✅ Image exists locally: {image}")
            else:
                logger.debug(f"Image not found locally: {image}")

            return exists

        except Exception as e:
            logger.warning(f"Failed to check image existence: {e}")
            return False


def main():
    """Test the unit."""
    import logging

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("Testing ImagePuller")
    print("=" * 50)

    puller = ImagePuller()

    # Test 1: Pull a small image
    print("\n1. Testing pull of alpine:latest (small image):")
    result = puller.pull("alpine:latest")
    print(f"   {result}")

    # Test 2: Check if image exists
    print("\n2. Testing image existence check:")
    exists = puller.check_image_exists("alpine:latest")
    print(f"   alpine:latest exists: {exists}")

    # Test 3: Pull same image again (should be up-to-date)
    print("\n3. Testing pull of already-existing image:")
    result = puller.pull("alpine:latest")
    print(f"   {result}")
    print(f"   Already exists: {result.already_exists}")

    # Test 4: Pull invalid image (should fail)
    print("\n4. Testing pull of invalid image:")
    result = puller.pull("nonexistent-image-12345:latest")
    print(f"   {result}")

    print("\n✅ ImagePuller tests complete")


if __name__ == "__main__":
    main()
