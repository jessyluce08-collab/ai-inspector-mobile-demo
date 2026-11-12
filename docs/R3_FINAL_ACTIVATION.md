# Conditional activation — no further general preparation ticket

Current status: no investigator information, actual authorization, registration or deployment approval is supplied. All current artifacts remain technical and NOT_AUTHORIZED. The local consent harness is never a study release and cannot be deployed.

## 1. Investigator completion

Complete R3_INVESTIGATOR_FINAL_DECISIONS.md and the private INVESTIGATOR_CONFIG.template.json truthfully. Approve the actual operational limits and review disposition. Record the externally published final protocol reference/time, actual protocol SHA256 and prospective owner approval. Placeholders or synthetic authorization are refused. This records an investigator declaration; software cannot certify its legal truth.

## 2. One conditional preparation command

From the repository, using the existing engineering Python/Playwright/Chromium environment:

```
python research/r3_pilot/tools/final_release.py prepare --config /private/INVESTIGATOR_CONFIG.completed.json --base-url https://jessyluce08-collab.github.io/ai-inspector-mobile-demo/ --output /private/r3-release-package
```

Missing decisions produce `PENDING_INVESTIGATOR_DECISIONS`, exit3 and **no research HTML**. With genuine complete decisions, the command builds an immutable `r3-pilot-<build12>-<configuration8>/index.html`, verifies all frozen scientific inputs, performs a full24trial exact-candidate technical browser/export check, and records the actual candidate/config/protocol/schema/analysis hashes and lock. An unavailable browser or failed check prevents finalization; preserve the error rather than manufacture PASS. No publication, recruitment or automatic response upload occurs. Reserved `PILOT-TECH…` codes are only engineering tests and are excluded from human admission. Automated checkbox metadata are not proof of a person's consent; raw scripted test exports are ephemeral.

The actual authorized-candidate branch cannot be executed before real approval. This is a human-dependent activation step, not a third optimization mission. It can be completed by the investigator's authorized operator or in continuation of this mission when actual decisions are supplied.

## 3. Exact deployment approval, publication and served-byte check

Review the exact HTML and generated DEPLOYMENT_APPROVAL.template.json. The generated approval is false. The real investigator must approve its actual hash and direct HTTPS URL, with responsible identity/time. Externally timestamp the final protocol/lock before first enrollment. Publish only the new immutable directory after that approval; do not change root index.html, old release directories or Pages settings unnecessarily.

On Android GitHub: create `<new-directory>/.keep` with a short text through Add file/Create new file; enter that folder, upload the exact supplied index.html and commit. No HTML editing or repository recreation. Wait for the actual Pages deployment. Never publish private configuration/registers. The directory name and exact URL come from PREPARED_RELEASE.json, not a guessed release name.

```
python research/r3_pilot/tools/final_release.py verify-served --receipt /private/r3-release-package/PREPARED_RELEASE.json --approval /private/DEPLOYMENT_APPROVAL.completed.json --output /private/r3-release-package/SERVED_VERIFICATION.json
```

This is a static GET/hash check, not device or human validation. A proxy/network error is environmental, not evidence that the site rejected a participant. Do not assert public deployment success without the exact bytes matching.

## 4. Proportionate device smoke and launch

Existing complete Samsung/iOS field reports are accepted as operational smoke evidence of unchanged rendering. Do not repeat an instrumented geometry campaign. On actual Android Chrome and iPhone Safari, open the new direct link, confirm completed information precedes consent; confirm refusal blocks start; use a reserved technical PILOT-TECH code, exercise start and export a short partial session (choose U, without making research judgments). Recover the JSON and validate its schema/identity; keep it outside the pilot register. The automated full24trial test covers navigation; the device smoke specifically checks the changed consent/export controls and actual save/share. Record real evidence or NOT_RUN, never emulation as a physical phone.

Only the actual investigator may launch after the required decisions, final identity, exact deployment approval and served-byte check, with no critical issue. Positive admission of a genuinely consenting enrolled observer is not fabricated beforehand. Pilot registers and observations stay private; old engineering files never become pilot data.
