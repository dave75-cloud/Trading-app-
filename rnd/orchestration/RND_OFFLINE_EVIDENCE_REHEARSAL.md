# RND-0023 Offline Evidence-Chain Rehearsal

Status: R&D CANDIDATE / NON-OPERATIONAL
Automatic merge: NONE
Automatic promotion: NONE
Human merge decision: REQUIRED

## Purpose

Rehearse the existing RND-0020 → RND-0021 → RND-0022 handoff for a harmless
`rnd/` candidate. The tool builds a work packet from an explicit task spec,
consumes an already-produced RND-0021 execution-evidence bundle and externally
attested validation records, assembles candidate evidence with RND-0022, then
evaluates it with RND-0020. It emits four deterministic JSON artifacts:

1. hashed work packet;
2. RND-0020-compatible candidate evidence;
3. RND-0022 assembly provenance;
4. RND-0020 review dossier.

The CLI refuses existing or duplicate output paths. It returns the evaluator's
exit status: PASS = 0, REVIEW_REQUIRED = 2, FAIL_CLOSED = 1. A malformed or
cross-revision input fails before output creation.

## Input boundary

All inputs are explicit local JSON paths. RND-0023 does not run the executor,
unit tests, workspace audit, candidate code or a shell. A human-controlled
external process must produce the RND-0021 bundle and external validation
attestations. The assembler verifies their identity and content hashes, but
cannot establish that an external validation actually ran. Output-hash records
are supplied claims, not independently checked against repository files.

Example, after producing the source artifacts separately:

```sh
python3 rnd/orchestration/offline_evidence_rehearsal.py \
  --task-spec /tmp/task-spec.json \
  --execution-evidence /tmp/execution-evidence.json \
  --external-validation /tmp/unit-tests.json \
  --external-validation /tmp/workspace-audit.json \
  --path-manifest /tmp/changed-paths.json \
  --output-manifest /tmp/output-hashes.json \
  --work-packet-output /tmp/work-packet.json \
  --candidate-output /tmp/candidate-evidence.json \
  --provenance-output /tmp/assembly-provenance.json \
  --dossier-output /tmp/review-dossier.json
```

The work packet used by the externally produced source artifacts must be the
same deterministic packet built from this task spec. A changed task spec or
candidate HEAD fails the handoff.

## Rehearsal cases

Focused tests call the real RND-0020 planner and evaluator, the RND-0021 plan
and evidence functions with an injected synthetic Git runner, and the real
RND-0022 assembler. They exercise PASS, missing external evidence
(REVIEW_REQUIRED), failed evidence (FAIL_CLOSED), rehashed cross-HEAD evidence,
scope/path disagreement and duplicate labels. The synthetic runner never
invokes Git and does not claim to be an independently run test or audit.

The branch also contains `rnd/rehearsal/fixture.txt`. A local smoke rehearsal
can use the real RND-0021 read-only Git actions against a committed branch
revision, with externally produced test/audit logs and exact output file hashes.
Those ephemeral evidence artifacts stay outside the repository.

## Authority

RND-0023 does not add subprocess, network, GitHub API, candidate-code, Git
mutation, broker, disposition, merge, promotion, trading execution or capital
authority. Human disposition remains unset in the dossier. Frozen M006e,
canonical M005 and the operational forward-observation stack are untouched.
