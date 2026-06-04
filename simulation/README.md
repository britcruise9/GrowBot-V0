# GrowBot V0 Simulation Snapshot

`growbot_current_body.xml` is a standalone MuJoCo body snapshot for the current live GrowBot body.

It is not the full training setup. It captures the measured body proportions and rounded/rockered
foot approximation used for policy experiments, but the agent harness, policy runtime, reward
functions, and training code are not included here.

The geometry is a measured box approximation of the same body the `mechanical/` STLs print
(body about 132 x 83 x 39 mm, 64 mm legs, the v215 rounded/rockered foot). It is close to the
printed shells within a few mm, not an exact mesh import, so print from the STLs and simulate
from this XML.
