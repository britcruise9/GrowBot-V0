# GrowBot V0 Simulation Snapshot

`growbot_current_body.xml` is a standalone MuJoCo body snapshot for the current live GrowBot body.

The full setup is coming with the next version. For now it captures the measured body proportions and the rounded/rockered foot approximation I use for policy experiments. The agent harness, policy runtime, reward functions, and training code come with it.

The geometry is a measured box approximation of the same body the `mechanical/` STLs print
(body about 132 x 83 x 39 mm, 64 mm legs, the v215 rounded/rockered foot). It is close to the
printed shells within a few mm, not an exact mesh import, so print from the STLs and simulate
from this XML.
