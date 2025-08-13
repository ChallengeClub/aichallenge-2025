#!/usr/bin/env python3
"""
Command-line script to download the latest submission file from vehicle ECU
Usage: python3 scripts/download_latest_submission.py --username=user@example.com --password=mypassword --output=./
"""

import os
import sys
import json
import argparse
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SubmissionDownloader:
    def __init__(self):
        """Initialize the downloader with configuration"""
        self.api_base_url = os.getenv('API_BASE_URL', 'https://aichallenge-board.jsae.or.jp')

        # Initialize requests session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def authenticate(self, username, password):
        """
        Authenticate with AWS Cognito using client-side authentication
        This approach doesn't require AWS credentials

        Args:
            username (str): Cognito username/email
            password (str): Cognito password

        Returns:
            str: Access token if successful, None otherwise
        """
        try:
            logger.info("Authenticating with AWS Cognito...")

            auth_url = f"{self.api_base_url}/api/user/login"

            auth_data = {
                'username': username,
                'password': password
            }

            response = self.session.post(auth_url, json=auth_data, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'AccessToken' in data:
                    logger.info("Authentication successful!")
                    return data['AccessToken']
                else:
                    logger.error("No access token in response")
                    return None
            else:
                logger.error(f"Authentication failed: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during authentication: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def download_latest_submission(self, access_token, output_dir='./'):
        """
        Download the latest submission file using the access token

        Args:
            access_token (str): Valid access token from Cognito
            output_dir (str): Directory to save the downloaded file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Requesting latest submission file...")

            # Set authorization header
            headers = {'Authorization': f'Bearer {access_token}'}

            # Make API request
            url = f"{self.api_base_url}/api/submission/download/latest"
            response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"API Error: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error("Invalid JSON response from API")
                return False

            if not data or 'download_url' not in data:
                logger.error("Invalid response from API")
                return False

            logger.info(f"Found submission file: {data['filename']}")
            logger.info(f"File size: {data['file_size']:,} bytes")

            if data.get('comment'):
                logger.info(f"Comment: {data['comment']}")

            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Download the file using the pre-signed URL
            download_url = data['download_url']
            output_path = os.path.join(output_dir, data['filename'])

            logger.info(f"Downloading file to: {output_path}")

            # Download file with progress tracking
            download_response = requests.get(download_url, stream=True, timeout=300)

            if download_response.status_code != 200:
                logger.error(f"Failed to download file. HTTP Code: {download_response.status_code}")
                return False

            # Write file with progress tracking
            total_size = int(download_response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(output_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Show progress for large files
                        if total_size > 0 and downloaded_size % (1024 * 1024) == 0:  # Every MB
                            progress = (downloaded_size / total_size) * 100
                            logger.info(f"Download progress: {progress:.1f}% ({downloaded_size:,}/{total_size:,} bytes)")

            # Verify file size
            actual_size = os.path.getsize(output_path)
            expected_size = data['file_size']

            if actual_size != expected_size:
                logger.warning(f"Downloaded file size ({actual_size:,}) doesn't match expected size ({expected_size:,})")

            logger.info("Download completed successfully!")
            logger.info(f"File saved to: {output_path}")
            logger.info(f"Downloaded size: {actual_size:,} bytes")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False

    def download_specific_submission(self, access_token, submission_id, output_dir='./'):
        """
        Download a specific submission file by ID

        Args:
            access_token (str): Valid access token from Cognito
            submission_id (str): Submission ID to download
            output_dir (str): Directory to save the downloaded file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Requesting specific submission: {submission_id}")

            headers = {'Authorization': f'Bearer {access_token}'}
            url = f"{self.api_base_url}/api/submission/download/{submission_id}"

            response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"API Error: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

            data = response.json()
            if not data or 'download_url' not in data:
                logger.error("Invalid response from API")
                return False

            logger.info(f"Found submission file: {data['filename']}")
            logger.info(f"File size: {data['file_size']:,} bytes")

            if data.get('comment'):
                logger.info(f"Comment: {data['comment']}")

            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Download the file
            download_url = data['download_url']
            output_path = os.path.join(output_dir, data['filename'])

            logger.info(f"Downloading file to: {output_path}")

            download_response = requests.get(download_url, stream=True, timeout=300)

            if download_response.status_code != 200:
                logger.error(f"Failed to download file. HTTP Code: {download_response.status_code}")
                return False

            with open(output_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            actual_size = os.path.getsize(output_path)
            logger.info("Download completed successfully!")
            logger.info(f"File saved to: {output_path}")
            logger.info(f"Downloaded size: {actual_size:,} bytes")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False

def show_usage():
    """Display usage information"""
    print("Usage: python3 scripts/download_latest_submission.py [options]")
    print()
    print("Options:")
    print("  --username=USERNAME    AWS Cognito username (email)")
    print("  --password=PASSWORD    AWS Cognito password")
    print("  --output=DIR           Output directory (default: ./)")
    print("  --submission-id=ID     Download specific submission by ID")
    print("  --help                 Show this help message")
    print()
    print("Examples:")
    print("  # Download latest submission")
    print("  python3 scripts/download_latest_submission.py --username=user@example.com --password=mypassword --output=./my-downloads/")
    print()
    print("  # Download specific submission")
    print("  python3 scripts/download_latest_submission.py --username=user@example.com --password=mypassword --submission-id=abc123")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Download latest submission file')
    parser.add_argument('--username', required=True, help='AWS Cognito username (email)')
    parser.add_argument('--password', required=True, help='AWS Cognito password')
    parser.add_argument('--output', default='./', help='Output directory (default: ./)')
    parser.add_argument('--submission-id', help='Download specific submission by ID')

    args = parser.parse_args()

    try:
        # Initialize downloader
        downloader = SubmissionDownloader()

        # Authenticate with Cognito
        access_token = downloader.authenticate(args.username, args.password)

        if not access_token:
            logger.error("Authentication failed. Exiting.")
            return 1

        # Download file
        if args.submission_id:
            success = downloader.download_specific_submission(access_token, args.submission_id, args.output)
        else:
            success = downloader.download_latest_submission(access_token, args.output)

        if not success:
            logger.error("Download failed. Exiting.")
            return 1

        logger.info("Script completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
