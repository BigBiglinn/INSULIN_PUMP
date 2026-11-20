# Literature Review {#ch:lit}

This chapter surveys the background the design draws on. It is limited to what bears on the decisions in Chapter 3. Statements about commercial devices are general and come from the project's background note "Technical and Clinical Architecture of Modern Insulin Infusion Pumps" (uploaded to the project on 4 August 2026) [26]. None of the figures in that note is used as a requirement of this project.

## Commercial insulin-pump architectures

Commercial pumps fall into two families. **Tethered (durable) pumps** such as the Medtronic MiniMed and Tandem t:slim X2 carry a reservoir and drive in a reusable body and deliver through an infusion set. **Patch pumps** such as the Insulet Omnipod attach the whole disposable pump to the skin. In both, a small motor and a mechanical transmission advance a plunger or pump a fixed volume per stroke. A low-power microcontroller handles dosing, and a separate monitoring circuit or processor can stop delivery. Occlusion sensing, air or reservoir sensing, alarms and wireless links to a CGM or phone are standard features. The background note was used only to understand this common structure. The project goal is explicitly to *recreate the function* of a pump, not to copy any commercial device's architecture (owner requirement U-14).

## Drive mechanisms and actuators

**Stepper or DC motor with a leadscrew** is the classical syringe-pump drive. It is cheap and well understood, but the gearbox and screw add backlash, friction that varies along the stroke, and size, and a stepper with no position sensor cannot detect a missed step. The v1 rig used exactly this arrangement (NEMA 17 on a T8 leadscrew), and its size was the reason for the v2 re-scope.

**Piezoelectric motors** use the deformation of piezoceramic elements. Two kinds were considered in this project:

- **Ultrasonic (resonant) motors**, such as the Shinsei USR30 family, run at a resonance in the tens of kilohertz. The USR30-E3 was rejected on 27 September after a datasheet check: its humidity limits do not suit the climate of Guwahati, its thrust-load limits do not suit a leadscrew, and its size is impractical.
- **Quasi-static walking ("LEGS") motors**, such as the PiezoMotor LL06, move a drive rod by the coordinated bending and extension of four piezo legs. They need four synchronised 0–48 V waveforms, which is why single-channel piezo drivers such as the TI DRV8662 and DRV2700 were rejected. In return they give nanometre-scale positioning, a direct linear output with no transmission, and **self-locking when unpowered**: the LL06 holds its rod with more than its 6.5 N stall force. Resonance tracking, backlash compensation and anti-free-flow valves are therefore unnecessary in this design (HARDWARE_CONSTRAINTS section 2.2).

Other candidates were New Scale Squiggle motors and DTI motors. They were listed and not selected; the reasons are not recorded beyond that.

## Occlusion detection

A blocked infusion line must raise an alarm before a large volume has been pushed against the blockage, and the stored volume must not be released as a bolus when the blockage clears. IEC 60601-2-24 describes the test method [7]. Common approaches are:

- a **pressure or force sensor** in the fluid path or between the drive and the plunger, which is direct but adds a part and a fluid interface;
- **motor current**, which works for DC and stepper motors whose current rises with load. It is not usable here, because piezo legs are capacitive and their current does not track load;
- **position error**, comparing commanded and measured motion.

This project uses the third principle in a new form. A LEGS motor's step length shrinks smoothly with load, so the ratio of measured encoder travel to commanded waveform steps estimates the load and hence the line pressure. In the reference firmware simulation, which used an assumed plant (friction 1.5 N, compliance 2 µL/bar, step length linear with load), an alarm occurred after about 0.21 U had been pushed into a blocked line, at about 773 mmHg. Whether step length falls smoothly and repeatably with load on the real motor is **unproven** (OPEN_QUESTIONS section D). Bench check MT-05 measures exactly this curve.

## Glucose–insulin modelling and control {#sec:bergman}

Closed-loop insulin delivery needs a model of how plasma glucose responds to insulin. The **Bergman minimal model** [1] is the most widely used compact model. In a common form with an exogenous insulin input it reads:

!eq eq:bergman1 | dG/dt = −(p_{1} + X(t))·G(t) + p_{1}·G_{b} + R_{a}(t)/V_{G}
!eq eq:bergman2 | dX/dt = −p_{2}·X(t) + p_{3}·(I(t) − I_{b})
!eq eq:bergman3 | dI/dt = −n·(I(t) − I_{b}) + u(t)/V_{I}

Here G is plasma glucose and G_{b} its basal value; X is the remote insulin action; I is plasma insulin and I_{b} its basal value; p_{1} is glucose effectiveness, and p_{2}, p_{3} set the insulin-action dynamics, with p_{3}/p_{2} the insulin sensitivity; n is the insulin clearance rate; R_{a}(t) is the rate of glucose appearance from a meal; V_{G} and V_{I} are distribution volumes; and u(t) is the insulin infusion rate, the controller output. {eq:bergman1} says that glucose falls faster when insulin action X is high. {eq:bergman2} says that insulin action follows plasma insulin with a lag. {eq:bergman3} says that infused insulin raises plasma insulin, which is then cleared.

Controllers studied with such models range from PID, which is simple and has well-understood tuning but reacts late to meals because of the insulin-action lag, to model-predictive control, which uses the model to look ahead and can respect constraints such as maximum infusion rate and insulin-on-board. A safety supervisor that limits or suspends delivery when predicted glucose is low is common to both. The paper by Kaçar, Özer and Taşçıoğlu (ICAT'19) [2], studied in the project on 21 September 2026, simulated a piezoelectric valveless micropump in COMSOL and Simulink with PID control of a Bergman plant. It was used as background only, because its actuator is unrelated to this design.

The v1 HybridPancreasSim implemented the Bergman minimal model in C++ (`BergmanModel.h`) together with PID and predictive controllers (`Controllers.h`), a safety supervisor and fault injection ({sec:v1}).

## Safety architecture and standards

Infusion-pump safety rests on three ideas that recur across the standards:

- every hazard is traced to a control and to a test that proves it (ISO 14971 [8]);
- no single fault may cause an unsafe over-delivery (IEC 60601-1 and IEC 60601-2-24 [7]); and
- safety software is developed and verified with a defined process (IEC 62304 [9]) and coding rules (MISRA C [10]).

A widely used pattern is an independent supervisor, a second processor of a different type running different code, that can remove motor power but cannot command delivery. For wireless control, the Bluetooth SIG's Insulin Delivery Service [11] defines a command layout with counters and integrity checks, and LE Secure Connections pairing protects the link.

This project is *designed and tested to the methods* in these standards but is not certified to any of them. The standards table in {app:req} records, for each standard, whether it is used as a test method, as a design input or for awareness only.

## Power conversion for piezo drives

The PMD401 requires 48 V ±5 % at up to 100 mA, while a single Li-ion cell supplies 3.0–4.2 V. A plain boost converter needs a duty cycle D = 1 − V_{in}/V_{out}. That is 0.94 at 3.0 V input, beyond the 93 % maximum duty of practical controllers, and the switch would also see the full 48 V. A **flyback converter** uses a coupled inductor (transformer) with turns ratio n, so that V_{out}/V_{in} = n·D/(1 − D). With n = 5 the duty cycle falls to about 0.70–0.77. Because a flyback has no DC path from input to output, disabling the controller removes the output entirely, which suits a fail-off kill switch. TI's LM5155/LM51551 datasheet [3] includes a typical non-isolated flyback application, which this design follows. On Rev A, the same job is done by two off-the-shelf modules (Pololu U3V70F12 3.7 → 12 V, then the Analog Devices DC2628A, an LT8362 demo board, 12 → 48 V).

## Research gap

Commercial pumps use rotary motors with transmissions and, in many cases, dedicated occlusion sensors. Published piezo pumps are mostly valve-based micropumps whose flow depends on fluid properties and back-pressure. The literature reviewed in the project contains no pump that uses a quasi-static piezo walking motor to push a syringe plunger directly and also derives occlusion pressure from that motor's step length. This project aims to fill that gap, and to do it with a dual-MCU fail-off architecture from a single cell. Because no hardware has been built, the claim is so far a design claim only.
