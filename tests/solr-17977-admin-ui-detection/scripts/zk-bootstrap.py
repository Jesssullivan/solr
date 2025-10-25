#!/usr/bin/env python3
"""
Bootstrap security.json to ZooKeeper for SOLR-17977 test infrastructure.
Based on production solr-9 bootstrap approach using direct ZK access.
"""

import json
import sys
import time
from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError

ZK_HOST = "localhost:2181"
SECURITY_JSON_PATH = "/security.json"

# Security configuration with BasicAuth
SECURITY_CONFIG = {
    "authentication": {
        "class": "solr.BasicAuthPlugin",
        "credentials": {
            # admin/admin - SHA-256 double-hash
            "admin": "IV0EHq1OnNrj6gvRCwvFwTrZ1+z1oBbnQdiVC3otuq0= Ndd7LKvVBAaZIF0QAVi1ekCfAJXr1GGfLtRUXhgrF8c="
        },
        "blockUnknown": True,
        "realm": "Solr SOLR-17977 Test",
        "forwardCredentials": True
    },
    "authorization": {
        "class": "solr.RuleBasedAuthorizationPlugin",
        "permissions": [
            # Public endpoints (no auth required for health checks)
            {"name": "health-check", "path": "/admin/ping", "role": None},
            {"name": "health-info", "path": "/admin/info/health", "role": None},
            {"name": "system-info", "path": "/admin/info/system", "role": None},
            # Admin role for everything else
            {"name": "all", "role": ["admin"]}
        ],
        "user-role": {
            "admin": ["admin"]
        }
    }
}


def wait_for_zookeeper(max_attempts=30):
    """Wait for ZooKeeper to be ready."""
    print(f"Waiting for ZooKeeper at {ZK_HOST}...")

    for attempt in range(1, max_attempts + 1):
        try:
            zk = KazooClient(hosts=ZK_HOST, timeout=5.0)
            zk.start(timeout=5)
            print(f"✅ ZooKeeper is ready!")
            zk.stop()
            return True
        except Exception as e:
            if attempt < max_attempts:
                print(f"  Attempt {attempt}/{max_attempts}: {e}")
                time.sleep(2)
            else:
                print(f"❌ ZooKeeper not ready after {max_attempts} attempts")
                return False

    return False


def upload_security_json():
    """Upload security.json directly to ZooKeeper."""
    print(f"\nUploading security.json to ZooKeeper...")

    zk = KazooClient(hosts=ZK_HOST, timeout=10.0)

    try:
        zk.start(timeout=10)

        security_data = json.dumps(SECURITY_CONFIG, indent=2).encode('utf-8')

        # Check if security.json already exists
        if zk.exists(SECURITY_JSON_PATH):
            print(f"  Security.json already exists, updating...")
            zk.set(SECURITY_JSON_PATH, security_data)
            print(f"✅ Security.json updated successfully")
        else:
            print(f"  Creating new security.json...")
            zk.create(SECURITY_JSON_PATH, security_data, makepath=True)
            print(f"✅ Security.json created successfully")

        # Verify the upload
        stored_data, stat = zk.get(SECURITY_JSON_PATH)
        stored_config = json.loads(stored_data.decode('utf-8'))

        if stored_config.get('authentication'):
            print(f"✅ Verification passed - authentication configured")
            print(f"   Realm: {stored_config['authentication'].get('realm')}")
            print(f"   Credentials: {len(stored_config['authentication'].get('credentials', {}))} user(s)")
            return True
        else:
            print(f"❌ Verification failed - security.json missing authentication")
            return False

    except Exception as e:
        print(f"❌ Failed to upload security.json: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        zk.stop()


def main():
    """Main bootstrap workflow."""
    print("=" * 60)
    print("SOLR-17977 ZooKeeper Security Bootstrap")
    print("=" * 60)

    # Step 1: Wait for ZooKeeper
    if not wait_for_zookeeper():
        print("\n❌ Bootstrap failed: ZooKeeper not available")
        sys.exit(1)

    # Step 2: Upload security.json
    if not upload_security_json():
        print("\n❌ Bootstrap failed: Could not upload security.json")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Bootstrap Complete!")
    print("=" * 60)
    print("\nTest URLs:")
    print("  Baseline (Bug):  http://localhost:8080/solr/")
    print("  Patched (Fix):   http://localhost:8984/solr/")
    print("  New UI (Works):  http://localhost:8985/solr/ui/")
    print("\nCredentials: admin / admin")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
