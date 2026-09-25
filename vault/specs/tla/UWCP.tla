-------------------------------- MODULE UWCP --------------------------------
(***************************************************************************)
(* The concurrency core of the Universal Workstream Continuity Plane: one  *)
(* goal, a chain of epochs, one authority home, a fenced resource.         *)
(*                                                                         *)
(* Each code behaviour is a BOOLEAN constant, so one spec checks the       *)
(* target design (UWCP.cfg, all TRUE) and every predicted defect (the      *)
(* other cfgs), and the gate proves each can go red.                       *)
(*   FenceAtResource     the resource refuses an effect with a stale fence *)
(*   RefuseEndedReceipt  ingest refuses a receipt for an ended epoch or a  *)
(*                       stale fence (landed in cf4d71b)                   *)
(*   UnknownIsNotLost    "cannot observe" never ends an epoch (A2a/b; the  *)
(*                       defect is providers/claude.py observe -> LOST)    *)
(*   SuccessorNeedsStopEvidence  a successor needs positive evidence the   *)
(*                       previous executor stopped (A2e). Split from the   *)
(*                       flag above after TLC's first counterexample went  *)
(*                       through Expire, not FalseLost: two mechanisms,    *)
(*                       one cfg each.                                     *)
(*   BoundExists         an UNKNOWN wait ends in BLOCKED_ENVIRONMENT       *)
(*   CancelAbsorbing     cancel is terminal (S1-7)                         *)
(* Fairness is given to system actions only, never to faults or operators: *)
(* the network may never come back, and nobody is obliged to cancel.       *)
(***************************************************************************)
EXTENDS Naturals, FiniteSets

CONSTANTS Epochs, MaxGen,
          FenceAtResource, RefuseEndedReceipt, UnknownIsNotLost, SuccessorNeedsStopEvidence,
          BoundExists, CancelAbsorbing

VARIABLES goal,            \* "active" | "paused" | "cancelled"
          st,              \* epoch lifecycle at the home
          obs,             \* what the home last observed of the epoch's executor
          alive,           \* ground truth: is the executor process running?
          efence,          \* fence each epoch was given (0 = none yet)
          gen,             \* current fence generation at the authority
          pending,         \* an executor wrote a receipt the home has not ingested
          blocked,         \* BLOCKED_ENVIRONMENT
          staleEffect,     \* history: the resource accepted an effect with a stale fence
          receiptAfterEnd  \* history: the home accepted a receipt for an ended epoch

vars == <<goal, st, obs, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

States == {"idle", "dispatching", "running", "ended"}
Views  == {"none", "running", "unknown", "ended"}
Open   == {e \in Epochs : st[e] \in {"dispatching", "running"}}

TypeOK ==
    /\ goal \in {"active", "paused", "cancelled"}
    /\ st \in [Epochs -> States]
    /\ obs \in [Epochs -> Views]
    /\ alive \in [Epochs -> BOOLEAN]
    /\ efence \in [Epochs -> 0..MaxGen]
    /\ gen \in 0..MaxGen
    /\ pending \in [Epochs -> BOOLEAN]
    /\ blocked \in [Epochs -> BOOLEAN]
    /\ staleEffect \in BOOLEAN
    /\ receiptAfterEnd \in BOOLEAN

Init ==
    /\ goal = "active"
    /\ st = [e \in Epochs |-> "idle"]
    /\ obs = [e \in Epochs |-> "none"]
    /\ alive = [e \in Epochs |-> FALSE]
    /\ efence = [e \in Epochs |-> 0]
    /\ gen = 0
    /\ pending = [e \in Epochs |-> FALSE]
    /\ blocked = [e \in Epochs |-> FALSE]
    /\ staleEffect = FALSE
    /\ receiptAfterEnd = FALSE

\* A successor needs POSITIVE evidence that every earlier executor stopped.
StopEvidence(e) == \A f \in Epochs \ {e} : st[f] = "ended" => obs[f] = "ended"

Begin(e) ==
    /\ goal = "active" /\ st[e] = "idle" /\ Open = {}
    /\ gen < MaxGen - 1                     \* leave room for a cancel to fence
    /\ SuccessorNeedsStopEvidence => StopEvidence(e)
    /\ st' = [st EXCEPT ![e] = "dispatching"]
    /\ gen' = gen + 1
    /\ efence' = [efence EXCEPT ![e] = gen + 1]
    /\ UNCHANGED <<goal, obs, alive, pending, blocked, staleEffect, receiptAfterEnd>>

Launch(e) ==
    /\ st[e] = "dispatching"
    /\ st' = [st EXCEPT ![e] = "running"]
    /\ alive' = [alive EXCEPT ![e] = TRUE]
    /\ obs' = [obs EXCEPT ![e] = "running"]
    /\ UNCHANGED <<goal, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

\* The executor attempts a side effect; the RESOURCE decides.
Effect(e) ==
    /\ alive[e]
    /\ LET accepted == IF FenceAtResource THEN efence[e] = gen ELSE TRUE
       IN staleEffect' = (staleEffect \/ (accepted /\ efence[e] < gen))
    /\ UNCHANGED <<goal, st, obs, alive, efence, gen, pending, blocked, receiptAfterEnd>>

Finish(e) ==                                \* the executor exits and leaves a receipt
    /\ alive[e]
    /\ alive' = [alive EXCEPT ![e] = FALSE]
    /\ pending' = [pending EXCEPT ![e] = TRUE]
    /\ UNCHANGED <<goal, st, obs, efence, gen, blocked, staleEffect, receiptAfterEnd>>

Crash(e) ==                                 \* the executor dies with no receipt
    /\ alive[e]
    /\ alive' = [alive EXCEPT ![e] = FALSE]
    /\ UNCHANGED <<goal, st, obs, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

NodeUnreachable(e) ==                       \* fault: the home cannot see the node
    /\ st[e] \in {"running", "ended"} /\ obs[e] \in {"running", "none"}
    /\ obs' = [obs EXCEPT ![e] = "unknown"]
    /\ UNCHANGED <<goal, st, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

ObserveOK(e) ==                             \* the network came back (never fair)
    /\ obs[e] = "unknown"
    /\ obs' = [obs EXCEPT ![e] = IF alive[e] THEN "running" ELSE "ended"]
    /\ blocked' = [blocked EXCEPT ![e] = FALSE]
    /\ UNCHANGED <<goal, st, alive, efence, gen, pending, staleEffect, receiptAfterEnd>>

ObserveExit(e) ==                           \* a reachable node reports the exit
    /\ obs[e] = "running" /\ ~alive[e]
    /\ obs' = [obs EXCEPT ![e] = "ended"]
    /\ UNCHANGED <<goal, st, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

\* Today's observe path: "no child handle in this process" reads as LOST.
FalseLost(e) ==
    /\ ~UnknownIsNotLost
    /\ st[e] = "running" /\ obs[e] = "unknown"
    /\ st' = [st EXCEPT ![e] = "ended"]
    /\ obs' = [obs EXCEPT ![e] = "ended"]
    /\ UNCHANGED <<goal, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

\* The home's wall bound ends an epoch whose executor may still be running.
Expire(e) ==
    /\ st[e] = "running"
    /\ st' = [st EXCEPT ![e] = "ended"]
    /\ UNCHANGED <<goal, obs, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

Harvest(e) ==                               \* ingest-before-end: nothing pending
    /\ st[e] = "running" /\ obs[e] = "ended" /\ ~pending[e]
    /\ st' = [st EXCEPT ![e] = "ended"]
    /\ UNCHANGED <<goal, obs, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

Bound(e) ==
    /\ BoundExists
    /\ st[e] = "running" /\ obs[e] = "unknown" /\ ~blocked[e]
    /\ blocked' = [blocked EXCEPT ![e] = TRUE]
    /\ UNCHANGED <<goal, st, obs, alive, efence, gen, pending, staleEffect, receiptAfterEnd>>

Receipt(e) ==
    /\ pending[e]
    /\ pending' = [pending EXCEPT ![e] = FALSE]
    /\ LET accepted == IF RefuseEndedReceipt THEN st[e] # "ended" /\ efence[e] = gen ELSE TRUE
       IN /\ receiptAfterEnd' = (receiptAfterEnd \/ (accepted /\ st[e] = "ended"))
          /\ st' = IF accepted THEN [st EXCEPT ![e] = "ended"] ELSE st
    /\ UNCHANGED <<goal, obs, alive, efence, gen, blocked, staleEffect>>

Cancel ==                                   \* operator: terminal, and it fences
    /\ goal # "cancelled" /\ gen < MaxGen
    /\ goal' = "cancelled"
    /\ gen' = gen + 1
    /\ UNCHANGED <<st, obs, alive, efence, pending, blocked, staleEffect, receiptAfterEnd>>

Pause ==
    /\ goal = "active" /\ goal' = "paused"
    /\ UNCHANGED <<st, obs, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

Resume ==
    /\ \/ goal = "paused"
       \/ ~CancelAbsorbing /\ goal = "cancelled"
    /\ goal' = "active"
    /\ UNCHANGED <<st, obs, alive, efence, gen, pending, blocked, staleEffect, receiptAfterEnd>>

\* Explicit terminal stutter, so TLC's deadlock check stays ON for everything else.
Done ==
    /\ \A e \in Epochs : st[e] \in {"idle", "ended"} /\ ~alive[e] /\ ~pending[e]
    /\ UNCHANGED vars

Next ==
    \/ \E e \in Epochs :
          \/ Begin(e) \/ Launch(e) \/ Effect(e) \/ Finish(e) \/ Crash(e)
          \/ NodeUnreachable(e) \/ ObserveOK(e) \/ ObserveExit(e) \/ FalseLost(e)
          \/ Expire(e) \/ Harvest(e) \/ Bound(e) \/ Receipt(e)
    \/ Cancel \/ Pause \/ Resume \/ Done

Fairness ==
    /\ \A e \in Epochs :
          /\ WF_vars(Launch(e))
          /\ WF_vars(Finish(e) \/ Crash(e))   \* the job budget eventually kills the process
          /\ WF_vars(ObserveExit(e))
          /\ WF_vars(Harvest(e))
          /\ WF_vars(Bound(e))
          /\ WF_vars(Receipt(e))

Spec == Init /\ [][Next]_vars /\ Fairness

\* ---- safety -------------------------------------------------------------
StaleFenceCannotAdvance == ~staleEffect
ReceiptOnlyForOpenEpoch == ~receiptAfterEnd
AtMostOneOpenEpoch      == Cardinality(Open) <= 1
AtMostOneLiveExecutor   == Cardinality({e \in Epochs : alive[e]}) <= 1

CancelledNeverResumes == [][goal = "cancelled" => goal' = "cancelled"]_goal
FenceMonotonic        == [][gen' >= gen]_gen
EndedIsTerminal       == [][\A e \in Epochs : st[e] = "ended" => st'[e] = "ended"]_st

\* ---- liveness -------------------------------------------------------------
DispatchingResolves  == \A e \in Epochs : st[e] = "dispatching" ~> st[e] # "dispatching"
EveryRunningEpochEndsOrBlocks ==
    \A e \in Epochs : st[e] = "running" ~> (st[e] = "ended" \/ blocked[e])
=============================================================================
