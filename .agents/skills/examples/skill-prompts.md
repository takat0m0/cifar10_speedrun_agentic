# Skill Prompt Examples

## training-log-summarizer

### Basic

```text
Use $training-log-summarizer at /root/work/cifar10_speedrun_agentic/.agents/skills/training-log-summarizer to summarize this training run.

Read:
- /root/work/cifar10_speedrun_agentic/artifacts/history.jsonl
- /root/work/cifar10_speedrun_agentic/artifacts/history.csv

Return:
- Experiment Summary
- Trend Summary
- Notable Issues
- Open Questions
```

### With stdout log

```text
Use $training-log-summarizer at /root/work/cifar10_speedrun_agentic/.agents/skills/training-log-summarizer to summarize this experiment.

Read:
- /root/work/cifar10_speedrun_agentic/artifacts/history.jsonl
- /root/work/cifar10_speedrun_agentic/artifacts/history.csv
- /root/work/cifar10_speedrun_agentic/train.log

Focus on:
- final train/validation/test accuracy
- best validation accuracy
- signs of overfitting or underfitting
- what should be inspected next
```

## experiment-next-step

### Basic

```text
Use $experiment-next-step at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-next-step to propose the next experiments.

Here is the current experiment summary:
<paste summary here>

Return:
- Current Read
- Working Hypotheses
- Recommended Experiments
- Optional Research Questions
- Next Action
```

### CIFAR-10 oriented

```text
Use $experiment-next-step at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-next-step to plan the next CIFAR-10 experiments.

Current setup:
- model: ResNet-18
- optimizer: SGD
- scheduler: cosine annealing
- dataset: CIFAR-10

Summary:
<paste summary here>

Constraints:
- keep experiments cheap
- prefer changes that isolate one factor at a time
- suggest web research only if it is likely to change the next run
```

## Two-step workflow

1. Run `training-log-summarizer` on `history.jsonl`, `history.csv`, and any stdout log.
2. Paste that summary into `experiment-next-step`.
3. Execute the highest-priority experiment first unless there is a clear resource constraint.


## experiment-code-updater

### Basic

```text
Use $experiment-code-updater at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-code-updater to implement this experiment recommendation.

Recommendation:
<paste experiment recommendation here>

Requirements:
- keep the baseline path available
- prefer opt-in CLI flags or configuration switches
- add a short smoke test command if needed

Return:
- what changed
- how to run the updated experiment
- any compatibility notes
```

### Example: loss change

```text
Use $experiment-code-updater at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-code-updater to implement this recommendation.

Recommendation:
- Add an option to use label smoothing instead of plain cross entropy.
- Keep the current baseline as the default.
- Make the change available from the training CLI.

Requirements:
- do not break existing checkpoints unless unavoidable
- keep the baseline run command working
- add a smoke test command
```

## Three-step workflow

1. Run `training-log-summarizer` on `history.jsonl`, `history.csv`, and any stdout log.
2. Paste that summary into `experiment-next-step` and get prioritized experiments.
3. Paste the chosen experiment into `experiment-code-updater` and implement the code change.

### End-to-end example

```text
Step 1:
Use $training-log-summarizer at /root/work/cifar10_speedrun_agentic/.agents/skills/training-log-summarizer to summarize:
- /root/work/cifar10_speedrun_agentic/artifacts/baseline_run_001/history.jsonl
- /root/work/cifar10_speedrun_agentic/artifacts/baseline_run_001/history.csv

Step 2:
Use $experiment-next-step at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-next-step to turn that summary into prioritized next experiments.

Step 3:
Use $experiment-code-updater at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-code-updater to implement the top-priority experiment as a minimal, comparable code change.
```


## experiment-loop-runner

### Basic

```text
Use $experiment-loop-runner at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-loop-runner to iterate experiments until a target validation accuracy is reached.

Inputs:
- target validation accuracy: 0.90
- baseline command: ./scripts/run_baselines.sh
- max iterations: 5
- keep runs comparable
- stop early if progress stalls

Return for each iteration:
- Iteration Status
- Summary
- Chosen Next Step
- Code Update
- Next Run Command
```

### CIFAR-10 loop example

```text
Use $experiment-loop-runner at /root/work/cifar10_speedrun_agentic/.agents/skills/experiment-loop-runner to manage the CIFAR-10 improvement loop.

Goal:
- reach validation accuracy >= 0.90

Starting point:
- current codebase in /root/work/cifar10_speedrun_agentic
- baseline run command: ./scripts/run_baselines.sh
- output root: /root/work/cifar10_speedrun_agentic/artifacts

Constraints:
- one main change per iteration
- preserve the baseline path
- stop after 5 iterations if the gain is too small
- use training-log-summarizer, experiment-next-step, and experiment-code-updater in sequence
```
