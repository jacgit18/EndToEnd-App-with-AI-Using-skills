# Store Options — Where Non-Row Data Lives

Reference for the "When persistence isn't decided yet" section of `SKILL.md`. The paradigm
list there (relational / document / key-value / wide-column / graph / time-series / ledger /
search) answers "what kind of database". It does **not** answer "where do the large binary
blobs go" — files, media, documents, exports, backups. That is a separate store choice, and
getting it wrong (multi-MB blobs in database rows) is a common early mistake that is
expensive to undo.

Ported from `Architecture/02. Backing Service Options/File System Storage.md`.

---

## The three storage shapes

| Shape | Structure | Interface | Prevalent as |
|---|---|---|---|
| **Block storage** | Fixed-size blocks on a disk; a filesystem is laid over them | Mount a volume to one host, read/write like a local disk | The disk under a database, lift-and-shift VMs (EBS, Persistent Disk, Azure Disk) |
| **Object storage** | Opaque objects of any size in a flat namespace of buckets + keys, each with metadata | HTTP API (`PUT`/`GET` by key); no partial in-place writes, no rename | Cloud-native blob storage — S3, GCS, Azure Blob, R2 |
| **Distributed file system (DFS)** | A POSIX-ish filesystem tree spanning many nodes | Many hosts mount the same tree concurrently | Shared mounts and big-data pipelines — EFS / FSx, HDFS, GlusterFS, CephFS |

**DFS characteristics to expect** (and to verify a candidate actually delivers): local-disk-comparable throughput and latency; availability through partial node failure; horizontal scale to petabytes without client disruption; data-loss protection via replication; a simple read/write/copy interface; consistency and atomicity under concurrent access; heterogeneous data and client support.

---

## Blob in object storage vs row in the database

The default for any binary above a few hundred KB: **store the bytes in object storage, store a
row in the database that points at them** (bucket, key, size, content-type, checksum, owner,
timestamps). The database row is the system of record for *metadata and access control*; the
object store holds the *bytes*.

| Put it in a **database row** (BYTEA / BLOB) when… | Put it in **object storage** (+ pointer row) when… |
|---|---|
| The binary is small (≲ 256 KB) and always read with its row | It is large, or grows unbounded (uploads, media, generated files) |
| It must be written/updated in the *same transaction* as related rows, atomically | Eventual consistency between the row and the bytes is acceptable (write bytes, then commit row) |
| It is rarely read and never served directly to clients | Clients download it directly (serve via pre-signed URL / CDN, off the app's request path) |
| Point-in-time consistency with the rest of the row data is a hard requirement | You want lifecycle rules, storage tiers, versioning, and per-object cost that a DB won't give you |

Costs of getting this wrong by putting large blobs in rows: bloated tables and backups, cache
and buffer-pool pollution, replication lag, `SELECT *` transferring megabytes, and a migration
later to pull the bytes back out.

**Block storage** is the answer only when a single host needs a real filesystem — the database's
own storage volume, or an app that shells out to tools expecting local files. **DFS** when many
application nodes need to read/write the *same* files concurrently through a filesystem
interface (legacy apps built around a shared mount, data-processing frameworks). If clients just
need to `GET` a file by identifier, object storage is simpler and cheaper than either.

---

## Large-binary patterns

- **User uploads / media** — object storage; pointer row with `status` (`pending` → `stored` →
  `scanned`); upload via pre-signed `PUT` so bytes never transit the app; serve via pre-signed
  `GET` or CDN origin.
- **Generated documents / exports / reports** — object storage with a TTL lifecycle rule;
  pointer row carries the expiry so the app stops offering a dead link.
- **Backups and archives** — object storage with a cold/archive tier and a retention lock;
  never the primary transactional store.
- **Static assets** — object storage as CDN origin; not the database at all.
- **Document / EHR / evidence stores** (regulated) — object storage with versioning +
  object-lock (WORM) for the retention window; the pointer row holds the audit trail.

---

## Compliance note — regulated data on object storage (HIPAA / GDPR / PCI)

Object storage is an acceptable home for PHI, PII, and cardholder data **only with the
controls turned on** — the defaults are not enough:

- **Encryption** at rest (SSE with a managed KMS key, per-bucket) *and* in transit (TLS-only
  bucket policy).
- **Access control** — deny public access at the account level; grant via narrow IAM
  policies / pre-signed URLs with short expiry, never a broad bucket ACL.
- **Access logging / audit trail** — server access logs or CloudTrail data events, retained
  per the regime's audit window.
- **A signed agreement with the provider** — e.g. a BAA for HIPAA — before any PHI lands.
- **Data residency** — pin the bucket region to an allowed jurisdiction; check replication
  targets don't cross it.
- **Retention & legal hold** — object-lock / retention policies where the regime requires
  immutability.

Record which of these the design commits to in the ADR's Consequences section, the same way a
regulated class pushes DB-enforced constraints in `decision-framework.md` step 3.

---

## Concrete service names — AWS

Useful once the shape or paradigm above is decided and the conversation moves to naming an
actual product. Not itself a decision aid — picking a service by name before its shape or
paradigm is settled is the mistake `SKILL.md`'s gate exists to prevent.

**Storage shapes:**

| Shape | AWS service | Note |
|---|---|---|
| Block | EBS | Attaches to one EC2 instance; the disk under a self-managed database |
| Object | S3 | Storage classes (Standard / Standard-IA / One Zone-IA / Glacier tiers) trade retrieval speed for cost — Intelligent-Tiering automates the choice by access pattern; a lifecycle policy is how "move to a colder tier after N days" gets enforced, not application code |
| DFS | EFS | POSIX filesystem mounted concurrently from many EC2/Lambda/ECS/EKS clients over a VPC; FSx is the equivalent for Windows/Lustre workloads |
| Hybrid on-prem bridge | AWS Storage Gateway | Not a fourth shape — a way to back an on-prem file/volume/tape workflow with S3 without rearchitecting the on-prem side first |
| One-time bulk transfer | Snowball / Snowmobile | For an initial migration's data volume too large to move over a network link in the available time; not an ongoing storage tier |

**Database paradigms** (extends the paradigm list in `SKILL.md`'s "When persistence isn't
decided yet"):

| Paradigm | AWS service |
|---|---|
| Relational | Aurora, RDS |
| Key-value | DynamoDB |
| In-memory | ElastiCache (Redis / Memcached) — a cache in front of a store, see `caching-strategy`, not itself a system of record |
| Document | DocumentDB |
| Wide-column | Keyspaces |
| Graph | Neptune |
| Time-series | Timestream |
| Ledger (append-only, cryptographically verifiable history) | QLDB |

The IaaS-vs-managed axis is orthogonal to the paradigm choice: any of the relational engines
above can be self-run on an EC2 instance (full control, full operational burden) or consumed
as the managed service named (AWS owns patching/backups/failover; less control over
configuration). Reach for self-managed only when a specific requirement the managed tier
doesn't support forces it — the managed tier is the default, not the exception to justify.
