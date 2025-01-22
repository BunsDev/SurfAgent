from config.log import logger
from urllib.parse import urlparse
import os

class HostTracker:
    def __init__(self, filename="HOSTS.txt"):
        self.filename = filename
        self.failed_hosts = set()
        self.load_failed_hosts()
    
    def load_failed_hosts(self):
        """Load failed hosts from file."""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    self.failed_hosts = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self.failed_hosts)} problematic hosts from {self.filename}")
        except Exception as e:
            logger.error(f"Error loading failed hosts: {str(e)}")
            self.failed_hosts = set()
    
    def add_failed_host(self, url: str):
        """Add a failed host to the tracking list."""
        try:
            host = urlparse(url).netloc
            if host and host not in self.failed_hosts:
                self.failed_hosts.add(host)
                with open(self.filename, 'a') as f:
                    f.write(f"{host}\n")
                logger.info(f"Added {host} to problematic hosts list")
        except Exception as e:
            logger.error(f"Error adding failed host: {str(e)}")
    
    def is_problematic_host(self, url: str) -> bool:
        """Check if a URL's host is in the problematic list."""
        try:
            host = urlparse(url).netloc
            return host in self.failed_hosts
        except Exception:
            return False
        
host_tracker = HostTracker()