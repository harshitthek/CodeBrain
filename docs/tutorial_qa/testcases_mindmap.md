# DTU ROVC 2026 Competition Test Suite

## Task 1: Qualification Round Submerged Gate Navigation (6 cases)

### Subsystem: Gate Aperture & Submerged Navigation (3 cases)

#### ROVC-TC-001: Task 1 Qualification Gate Nominal Traversal
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Arena pool (20m x 10m) filled to 1.8m depth; qualification gate with 1.0m clear internal width positioned at 1.2m depth; ROV ballasted for neutral buoyancy; ~50m tether connected to surface control station.
- **Test Steps**
  - 1. Deploy the ROV into the designated poolside staging zone and verify surface telemetry link.
  - 2. Command vertical descent to align vehicle centerline with the 1.2m gate passage depth.
  - 3. Apply surge forward thrust to traverse through the 1.0m wide gate aperture.
  - 4. Maintain straight heading until vehicle stern and trailing tether segment completely clear the gate exit plane.
- **Expected Results / Assertions**
  - 1. Vehicle maintains stable depth at 1.2m ± 0.05m during gate approach.
  - 2. ROV traverses through the 1.0m gate opening with zero physical contact against uprights or crossbar.
  - 3. Trailing tether clears the gate structure without snagging, looping, or displacing gate anchoring buoys.
  - 4. Official judge scorekeeper logs a clean qualification passage on attempt 1.

#### ROVC-TC-002: Task 1 Gate Passage Lateral Clearance Boundary (1.00m Gate Opening)
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Submerged gate measured and calibrated to exactly 1.00m (100.0cm) clear internal width; vehicle width verified at 55cm; pool water still with zero surface turbulence.
- **Test Steps**
  - 1. Position the ROV 2.0m upstream of the 1.00m gate opening, offset laterally 20cm to the starboard upright.
  - 2. Steer the vehicle through the gate with starboard thruster shroud passing within 5cm of the upright.
  - 3. Monitor poolside video feed and underwater acoustic/optical sensors for contact indication.
  - 4. Verify complete passage without deflection or physical touch.
- **Expected Results / Assertions**
  - 1. Vehicle clears the 1.00m gate opening maintaining >=3cm measured clearance between thruster shroud and upright.
  - 2. Zero physical contact occurs; no vibration or contact marker triggered.
  - 3. Lateral clearance boundary validated as compliant under strict 1.00m aperture constraint.

#### ROVC-TC-003: Task 1 Submerged Depth Boundaries at 0.6m Minimum and 1.8m Maximum Limits
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Pool depth gradient configured with 0.6m shallow shelf and 1.8m deep pit; hydrostatic depth sensor calibrated with ±0.01m accuracy.
- **Test Steps**
  - 1. Command the ROV to navigate the gate positioned at the shallow boundary depth of 0.60m.
  - 2. Record vertical stability, surface wake, and thruster cavitation risk at 0.60m depth.
  - 3. Relocate gate or transit vehicle to deep boundary pit at 1.80m depth.
  - 4. Execute traversal at 1.80m depth and monitor internal hull pressure and ballast equilibrium.
- **Expected Results / Assertions**
  - 1. Vehicle navigates gate at 0.60m depth without broaching water surface or cavitating thrusters.
  - 2. Vehicle navigates gate at 1.80m depth without hull seal compression leakage or bottom grounding.
  - 3. Closed-loop depth controller holds target depth within ±0.04m across both 0.6m and 1.8m operational extremes.

### Subsystem: Attempt Quotas & Timing Penalties (1 cases)

#### ROVC-TC-004: Task 1 Maximum 3-Attempt Gate Traversal Limit & Timing Penalty Evaluation
- **Metadata**: Type: `Boundary` | Priority: `Medium`
- **Preconditions**: Judge timing system active; 3-attempt quota initialized for Task 1; stopwatch synchronized.
- **Test Steps**
  - 1. Execute Attempt 1: Intentionally touch gate upright with thruster guard; record fault and abort.
  - 2. Reset vehicle to start gate zone within the 2-minute reset window.
  - 3. Execute Attempt 2: Cause gate abort by tether entanglement; record second fault.
  - 4. Reset and execute Attempt 3: Execute clean contact-free gate passage.
  - 5. Attempt an unauthorized 4th run to verify gate attempt lockout.
- **Expected Results / Assertions**
  - 1. Judge records navigation faults for Attempt 1 and Attempt 2 with appropriate time penalties.
  - 2. Attempt 3 successfully completes contact-free gate passage and awards qualification points.
  - 3. System rejects 4th attempt; maximum 3-attempt rule enforced strictly.

### Subsystem: Thruster Collision & Tether Dynamics (2 cases)

#### ROVC-TC-005: Task 1 Thruster Stall and Gate Upright Collision Recovery
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Vehicle in active forward transit through qualification gate; telemetry monitor logging individual thruster currents.
- **Test Steps**
  - 1. Command 70% forward surge thrust through the gate.
  - 2. Simulate port surge motor stall / mechanical blockage during gate transit.
  - 3. Observe pilot emergency stabilization or autonomous yaw compensation.
  - 4. Apply reverse thrust or emergency stop before severe impact occurs.
  - 5. Extract vehicle safely to poolside staging area for fault inspection.
- **Expected Results / Assertions**
  - 1. Telemetry detects port motor overcurrent surge and flags thruster stall warning.
  - 2. Vehicle yaw rate remains controllable or failsafe neutral buoyancy prevents violent rotation.
  - 3. Hardened thruster shroud absorbs any incidental brush without hull deformation or gate damage.
  - 4. Pilot initiates safe abort; vehicle is safely recovered without hazard to pool infrastructure.

#### ROVC-TC-006: Task 1 50m Tether Trailing Gate Contact & Snag Mitigation
- **Metadata**: Type: `Exception` | Priority: `Medium`
- **Preconditions**: 50m umbilical tether deployed from pool deck; tether strain relief collar attached at vehicle stern.
- **Test Steps**
  - 1. Pilot vehicle forward through gate until main hull completely exits gate plane.
  - 2. Introduce tether slack causing trailing umbilical cable to drape over gate lower crossbar.
  - 3. Command slow forward surge thrust to test tether slip across smooth PVC gate surface.
  - 4. If snag occurs, execute pilot tether-jiggle recovery maneuver.
- **Expected Results / Assertions**
  - 1. Smooth tether jacket slides across PVC gate frame without catching or toppling gate structure.
  - 2. Strain relief prevents mechanical shock to vehicle internal penetrators.
  - 3. Vehicle completes passage without structural tether damage or electrical signal drop.

## Task 2: Low-Visibility Vision Target Identification and Touch (7 cases)

### Subsystem: Low-Visibility Vision & Onboard Illumination (3 cases)

#### ROVC-TC-007: Task 2 Low-Visibility Vision Target Nominal Identification and Soft Contact
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Pool arena lights extinguished (unlit/low-visibility condition); designated target balloon (Red) submerged at 1.0m depth; onboard LED floodlights powered; soft-touch bumper installed.
- **Test Steps**
  - 1. Extinguish arena ambient lighting to simulate low-visibility underwater environment.
  - 2. Activate onboard high-intensity LED illumination array from surface control console.
  - 3. Pilot vehicle in search pattern until camera visual feed captures target balloon.
  - 4. Perform color recognition and align vehicle probe with designated Red balloon target.
  - 5. Advance at low speed (<=0.2 m/s) and make contact with target balloon using soft probe.
  - 6. Hold contact for 3 seconds, then reverse away cleanly.
- **Expected Results / Assertions**
  - 1. Onboard lighting illuminates target with sufficient contrast for camera sensor recognition.
  - 2. Visual feed confirms Red balloon target locked and centered in reticle.
  - 3. Soft bumper makes physical contact with balloon without rupturing or deflating it.
  - 4. Successful touch verified by judge video review and full Task 2 points awarded.

#### ROVC-TC-008: Task 2 Ambient Darkness & Onboard Illumination Lux Threshold Boundary
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Photometer placed at balloon target location; ambient pool water darkness measured at <5 lux; onboard light dimmer calibrated.
- **Test Steps**
  - 1. Set onboard illumination to minimum output (20% power / ~100 lumens).
  - 2. Measure target lux level at 1.5m standoff distance.
  - 3. Incrementally increase illumination power (40%, 60%, 80%, 100%) until color segmentation algorithm reaches >=90% confidence score.
  - 4. Record minimum lux threshold required for positive color identification.
- **Expected Results / Assertions**
  - 1. Target becomes identifiable at >=50 lux incident illumination at 1.5m standoff distance.
  - 2. Onboard illumination delivers >=200 lux at 1.0m target distance at 80% duty cycle.
  - 3. Color segmentation confidence exceeds 92% meeting low-visibility boundary criteria.

#### ROVC-TC-011: Task 2 Onboard Illumination Electrical Circuit Failure in Unlit Pool
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: ROV submerged at 1.5m depth in total darkness pool; light power relay mapped to test trip switch.
- **Test Steps**
  - 1. While navigating in dark pool, trigger onboard LED power bus disconnect.
  - 2. Observe camera video feed blackout on surface console.
  - 3. Verify pilot sensor fallback (depth, heading, IMU attitude telemetry).
  - 4. Command autonomous depth hold or gentle ascent to pool surface.
- **Expected Results / Assertions**
  - 1. Surface station immediately reports video loss / zero lux illumination fault.
  - 2. Vehicle vertical and heading hold controllers remain stable despite vision loss.
  - 3. Vehicle halts surge motion to avoid collision and ascends safely under pilot command.

### Subsystem: Target Discrimination & False-Positive Mitigation (2 cases)

#### ROVC-TC-009: Task 2 Balloon Color Discrimination Against Clutter and Distractors
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Cluster of 4 colored balloons (Green designated, Red, Blue, Yellow distractors) tethered with 40cm spacing; onboard vision system active.
- **Test Steps**
  - 1. Transmit designated target color 'Green' to pilot and computer vision pipeline.
  - 2. Approach balloon cluster under onboard illumination.
  - 3. Isolate color histograms / bounding boxes for all 4 balloons.
  - 4. Lock onto the designated Green balloon and reject Red, Blue, and Yellow distractors.
  - 5. Execute precision forward touch maneuver exclusively on the Green balloon.
- **Expected Results / Assertions**
  - 1. Vision algorithm correctly identifies and tags all 4 balloons with respective color classes.
  - 2. Guidance vector navigates directly to Green balloon ignoring adjacent distractors.
  - 3. Probe touches Green balloon without contacting neighboring balloons.
  - 4. Task validated with zero false-target contact penalties.

#### ROVC-TC-012: Task 2 False-Positive Target Touch on Wrong-Color Balloon Exception
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Designated target is Blue; vehicle approaches balloon cluster in low-light condition.
- **Test Steps**
  - 1. Pilot vehicle to intentionally touch adjacent Yellow distractor balloon.
  - 2. Record judge scoring reaction and system fault classification.
  - 3. Verify zero points awarded for the incorrect touch.
  - 4. Re-orient vehicle to locate and touch the correct Blue balloon within remaining time.
- **Expected Results / Assertions**
  - 1. Judge records touch on non-designated balloon; zero points credited for Task 2 target.
  - 2. System enforces one-touch attempt policy or records fault deduction.
  - 3. Team receives zero points or restarts from staging area per official rules.

### Subsystem: Soft-Touch Force & Probe Compliance (2 cases)

#### ROVC-TC-010: Task 2 Soft-Touch Probe Contact Force Boundary Limit (Non-Destructive Touch)
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Calibrated force transducer mounted behind probe bumper; test balloon inflated to standard competition diameter (25cm, 0.05 bar gauge).
- **Test Steps**
  - 1. Drive ROV into target balloon at nominal approach velocity (0.15 m/s).
  - 2. Record peak contact force on transducer during probe impact.
  - 3. Repeat approach at maximum allowable competition velocity (0.35 m/s).
  - 4. Inspect balloon envelope for micro-tears, scuffs, or wall thinning post-contact.
- **Expected Results / Assertions**
  - 1. Peak contact force remains <=1.8 N at 0.15 m/s and <=2.5 N at 0.35 m/s.
  - 2. Probe compliant spring mechanism absorbs kinetic energy smoothly.
  - 3. Balloon remains fully inflated and undamaged across 5 consecutive touch trials.

#### ROVC-TC-013: Task 2 Target Balloon Rupture / Excessive Contact Force Penalty
- **Metadata**: Type: `Exception` | Priority: `Medium`
- **Preconditions**: Arena target balloon tethered in pool; judge acoustic and visual monitoring active.
- **Test Steps**
  - 1. Simulate high-velocity collision or unshielded probe edge contact against balloon.
  - 2. Balloon bursts with acoustic report.
  - 3. Judge signals immediate task abort whistle.
  - 4. Vehicle ordered to surface immediately for bumper safety re-inspection.
- **Expected Results / Assertions**
  - 1. Judge disqualifies or awards zero score for Task 2 due to damaged arena property.
  - 2. Arena marshal halts competition clock to install replacement balloon.
  - 3. Vehicle barred from subsequent trials until probe compliance is physically re-certified.

## Task 3: The Maze Walk Submerged Traversal (8 cases)

### Subsystem: Maze Channel Navigation & Obstacle Avoidance (4 cases)

#### ROVC-TC-014: Task 3 Section 1 Straight Path Surge & Heading Hold Traversal
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Section 1 PVC maze straight corridor (width 1.2m, length 6.0m) submerged at 1.0m depth; heading gyroscope calibrated.
- **Test Steps**
  - 1. Enter Section 1 entrance gate and establish target heading of 090°.
  - 2. Apply constant 60% surge thrust to traverse the 6.0m straight corridor.
  - 3. Monitor yaw drift, sway oscillations, and wall clearance along both flanks.
  - 4. Exit Section 1 and record transit time and contact count.
- **Expected Results / Assertions**
  - 1. Heading held within ±2.5° of commanded 090° vector throughout traversal.
  - 2. Lateral distance from corridor walls maintained at >=25cm on port and starboard sides.
  - 3. Zero wall contacts recorded (0 penalty points incurred).
  - 4. Section 1 traversed cleanly in <25 seconds.

#### ROVC-TC-015: Task 3 Section 2 Obstacle Course Pylon Avoidance and Yaw Maneuvering
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Section 2 contains 3 staggered vertical PVC obstacle pylons spaced 1.5m apart; camera and telemetry active.
- **Test Steps**
  - 1. Enter Section 2 obstacle zone from Section 1 exit.
  - 2. Execute starboard yaw rotation to negotiate around Pylon 1.
  - 3. Apply port sway thrust and forward surge to clear Pylon 2.
  - 4. Re-align vehicle heading to round Pylon 3 and enter Section 3 transition corridor.
  - 5. Manage tether payout to avoid wrapping cable around obstacle pylons.
- **Expected Results / Assertions**
  - 1. Vehicle completes slalom trajectory around all 3 pylons with >=15cm minimum clearance.
  - 2. Multi-DoF thruster coordination enables tight turning radius without wall brushing.
  - 3. Tether handler maintains proper tension, preventing line snagging around pylons.
  - 4. Section 2 completed with zero obstacle contacts.

#### ROVC-TC-016: Task 3 Section 3 1.5m High-Wall Narrow Channel Submerged Traversal
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Section 3 channel bounded by 1.5m vertical PVC walls; channel internal width 1.1m; top of wall at 0.3m depth, bottom at 1.8m.
- **Test Steps**
  - 1. Submerge vehicle to 1.1m depth (midpoint of 1.5m high wall vertical span).
  - 2. Enter Section 3 narrow channel and activate active depth hold.
  - 3. Traverse the 5.0m walled channel while monitoring pitch, roll, and heave stability.
  - 4. Exit through the final maze portal into the recovery arena.
- **Expected Results / Assertions**
  - 1. Vehicle operates within the 1.5m vertical wall envelope without broaching or bottom grounding.
  - 2. Depth maintained at 1.1m ± 0.08m throughout channel navigation.
  - 3. Narrow 1.1m channel negotiated with zero wall collisions.
  - 4. Full base points for Section 3 completion earned.

#### ROVC-TC-017: Task 3 Maze Wall Collision Penalty Deduction Boundary (<=5 Points per Contact)
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Scoring sheet calibrated with <=5.0 points deduction per verified physical contact; maze acoustic/video judges ready.
- **Test Steps**
  - 1. Traverse maze; execute Run A with exactly 1 deliberate wall brush.
  - 2. Verify judge records exactly 1 contact and deducts 5.0 points from base task score.
  - 3. Execute Run B with exactly 3 wall brushes; verify deduction equals 15.0 points.
  - 4. Execute Run C with 6 contacts; verify deduction equals 30.0 points or triggers task score floor at zero.
- **Expected Results / Assertions**
  - 1. Run A: Task score = Base Points - 5.0 points.
  - 2. Run B: Task score = Base Points - 15.0 points.
  - 3. Run C: Task score deductions cannot reduce task total below 0 points.
  - 4. Collision penalty calculation confirmed compliant with official rules.

### Subsystem: Submerged Depth Containment & Anti-Broach Boundary (2 cases)

#### ROVC-TC-018: Task 3 Section 3 Submerged Containment Boundary (Depth Hold vs Broaching)
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Section 3 wall top submerged at 0.30m below water surface; boundary depth alarm set at 0.40m.
- **Test Steps**
  - 1. Pilot vehicle along Section 3 at 0.60m depth.
  - 2. Gradually ascend toward wall top: test 0.50m, 0.45m, and 0.41m depths.
  - 3. Verify depth alarm triggers if vehicle ascends shallower than 0.40m boundary limit.
  - 4. Ensure vehicle never broaches or clears wall top from above.
- **Expected Results / Assertions**
  - 1. Telemetry triggers visual warning when vehicle depth reaches 0.40m boundary.
  - 2. Pilot or autonomous override stops ascent, maintaining submerged channel containment.
  - 3. Vehicle completes traversal without broaching surface or traversing over wall tops.

#### ROVC-TC-019: Task 3 Surface Broaching Disqualification in High-Walled Passage
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Vehicle navigating Section 3 high-walled channel; official judge observing surface profile.
- **Test Steps**
  - 1. Intentionally blow ballast or command full vertical thruster ascent.
  - 2. Propel vehicle over the top edge of the 1.5m PVC wall, surfacing into clear air.
  - 3. Observe judge whistle and immediate run abort command.
  - 4. Verify official scorecard records Disqualification / Void for Task 3.
- **Expected Results / Assertions**
  - 1. Judge identifies out-of-bounds violation: vehicle broached above 1.5m wall containment.
  - 2. Run aborted immediately; zero points awarded for Section 3.
  - 3. Protocol enforces requirement that vehicle must navigate through, not over, the maze.

### Subsystem: Dead-End Extraction & Tether Snag Recovery (2 cases)

#### ROVC-TC-020: Task 3 Dead-End Entrapment and Reverse Yaw Extraction
- **Metadata**: Type: `Exception` | Priority: `Medium`
- **Preconditions**: Maze configured with a 2.0m blind dead-end pocket branching off Section 2; vehicle inside dead-end.
- **Test Steps**
  - 1. Steer vehicle into the blind dead-end corridor until forward bulkhead is 20cm from end wall.
  - 2. Evaluate spatial options: pilot attempts 180° pirouette yaw turn in 1.2m width.
  - 3. If turn radius insufficient, engage reverse surge thrusters with stern camera / sonar assistance.
  - 4. Reverse vehicle cleanly back into main channel and re-orient onto correct course.
- **Expected Results / Assertions**
  - 1. Vehicle executes reverse exit without wedging against corner junctions.
  - 2. Tether does not foul under vehicle belly or thruster nozzles during reverse motion.
  - 3. Vehicle re-enters main course and completes maze run within allowable overall time window.

#### ROVC-TC-021: Task 3 50m Tether Snag on Obstacle Pylon in Section 2
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: 50m umbilical tether snagged on Pylon 2; pilot observes sudden vehicle arrest and tether tension spike.
- **Test Steps**
  - 1. Vehicle moves past Pylon 2; tether catches on pylon bracket.
  - 2. Surface console logs motor current spike due to forward motion impedance.
  - 3. Pilot stops forward thrust, checks rear camera view, and identifies snag location.
  - 4. Pilot executes reverse yaw rotation matching the snag loop to unwrap cable.
  - 5. Deck crew takes in slack to clear the pylon.
- **Expected Results / Assertions**
  - 1. Snag detected before cable insulation tears or penetrator is damaged.
  - 2. Counter-rotation successfully releases tether loop from pylon.
  - 3. Forward motion resumes without needing poolside diver intervention.

## Physical & Safety Constraints (14 cases)

### Subsystem: Vehicle Mass & Compact Footprint Envelope (3 cases)

#### ROVC-TC-022: Physical Constraint: Maximum Vehicle Weight Boundary (35.00kg Pass vs 35.05kg DQ)
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Certified digital hanging scale calibrated with ±0.01kg accuracy; vehicle fully assembled with battery, camera, and ballast.
- **Test Steps**
  - 1. Suspend vehicle on calibrated scale with dry tether connector; record mass reading for Vehicle A at exactly 35.00kg.
  - 2. Verify inspection official issues approved compliance stamp for 35.00kg.
  - 3. Add 50 grams of ballast to create Vehicle B weighing exactly 35.05kg.
  - 4. Record official verdict on 35.05kg reading.
  - 5. Strip non-essential mass to return vehicle to <=35.00kg and verify re-test clearance.
- **Expected Results / Assertions**
  - 1. Vehicle A (35.00 kg) validated as PASS (inclusive threshold: <=35.0 kg).
  - 2. Vehicle B (35.05 kg) validated as FAIL / Disqualification (strictly exceeds 35.0 kg limit).
  - 3. Re-weighed vehicle approved only when certified scale displays <=35.00 kg.

#### ROVC-TC-023: Physical Constraint: Lightweight Bonus Tier Boundary (<20.00kg vs 20.00kg)
- **Metadata**: Type: `Boundary` | Priority: `Medium`
- **Preconditions**: Calibrated inspection scale; scoring bonus matrix programmed per Section 6.
- **Test Steps**
  - 1. Weigh Vehicle 1: Measured mass = 19.95kg. Submit to scorecard.
  - 2. Weigh Vehicle 2: Measured mass = 20.00kg. Submit to scorecard.
  - 3. Weigh Vehicle 3: Measured mass = 25.00kg. Submit to scorecard.
- **Expected Results / Assertions**
  - 1. Vehicle 1 (19.95kg) receives maximum Lightweight Bonus Tier points (mass < 20.00kg).
  - 2. Vehicle 2 (20.00kg) enters standard weight tier; receives 0 bonus points for strict <20.0kg tier.
  - 3. Vehicle 3 (25.00kg) approved to compete with 0 weight bonus.
  - 4. Strict inequality boundary (<20.00kg) verified.

#### ROVC-TC-024: Physical Constraint: Compact Footprint Bonus Envelope Verification (L<75, B<65.01, H<60.01 cm)
- **Metadata**: Type: `Boundary` | Priority: `Medium`
- **Preconditions**: Dimensional check cube template (75.0cm x 65.01cm x 60.01cm); calibrated laser distance meter.
- **Test Steps**
  - 1. Measure Vehicle 1: Length=74.5cm, Breadth=64.8cm, Height=59.5cm; slide through gauge template.
  - 2. Measure Vehicle 2: Length=75.0cm, Breadth=65.0cm, Height=59.5cm; test against template.
  - 3. Measure Vehicle 3: Length=74.0cm, Breadth=65.02cm, Height=59.0cm; test against template.
- **Expected Results / Assertions**
  - 1. Vehicle 1 fits completely inside dimensional cube without forcing; earns Compact Footprint Bonus.
  - 2. Vehicle 2 fails bonus: Length 75.0cm does not satisfy strict L < 75.0cm requirement.
  - 3. Vehicle 3 fails bonus: Breadth 65.02cm exceeds 65.01cm ceiling.
  - 4. Dimensional envelope boundary rules rigorously enforced.

### Subsystem: External Kill Switch & Emergency Cutoff (2 cases)

#### ROVC-TC-025: Safety Constraint: External Hardware Kill Switch Actuation Latency (<100ms Cutoff)
- **Metadata**: Type: `Security` | Priority: `High`
- **Preconditions**: Vehicle secured on dry bench in water test tank; all thrusters commanded to 100% duty cycle; high-speed digital oscilloscope connected to motor ESC PWM/power rails.
- **Test Steps**
  - 1. Spin up all thrusters to 100% full forward/reverse speed.
  - 2. Actuate prominent external mechanical kill switch (red mushroom e-stop button).
  - 3. Record elapsed time from switch contact closure to total thruster power bus cutoff on oscilloscope.
  - 4. Verify zero residual motor rotation within 150ms.
- **Expected Results / Assertions**
  - 1. Actuator power bus disconnected in <80ms (strict compliance with <100ms requirement).
  - 2. All thruster spinning halts immediately.
  - 3. Auxiliary systems (grippers, pneumatics) safely de-energize.
  - 4. Kill switch verified as hardwired and failsafe.

#### ROVC-TC-026: Safety Constraint: Kill Switch Latching Relay Failure / Actuator Runaway Exception
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Vehicle on test bench; simulated welded relay contact on ESC power branch.
- **Test Steps**
  - 1. Simulate welded contact on main relay while thrusters are commanded to spin.
  - 2. Actuate external kill switch.
  - 3. Detect that primary relay failed to open.
  - 4. Verify secondary inline circuit breaker / surface tether isolation switch cuts power.
- **Expected Results / Assertions**
  - 1. Secondary surface circuit breaker trips immediately upon manual deck throw, isolating vehicle.
  - 2. Pre-event safety inspection flags relay failure; vehicle rejected until contactor is replaced.
  - 3. Redundant dual-layer power cutoff prevents hazardous runaway in pool.

### Subsystem: Electrical Safety & Branch Fusing (2 cases)

#### ROVC-TC-027: Electrical Constraint: Branch Fusing on 230V AC Supply and DC Motor ESC Rails
- **Metadata**: Type: `Security` | Priority: `High`
- **Preconditions**: Electrical distribution schematic inspected; multimeter and circuit tester available; vehicle open for bench audit.
- **Test Steps**
  - 1. Inspect surface power supply: verify 230V / 50Hz AC input is protected with 16A fast-blow circuit breaker.
  - 2. Inspect DC distribution board inside pressure hull: verify each ESC motor rail has a dedicated inline fuse (e.g. 20A ATO/ATC).
  - 3. Inspect logic board / camera rail: verify 5V/12V DC-DC converters have dedicated 2A fuse protection.
  - 4. Verify reverse polarity protection diodes / MOSFETs on main battery terminal.
- **Expected Results / Assertions**
  - 1. Surface 230V AC power protected with rated fuse/breaker meeting IEC 60898.
  - 2. Every motor branch individually fused; zero unfused power branches detected.
  - 3. Reverse polarity protection prevents damage if leads are reversed.
  - 4. Electrical safety audit marked PASS.

#### ROVC-TC-028: Electrical Constraint: Motor ESC Overcurrent Short-Circuit and Fuse Trip Exception
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Vehicle bench test fixture; port surge motor ESC wired with calibrated 20A fast-acting fuse; artificial short-circuit simulator.
- **Test Steps**
  - 1. Apply 40A overcurrent surge to port motor branch simulating fouled propeller stall.
  - 2. Measure time-to-clear for the 20A branch fuse.
  - 3. Verify faulted branch is completely de-energized.
  - 4. Verify adjacent starboard motor, logic computer, and camera feeds remain fully powered and operational.
- **Expected Results / Assertions**
  - 1. 20A fuse safely blows within <20ms, isolating faulted motor rail.
  - 2. Zero smoke, thermal damage, or PCB trace delamination occurs inside pressure housing.
  - 3. Main DC bus voltage remains stable (no brownout on telemetry or camera).
  - 4. Short-circuit containment verified compliant with competition safety rules.

### Subsystem: Pneumatics & Overpressure Protection (2 cases)

#### ROVC-TC-029: Safety Constraint: Pneumatic Auxiliary System Pressure Limit (<=6.0 bar Ceiling)
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Calibrated pneumatic pressure gauge; vehicle equipped with pneumatic gripper or ballast accumulator.
- **Test Steps**
  - 1. Connect compressed air supply to vehicle onboard pneumatic reservoir.
  - 2. Pressurize system to standard operating pressure of 4.5 bar; verify zero pressure drop over 15 minutes.
  - 3. Incrementally pressurize to 5.8 bar and 6.0 bar; monitor pressure regulator stability.
  - 4. Attempt to pressurize to 6.2 bar; verify pressure relief valve opens.
- **Expected Results / Assertions**
  - 1. Normal operating pressure maintained at <=5.0 bar.
  - 2. Mechanical pressure relief valve cracks open at 6.0 bar ± 0.1 bar, venting excess gas.
  - 3. Reservoir pressure cannot exceed 6.0 bar under any input condition.
  - 4. Safety inspection approves pneumatic system.

#### ROVC-TC-030: Safety Constraint: Pneumatic Regulator Overpressure Relief Valve Trip (>6.0 bar) Exception
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Pneumatic test bench with safety enclosure; regulator bypass valve installed.
- **Test Steps**
  - 1. Simulate upstream pressure regulator failure by opening high-pressure bypass from dive tank.
  - 2. Monitor downstream accumulator pressure spike.
  - 3. Verify relief valve vents gas rapidly into pool water.
  - 4. Measure peak pressure achieved during full bypass dump.
- **Expected Results / Assertions**
  - 1. Relief valve opens instantly, venting gas and preventing vessel rupture.
  - 2. Peak system pressure clamped below 6.2 bar.
  - 3. Pressure vessel integrity maintained with zero catastrophic failure.

### Subsystem: Environmental Containment & Optical Safety (3 cases)

#### ROVC-TC-031: Environmental Safety: Zero Environmental Chemical/Oil Leakage Strict Containment
- **Metadata**: Type: `Security` | Priority: `High`
- **Preconditions**: Clean water test tank; white absorbent inspection paper; UV blacklight for fluorescent oil detection.
- **Test Steps**
  - 1. Submerge vehicle in clear test tank for 30 minutes with thrusters cycling through forward and reverse speeds.
  - 2. Wipe water surface along vehicle perimeter with clean white oil-absorbent paper.
  - 3. Inspect water surface under UV blacklight for petroleum or synthetic sheen.
  - 4. Inspect battery enclosure for acidic/alkaline electrolyte seepage using litmus test strips.
- **Expected Results / Assertions**
  - 1. Zero oil sheen, droplets, or particulate dispersion detected on water surface.
  - 2. Absorbent paper shows zero discoloration or hydrocarbon residue.
  - 3. Litmus test confirms neutral pH (no battery chemical leakage).
  - 4. Environmental compliance certified for competition pool entry.

#### ROVC-TC-032: Environmental Safety: Propeller Shaft Dynamic Seal Oil Drip & Run Abort Exception
- **Metadata**: Type: `Exception` | Priority: `High`
- **Preconditions**: Vehicle in competition arena; simulated oil release marker deployed.
- **Test Steps**
  - 1. Release trace biodegradable test fluorescent marker at propeller shaft during mission run.
  - 2. Arena marshal detects sheen on pool surface and sounds immediate abort whistle.
  - 3. Vehicle pilot immediately shuts down all thrusters via kill switch.
  - 4. Poolside rescue team deploys oil absorbent boom and retrieves vehicle.
- **Expected Results / Assertions**
  - 1. Mission terminated immediately upon environmental sheen detection.
  - 2. Vehicle disqualified from current round per Section 7 zero-leakage mandate.
  - 3. Vehicle barred from water until shaft seals are replaced and re-inspected.

#### ROVC-TC-033: Optical Safety: Class 2 Laser Boundary Rating (<1 mW Cutoff)
- **Metadata**: Type: `Boundary` | Priority: `Medium`
- **Preconditions**: Calibrated optical power meter (spectroradiometer) at 532nm/650nm; vehicle laser diodes powered.
- **Test Steps**
  - 1. Measure optical power output of onboard parallel scaling lasers at 10cm aperture.
  - 2. Verify laser power reading is <=0.95 mW (Class 2 limit < 1.0 mW).
  - 3. Verify laser beam orientation is fixed strictly parallel to camera optical axis facing forward/downward.
  - 4. Verify physical beam shroud prevents upward stray reflections toward spectator gallery.
- **Expected Results / Assertions**
  - 1. Laser optical output measured at <1.0 mW meeting Class 2 safety standards (IEC 60825-1).
  - 2. Beam alignment certified downward/forward away from judges and spectators.
  - 3. Class 2 laser safety label affixed to vehicle hull.

### Subsystem: Battery Certification & Hydrostatic Hull Integrity (2 cases)

#### ROVC-TC-034: Safety Constraint: Certified Lithium Battery Pack Regulatory Documentation Audit
- **Metadata**: Type: `Security` | Priority: `High`
- **Preconditions**: Technical documentation binder presented at Stage 4 VALIDATE gate; battery pack physically extracted for inspection.
- **Test Steps**
  - 1. Review battery specification sheet: verify cell chemistry (LiFePO4 or certified Li-ion 18650/21700).
  - 2. Check UN 38.3 test summary document and CE/UL compliance certificates.
  - 3. Inspect physical battery pack: verify integrated BMS with overvoltage, undervoltage, and thermal cutoff protection.
  - 4. Inspect fireproof battery containment bag/vessel.
- **Expected Results / Assertions**
  - 1. Valid UN 38.3 and manufacturer certificates verified and stamped by safety official.
  - 2. Integrated BMS confirmed functional on all series cell groups.
  - 3. Battery approved for competition pool operation.

#### ROVC-TC-035: Structural Constraint: Hydrostatic Pressure Hull Seal Boundary at 1.8m Pool Pit
- **Metadata**: Type: `Boundary` | Priority: `High`
- **Preconditions**: Pool deep pit at 1.8m depth (hydrostatic pressure 0.18 bar gauge / ~118 kPa absolute); internal vacuum test kit or humidity telemetry sensor active.
- **Test Steps**
  - 1. Submerge vehicle to maximum pool depth of 1.80m for a continuous 20-minute soak period.
  - 2. Monitor internal relative humidity and pressure telemetry via surface telemetry stream.
  - 3. Cycle vertical thrusters to create dynamic pressure fluctuations around end-cap O-rings.
  - 4. Retrieve vehicle and conduct internal visual inspection for droplet condensation.
- **Expected Results / Assertions**
  - 1. Internal hull humidity remains constant (zero water ingress over 20-minute submersion).
  - 2. O-ring seals withstand 0.18 bar static and dynamic head pressure without deformation.
  - 3. Electronics enclosure interior remains 100% dry; pressure seal boundary verified.

## User Stories & Governance (5 cases)

### Subsystem: Category I — School Tier Teleoperation & Safety (1 cases)

#### ROVC-TC-036: User Story Category I (School): Teleoperated Flight & Teacher Safety Governance
- **Metadata**: Type: `Functional` | Priority: `Medium`
- **Preconditions**: Category I team (high school students, max 5 members) with official teacher mentor present; surface joystick control console connected.
- **Test Steps**
  - 1. Verify team roster: all 5 students from same high school, authorized by designated teacher mentor.
  - 2. Power up surface control station and pilot vehicle manually through qualification gate using gamepad joystick.
  - 3. Teacher mentor performs independent safety switch check before water entry.
  - 4. Verify surface console displays real-time depth, heading, and battery voltage.
- **Expected Results / Assertions**
  - 1. Category I team eligibility confirmed under teacher mentor governance.
  - 2. Manual teleoperation responsive with <150ms command latency.
  - 3. Pilot completes basic gate passage using surface video and telemetry.
  - 4. Safety checklist signed off by school teacher mentor.

### Subsystem: Category II — College Tier TDR & Autonomy (2 cases)

#### ROVC-TC-037: User Story Category II (College): Technical Design Report & Indigenous Thruster Bonus Audit
- **Metadata**: Type: `Functional` | Priority: `High`
- **Preconditions**: Category II team submission package; physical vehicle presented with in-house 3D printed / machined thruster assemblies.
- **Test Steps**
  - 1. Audit Technical Design Report (TDR): verify 3D CAD assemblies, hydrodynamic thrust calculations, and electrical schematics.
  - 2. Conduct physical audit of propulsion subsystem: verify thruster kort nozzles and motor housings are custom-fabricated in college makerspace.
  - 3. Inspect machining dossiers and time-lapse fabrication proof.
  - 4. Calculate and award Indigenous Innovation Bonus points per Section 7 rubric.
- **Expected Results / Assertions**
  - 1. TDR meets all documentation standards; scores >=85/100 on engineering rigor.
  - 2. Physical inspection confirms indigenous thruster design (non-COTS custom build).
  - 3. Indigenous Innovation Bonus points credited to team scorecard.

#### ROVC-TC-038: User Story Category II (College): ROS / ROS 2 Autonomous Waypoint Following Bonus
- **Metadata**: Type: `Functional` | Priority: `Medium`
- **Preconditions**: ROS 2 Humble / Iron environment active on companion computer; odometry and EKF state estimation nodes running.
- **Test Steps**
  - 1. Launch ROS 2 navigation stack: publish target waypoint coordinates for Task 1 gate entrance.
  - 2. Release manual joystick; switch vehicle into autonomous mode.
  - 3. Monitor ROS topic `/odom` and `/cmd_vel` during autonomous trajectory execution.
  - 4. Observe vehicle traverse gate without manual pilot intervention.
- **Expected Results / Assertions**
  - 1. ROS 2 node autonomously computes velocity commands and guides vehicle through gate.
  - 2. Position hold holds target within ±5cm error radius.
  - 3. Autonomous Control (ROS) Bonus points credited per Section 7 scoring guidelines.

### Subsystem: Category III — Industry Tier Benchmark (1 cases)

#### ROVC-TC-039: User Story Category III (Industry): Defense/Commercial Transferability & Zero-Fault Benchmark
- **Metadata**: Type: `Performance` | Priority: `High`
- **Preconditions**: Category III professional team entry; industrial-grade vehicle featuring anodized aluminum hull and subsea penetrators.
- **Test Steps**
  - 1. Execute back-to-back timed trials across Task 1, Task 2, and Task 3 without turnaround delay.
  - 2. Measure cumulative mission execution time across all three tasks.
  - 3. Monitor contact deductions: verify 0 wall contacts across entire maze and gate traversal.
  - 4. Audit commercial/defense transferability dossier for subsea inspection applications.
- **Expected Results / Assertions**
  - 1. All 3 tasks executed in <6 minutes total elapsed time.
  - 2. Exactly 0 contact deductions recorded across all stages.
  - 3. Industrial reliability benchmark certified meeting Category III standards.

### Subsystem: Institutional Eligibility & Team Roster Rules (1 cases)

#### ROVC-TC-040: Team Rules: Institutional Eligibility and Team Roster Boundary (Single-Institution Rule)
- **Metadata**: Type: `Security` | Priority: `High`
- **Preconditions**: Team registration portal; government/institutional identity cards for all 5 team members.
- **Test Steps**
  - 1. Audit Team A: 5 members with valid student ID cards from Delhi Technological University (DTU); verify single institution.
  - 2. Audit Team B: 4 members from DTU and 1 member from outside institution; check eligibility flag.
  - 3. Verify system rejects Team B registration or requires replacement of external member before Stage 2.
- **Expected Results / Assertions**
  - 1. Team A validated as compliant and issued official registration credential.
  - 2. Team B flagged as non-compliant with Section 4 single-institution mandate.
  - 3. Multi-institutional mixing strictly barred ensuring fair tournament governance.
