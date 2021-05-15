# IntrinsicML
Tinkering with ML Setups that learn without any outside data. The name for this comes from intrinsic motivation: making agents that play, and enjoy doing things in simulated worlds because it's fun and interesting (technically, making agents that have drives for competence and autonomy).

The goal of this direction of work is to make something that looks like culture. It's fine if it's different in many ways, I just want it to have a lot of the same underlying components. Another way to view this work is as alternative approaches to ALife and Open-Endedness, or as investigating capabilities we should probably expect agents to discover at high enough levels of scaling.

Three current high level directions are:

- Simulated Economy/Production chain, where the products are proofs in metamath. Goal here is to have an open-ended economy I can study, and investigating if you can get complex behaviour with very simple agents. Might also involve some automated theorem proving as an easier way of diagnosing which kind of the theorems I'd like my economy to discover and avoid.
- Iterated game playing (using game theory loss matrices, potentially also partial monitoring). Part of determining what it means to learn without outside data by starting from minimal pieces and working up from them. Goal is to see how far I can get with this, or if I need other things, such as more specifics about agent internals and environment agent boundary.
- "Interesting" object discovery in Conway's game of life. Goal is to eventually expand this to arbitrary cellular automata, and eventually arbitrary systems. Long term, the hope would be to be to develop a tool for game designers that specialize in system design.
