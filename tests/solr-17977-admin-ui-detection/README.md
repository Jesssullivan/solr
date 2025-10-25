# SOLR-17977 Demo Test Infrastructure

Test infrastructure for Admin UI security detection bug when behind reverse proxies.


From this test stack AFAICT, the new UI will need some minor updates as well (security nav menu is greyed out in these conditions), but that'll need to be a new PR as I am still exploring the new UI code.  It looks totally awesome though!

## The 17977 Bug

Admin UI shows "Security not enabled" when Solr runs behind a reverse proxy (Caddy, nginx) with BasicAuth passthrough, even though security **is** configured in ZooKeeper.

UI detection checks `/admin/info/system` for HTTP 401, but proxies pass auth headers → 200 OK → detection fails.

## The Fix

Add a fallback chain for wwww-authenticate header detection:
1. `/admin/info/system` endpoint (existing)
2. `/admin/authentication` endpoint
3. ZooKeeper `/security.json` check

## Test Stack

Three parallel Solr instances sharing one ZooKeeper:

```
ZooKeeper :2181
    ├─> Baseline  :8080  (apache/solr, legacy UI, shows bug)
    ├─> Patched   :8984  (Jesssullivan/solr, legacy UI + fix)
    └─> NewUI     :8985  (apache/solr, SOLR-17885 new UI- does not appear to work yet, though I am still exploring the new UI code)
```

## Sources

- **Baseline**: `apache/solr` main branch, legacy UI only (`-x :solr:ui:assemble`)
- **Patched**: `Jesssullivan/solr` main branch (PR #3807) with SOLR-17977 fix
- **NewUI**: `apache/solr` main branch with SOLR-17885 (PR #3704 by @malliaridis)

## Usage

```bash
# Start everything
podman-compose up -d

# Enable auth (run once after containers start)
podman exec solr-17977-baseline bin/solr auth enable \
  --type basicAuth --credentials admin:admin -z zookeeper:2181

# Test
open http://localhost:8080/solr/   # Baseline (shows bug)
open http://localhost:8984/solr/   # Patched (shows fix)
open http://localhost:8985/solr/ui/  # New UI (works)
```

Credentials: `admin` / `admin`

## Structure

```
.
├── baseline/
│   ├── Dockerfile          # Builds apache/solr (legacy UI only)
│   └── Caddyfile
├── patched/
│   ├── Dockerfile          # Builds Jesssullivan/solr (with fix)
│   └── Caddyfile
├── newui/
│   ├── Dockerfile          # Builds apache/solr (with new UI)
│   └── Caddyfile
├── scripts/zk-bootstrap.py
└── podman-compose.yml
```

## Cleanup

```bash
podman-compose down -v
podman system prune -af
```

## References

- **SOLR-17977** (this fix): https://issues.apache.org/jira/browse/SOLR-17977
  - PR #3807: https://github.com/apache/solr/pull/3807
  - Source: https://github.com/Jesssullivan/solr
- **SOLR-17885** (new UI): https://issues.apache.org/jira/browse/SOLR-17885
  - PR #3704: https://github.com/apache/solr/pull/3704
  - Author: @malliaridis
