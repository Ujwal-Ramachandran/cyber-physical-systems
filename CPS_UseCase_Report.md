# SE6012 CA1: CPS Use Case Report (Course-Aligned)

**Assignment:** Positive CPS use case, 3 security/privacy issues under the CIA triad, deep-dive one issue with mitigations.
**Weightage:** 30% of module. **Presentation:** 09/09/2026. **Time:** 15 min talk + 5 min Q&A.
**Grading:** Comprehensiveness 35%, Issue Analysis (CIA) 35%, Mitigation 20%, Uniqueness 10%, plus +5% for a live demo/simulation.

Priorities for this report, as you asked: **novelty** and a **buildable demo** are weighted highest, then alignment to how this specific course grades.

---

## The single most important insight

**Match the deep-dive to the professor's expertise.** Dr. Shivam Bhasin (Temasek Labs @ NTU) and TA Dirmanto Jap are side-channel and hardware-security researchers. Lecture 2 and the whole syllabus revolve around:

- Side-channel analysis (weeks 2-6, plus a hands-on SCA lab)
- Fault-injection analysis (weeks 8-10, plus a Fault-Analysis lab)
- Hardware trojans, PUFs, root of trust (week 11)
- Lightweight authenticated crypto (ASCON) and AES modes
- Post-quantum cryptography and "Store Now, Decrypt Later" (SNDL)
- The lecture's own real-world examples: KeeLoq keyless entry, MIFARE transit cards, FPGA bitstream, Bitcoin wallets, smartphone-sensor PIN recovery

**Implication.** Two teams can pick the same use case, but the one whose critical issue is an *implementation-level* attack (side-channel key extraction, fault injection, a physical-layer relay/spoof) and whose mitigations come from this course's world (masking/hiding, ASCON, secure boot / root of trust, PQC for long-lived keys) will win Issue Analysis (35%) and Uniqueness (10%), and can build a demo that mirrors the lab, which is credibility plus the +5%. A deep-dive that ends on generic "use TLS / DDoS protection" reads as a standard IT talk and leaves marks on the table.

**Portable demo advantage.** One demo engine covers several of the ideas below: generate synthetic AES power traces (Hamming-weight leakage + noise) and run **Correlation Power Analysis (CPA) to recover a key byte live**. It is pure Python, needs no hardware, and is exactly what the SCA lab teaches. Any AES-on-embedded target (smart meter, key fob, implant, payment card) can reuse it. A second reusable engine is a **fault-injection simulation** (a glitch that skips a comparison/loop to bypass a check).

---

## Ranking (novelty and demo weighted highest)

Scores are 1-5. "Course fit" = how well the deep-dive maps to side-channel / fault / hardware security.

| # | Use case | Novelty | Demo | Course fit | CIA richness | Verdict |
|---|----------|:------:|:----:|:----------:|:------------:|---------|
| 1 | Implantable/medical device key extraction | 5 | 4 | 5 | High | Boldest novelty + on-topic |
| 2 | Smart meter (AMI) power-analysis | 4 | 5 | 5 | Very high | Best all-rounder |
| 3 | Teleoperated robotic surgery | 5 | 4 | 3 | High | Highest novelty, weaker HW fit |
| 4 | Automotive ECU / EV fault-injection | 4 | 4 | 5 | High | Great for the fault-injection angle |
| 5 | Keyless car entry (KeeLoq / PKES) | 3 | 5 | 5 | Medium | Safest fit, lowest novelty |
| 6 | EV charging + grid switching attack | 3 | 5 | 3 | High | Strong systems demo |
| 7 | Precision agriculture drones | 4 | 3 | 3 | Medium | Novel, softer security depth |
| 8 | Contactless payment / transit card | 3 | 4 | 5 | Medium | Solid but common target |

**Top recommendations given your priorities:**

- **Boldest (novelty + demo + on-topic): #1 Implantable medical device with a side-channel/relay key-extraction deep-dive.** Rare in a student setting, fits your healthcare background, and the CPA demo carries it.
- **Safest high score: #2 Smart meter (AMI).** Clean positive-impact story, the deep-dive is textbook course material, and the demo is the best of the set.
- **Pure uniqueness play: #3 Robotic surgery**, if you would rather wow on the system than on the hardware attack.

---

## Group A: Hardware / side-channel aligned (recommended)

### 1. Implantable / wearable medical device: key extraction  (novelty 5, demo 4)

**System.** An implanted pacemaker/ICD or a closed-loop insulin pump with a wireless link to a home transmitter or phone. Sense to compute to actuate, directly on the body.

**Positive impact.** Remote monitoring catches arrhythmias or glucose excursions early, automates therapy, reduces admissions, saves lives. Societal and economic upside is large and concrete.

**Unique feature.** A safety-critical control loop small enough to sit inside a body, so it runs tiny embedded crypto on a power- and area-constrained chip. That constraint is exactly why side-channel and lightweight-crypto arguments apply.

**Three CIA issues.**
- **Confidentiality (deep-dive candidate):** the device authenticates commands with an embedded key; **side-channel (power/EM) or a relay attack can recover or bypass that key**, so an attacker can pair as a legitimate controller. Grounded in the St. Jude/Abbott recall of 465,000 devices (2017) and the Medtronic MiniMed replay flaw (CVE-2019-10964).
- **Integrity:** once paired, forged commands deliver inappropriate pacing/shock or a wrong insulin dose.
- **Availability:** battery-drain or RF jamming disables therapy.

**Why confidentiality (key exposure) is most critical.** It is the root cause: extract or bypass the key and the integrity/availability attacks all follow. Consequences span safety (lethal), operational (device recall), reputational/regulatory (FDA action, which really happened).

**Mitigations (technical / organizational / procedural).** Side-channel-hardened crypto (masking and hiding); lightweight authenticated encryption (ASCON) sized for the implant; distance-bounding / proximity pairing to defeat relay; secure element as root of trust; coordinated disclosure and OTA patching (the real fix). PQC is a fair "future" note given device lifetimes.

**Demo.** Reuse the CPA engine: show simulated power traces of the device's AES/authentication step, then recover a key byte by correlation. Punchline: "the secret that protects a human heart leaked through power, not the network." Optionally add the masking countermeasure and show the correlation collapse.

---

### 2. Smart meter / Advanced Metering Infrastructure  (novelty 4, demo 5)  BEST ALL-ROUNDER

**System.** Networked smart meters measure consumption, report over AMI to the utility, and accept remote commands (e.g., disconnect). AES-128 secures the link. A clear sensor-compute-actuate-communicate CPS.

**Positive impact.** Grid efficiency and demand response, accurate real-time billing, faster outage detection, integration of renewables and EVs, less manual meter reading. Strong economic and environmental story.

**Unique feature.** Millions of identical embedded endpoints, physically accessible on the sides of homes, each holding cryptographic keys. Scale plus physical access is the interesting threat model.

**Three CIA issues.**
- **Confidentiality (deep-dive candidate):** **Correlation Power Analysis extracts the AES-128 key** from a meter an attacker can physically hold, because the endpoint is unguarded and dispersed.
- **Integrity:** with the key, forge meter readings for billing fraud or inject false grid telemetry.
- **Availability:** with the key, replay or issue mass remote-disconnect commands to destabilise supply.

**Why confidentiality (key extraction) is most critical.** One extracted key can generalise across a meter family (shared or weakly diversified keys), turning a single lab attack into fleet-wide integrity and availability attacks. Consequences: economic (fraud), operational (grid instability, mass disconnects), reputational (utility trust), safety (loss of power to critical loads).

**Mitigations.** Masking/hiding SCA countermeasures on the crypto core; per-device key diversification; ASCON lightweight AEAD; secure element / root of trust for key storage; anomaly detection on consumption and command patterns; and PQC for the 15-20 year meter lifetime, where SNDL is a real concern.

**Demo.** The flagship CPA demo: synthetic AES traces to on-screen recovery of a key byte, then flip on masking and show it fail. Mirrors the SCA lab one-to-one.

---

### 4. Automotive ECU / EV secure boot: fault injection  (novelty 4, demo 4)

**System.** A modern vehicle is a network of ECUs (electronic control units) governing braking, steering, battery management. Secure boot and signed firmware are the root of trust.

**Positive impact.** Driver-assist and safety features, emissions control, EV battery management, OTA updates that fix defects without recalls.

**Unique feature.** Safety-critical actuation (brakes, throttle, battery) gated by embedded security that an attacker with physical access can glitch.

**Three CIA issues.**
- **Integrity (deep-dive candidate):** **voltage/clock glitching (fault injection) skips a signature check or secure-boot step**, letting unsigned firmware run. Aligns with weeks 8-10 and the Fault-Analysis lab.
- **Confidentiality:** side-channel extraction of firmware-encryption or immobiliser keys.
- **Availability:** flooding the CAN bus or triggering fail-safe modes disables functions.

**Why integrity via fault injection is most critical.** Bypassing secure boot compromises the whole trust chain and can enable unsafe actuation. Consequences: safety (crash), operational (bricked/recalled fleet), reputational.

**Mitigations.** Fault-injection countermeasures (redundant checks, double-verification, control-flow integrity, glitch sensors); secure boot with hardware root of trust; message authentication on CAN; ASCON for constrained ECUs.

**Demo.** Fault-injection simulation: a signature/PIN check loop where an injected "glitch" flips the comparison and unlocks a normally-rejected firmware. Visual and directly tied to the fault lab.

---

### 5. Keyless car entry: KeeLoq / Passive Keyless Entry & Start  (novelty 3, demo 5)

**System.** Rolling-code key fob and immobiliser (KeeLoq), or modern PKES where the car unlocks/starts on proximity.

**Positive impact.** Convenience and anti-theft rolling codes; PKES removes the physical key.

**Three CIA issues.**
- **Confidentiality (deep-dive candidate):** **DPA recovers the KeeLoq manufacturer/device key and clones a fob from ~10 power traces**; or a **relay attack** extends the PKES signal to unlock a car whose key is indoors.
- **Integrity:** cloned credential grants unauthorised unlock/start.
- **Availability:** jamming the fob (rolljam) blocks legitimate locking.

**Why the key-extraction/relay is most critical.** It defeats the anti-theft premise entirely and enables silent, scalable theft. Consequences: economic (theft), reputational (model-wide vulnerability), safety.

**Mitigations.** Side-channel-hardened key storage; UWB distance-bounding against relay; authenticated lightweight crypto; motion-sensing fobs.

**Demo.** CPA engine again, or a clean relay-attack animation (attacker A near the house, attacker B at the car). Note: strongest *fit* but lowest novelty because it is in the professor's own slides, so expect other teams to consider it.

---

### 8. Contactless payment / transit access card (MIFARE DESFire)  (novelty 3, demo 4)

**System.** Contactless smartcards for payment, transit, and building access; hardware crypto (3DES/AES) on the card.

**Positive impact.** Fast, cashless, high-throughput access; fraud reduction versus magnetic stripe.

**CIA issues.** Confidentiality (side-channel key extraction enabling **card cloning**, deep-dive), Integrity (forged balances/access), Availability (jamming readers). NXP discontinued a DESFire product after a successful CPA clone (~250k traces), a strong real anchor. Mitigations mirror the others (SCA countermeasures, key diversification, ASCON, root of trust). Demo: CPA engine. Solid but a very commonly analysed target, so novelty is modest.

---

## Group B: Systems-level picks (higher novelty on the system, demo is a simulation not a hardware attack)

### 3. Teleoperated robotic surgery  (novelty 5, demo 4)

**System.** Surgeon console to networked robot operating on a possibly-remote patient (research platform: Raven II, University of Washington).

**Positive impact.** Expert surgery in remote, rural, battlefield, or disaster settings; precision and tremor reduction.

**CIA issues.** Integrity (a **MITM modifies/injects commands**, demonstrated on Raven II by UW, deep-dive), Availability (a single crafted packet triggers the robot's emergency-stop; DoS makes it jerky), Confidentiality (unencrypted video/command streams leak patient and procedure).

**Why integrity is most critical.** Silent command tampering during surgery can injure or kill unnoticed. Mitigations: end-to-end encryption + per-packet HMAC to detect tampering, sequence numbers/timestamps against injection/replay, redundant links, dedicated QoS networks. **Demo:** simulate the surgeon-to-robot path; MITM nudges the arm off a target trajectory; enable HMAC and tampered packets get rejected. Highest novelty; the deep-dive is protocol-level rather than hardware, so it fits the course a bit less, but it is defensible and visually excellent.

### 6. Smart EV charging + grid switching attack  (novelty 3, demo 5)

**System.** Networked EV chargers on OCPP coordinating charging and demand response with the grid.

**Positive impact.** Load balancing, renewables integration, V2G, avoided peaks.

**CIA issues.** Availability/Integrity (**synchronised switching of many compromised chargers creates demand spikes that can black out a grid**; six OCPP zero-days found in 2024, deep-dive), Integrity (billing/pricing tampering), Confidentiality (weak OCPP auth leaks user/location/payment). Mitigations: mutual TLS auth, per-charger rate-limiting/staggering, grid-side anomaly detection, segmentation. **Demo:** neighbourhood of chargers plus a grid load meter; synchronised on/off oscillates load past a blackout line; auth + staggering damps it. Great systems demo, softer on the hardware-security angle.

### 7. Precision agriculture drones/sensors  (novelty 4, demo 3)

**System.** Soil/crop sensors, GPS-guided drones and robots, cloud analytics driving irrigation/spraying.

**Positive impact.** Higher yields, less water/chemical, food security, environmental gains.

**CIA issues.** Integrity (**spoofed sensor data or GPS pushes a drone off course / mis-waters a field**, deep-dive, and GPS spoofing is a genuine physical-layer attack that fits the course), Availability (jamming halts irrigation), Confidentiality (yield data leakage). Mitigations: authenticated/encrypted telemetry, plausibility checks, GPS-spoofing detection, secure firmware. **Demo:** irrigation controller reacting to a live "moisture" feed; inject spoofed readings to flood/wilt; signed messages + range checks reject the spoof.

---

## Presentation best practices (mapped to your rubric)

**Open with the attack, not the definition.** Lead with the human/physical stakes ("a key that protects a heart, or a whole street's electricity meters, leaked through power consumption"), then explain the system. Grabbing attention early is the most repeated presentation tip.

**Comprehensiveness (35%).** One clean architecture diagram (sensor to controller to actuator to network). State problem, impact across societal/economic/environmental, and one genuinely unique feature (predictive analytics, digital twin, on-body control, grid-scale actuation). Do not rush this; it is a joint-largest scored block. Note the slide even suggests naming a unique feature like predictive analytics or digital twins.

**Issue Analysis / CIA (35%).** A 3-row table: issue, CIA class, one-line operational relevance. Ground at least one issue in a real incident (the CVEs, recalls, and published attacks cited here) so it reads as realistic, not hypothetical. This is where the hardware-attack framing separates you from other teams.

**Mitigation (20%).** For the one critical issue, give consequences across safety / operational continuity / reputation (the slide's exact three axes), then mitigations across technical / organizational / procedural, and justify feasibility and effectiveness. Reference course concepts by name: masking/hiding, ASCON, secure boot / root of trust, and PQC/SNDL for long-lived keys. Make a defensible choice, not a list of ten.

**Uniqueness (10%).** Novelty comes from the angle as much as the system. A side-channel or fault-injection deep-dive on a familiar system still reads as novel to this grader.

**Demo (+5%).** A 60-90 second "normal to attack to mitigated" simulation is the highest-leverage time in the talk. Pre-build and rehearse it; keep a screen recording as backup. The CPA key-recovery demo is ideal because it mirrors the lab.

**Delivery.** Three members, one part each (the slide is explicit). Time budget: Part 1 4-5 min, Part 2 4-5 min, Part 3 5-6 min, with the demo inside Part 3. Rehearse to land under 15:00; 5 min Q&A follows.

---

## Logistics you should not miss (from Lecture 2)

- **Team size is now "exactly 3 students."** Your team lists Ujwal and Markie (2). Lecture 1 said teams of 2; Lecture 2 changed it. You likely need a third member.
- **Confirm team + use case by 25 August** via email to sbhasin@ntu.edu.sg. That is close, so lock a direction this week.
- Presentation date 09/09/2026 (lecture 5 slot); the SCA hands-on lab (29/8 and 5/9) lands right before it, so a side-channel demo will be fresh in everyone's mind, including the grader's.

---

## My bottom line

If you want maximum novelty with a demo that still lands, go **medical-implant key extraction (#1)**. If you want the safest high score with the best demo-to-effort ratio, go **smart meter AMI (#2)**. Both let the deep-dive be a side-channel attack with course-native mitigations, which is where the marks are. Robotic surgery (#3) is the pick if you would rather dazzle on the system than on the hardware attack.

---

## Sources

- [ISO: Cyber-physical systems](https://www.iso.org/foresight/cyber-physical-systems.html)
- [Fortinet: What is the CIA Triad](https://www.fortinet.com/resources/cyberglossary/cia-triad)
- [KeeLoq and Side-Channel Analysis: Evolution of an Attack (IEEE)](https://ieeexplore.ieee.org/document/5412857/)
- [On the Power of Power Analysis: Complete Break of KeeLoq (CRYPTO 2008 PDF)](https://www.iacr.org/archive/crypto2008/51570204/51570204.pdf)
- [Power-Based Side-Channel Attack for AES Key Extraction (arXiv)](https://arxiv.org/pdf/2203.08220)
- [Security of Smart-Meters against Side-Channel Attacks (ResearchGate)](https://www.researchgate.net/publication/339593548_Security_of_Smart-Meters_against_Side-Channel-Attacks_SCA)
- [St. Jude pacemaker recall over hacking (SecurityWeek)](https://www.securityweek.com/st-jude-medical-recalls-465000-pacemakers-over-security-vulnerabilities/)
- [Medtronic insulin pump vulnerability (SecurityWeek)](https://www.securityweek.com/some-medtronic-insulin-pumps-vulnerable-hacker-attacks/)
- [UW: Hacking a teleoperated surgical robot, Raven II](https://www.washington.edu/news/2015/05/07/uw-researchers-hack-a-teleoperated-surgical-robot-to-reveal-security-flaws/)
- [Targeted Attacks on Teleoperated Surgical Robots (DSN 2016 PDF)](https://homa-alem.github.io/papers/DSN_2016.pdf)
- [EV charging OCPP zero-days and grid risk (Upstream)](https://upstream.auto/cybersecurity-risks-ev-charging-ecosystem/)
- [Cybersecurity in precision agriculture (Infosecurity Magazine)](https://www.infosecurity-magazine.com/blogs/cybersecurity-in-precision/)
- [NIST post-quantum cryptography standards (FIPS 203/204/205)](https://csrc.nist.gov/pubs/fips/203/final)
- [SANS: Secrets to successful cybersecurity presentations](https://www.sans.org/cyber-security-courses/effective-security-presentations)
