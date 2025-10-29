<div align=center><h1>
    📐 AMO-Bench: Large Language Models Still<br>
    Struggle in High School Math Competitions
</h1></div>

<p align="center">
  📃 <a href="xxx" target="_blank">Paper</a > • 🌐 <a href="xxx" target="_blank">Homepage</a > • 🤗 <a href="xxx" target="_blank">Dataset</a ><br>
</p >

This is the official repo for the paper **AMO-Bench: Large Language Models Still Struggle in High School Math Competitions**.

<p align="center">
    <img src="./figures/cover_fig.png" width="800">
    <br>
</p>


## 📖 Abstract

We present **AMO-Bench**, an **A**dvanced **M**athematical reasoning benchmark with **O**lympiad
level or even higher difficulty, comprising 50 human-crafted problems.
Existing benchmarks have widely leveraged high school math competitions for evaluating mathematical
reasoning capabilities of large language models (LLMs).
However, many existing math competitions are becoming less effective for assessing top-tier LLMs due to performance saturation (e.g., AIME24/25).
To address this, AMO-Bench introduces more rigorous challenges by ensuring all 50 problems are (1) cross-validated by experts to meet at least the International Mathematical Olympiad (IMO) difficulty standards, and (2) entirely original problems to prevent potential performance leakages from data memorization.
Moreover, each problem in AMO-Bench requires only a final answer rather than a proof, enabling automatic and robust grading for evaluation.

## ⭐ Key Features

<p align="center">
    <img src="./figures/pipeline.png" width="800">
    <br>
</p>

- **Original problems.** To prevent performance leaks from existing resources as much as possible,
all problems in AMO-Bench are newly crafted by human experts. Moreover, we conduct a
secondary verification to ensure that there are no highly similar problems in existing competitions
or online resources.
- **Guaranteed difficulty.** Each problem has undergone rigorous cross-validation by multiple
experts to ensure it meets at least the difficulty standards of IMO. We also incorporate an
LLM-based difficulty filtering stage to exclude questions that do not present sufficient challenge
to current reasoning models.
- **Final-answer based grading.** Each problem in AMO-Bench requires a final answer rather than
a full proof, enabling efficient automatic grading. For each problem, we employ a parser-based
or LLM-based grading method according to its answer type, balancing the grading cost and
generalizability.
- **Human-annotated reasoning paths.** In addition to the final answer, each problem also includes
a detailed reasoning path written by human experts. These additional annotations enhance
solution transparency and could support further explorations on AMO-Bench, such as prompt
engineering and error analysis.

## 📊 Leaderboard

<p align="center">
    <img src="./figures/leaderboard.png" width="800">
    <br>
</p>

Experimental results across 26 LLMs on
AMO-Bench show that even the best-performing model achieves only 52.4% accuracy on
AMO-Bench, with most LLMs scoring below 40%. 

## 🛠️ Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/meituan-longcat/AMO-Bench.git
cd AMO-Bench
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running evaluations

#### Step 1: Format Model Response File

After obtaining model responses, format them as follows (one JSON object per line):
```data
{"question_id": 1, "model_response": "..."}
{"question_id": 2, "model_response": "..."}
...
```
Save this file in the `./model_responses/` directory.

#### Step 2: Grading Responses
Set your API key and URL in lines 13-14 of `utils.py`.
Then run:
```bash
python grading.py --response_file example.jsonl
```
Evaluation results will be saved under the  `./grading_results/` directory.

### Step 3 (Optional): Grade on AMO-Bench-P Subset

For a quick evaluation using only the parser-based subset (39 problems), run:
```bash
python grading.py --response_file example.jsonl --only_parser True
```


## 🔎 Citation

If you find our work helpful or relevant to your research, please kindly cite our paper:

```
xxx
```

## 🤗 Acknowledgement

The evaluation script utilizes [Math-Verify](https://github.com/huggingface/Math-Verify) to parse and verify model outputs.
We greatly appreciate the contributors' efforts in providing this valuable tool.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 📪 Support

For questions and support, please open an issue on GitHub or contact the maintainers.