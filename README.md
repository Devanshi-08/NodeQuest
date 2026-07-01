# NodeQuest

NodeQuest is an adaptive diagnostic quiz app that identifies concept gaps by walking backward through a prerequisite knowledge graph. Instead of only telling a learner that an answer was wrong, it traces the mistake to the most likely missing foundation and produces a short remediation report.

## Why It Matters

Traditional quizzes often report a score without explaining why a learner struggled. NodeQuest models concepts as dependencies, such as:

```text
Addition -> Multiplication -> Exponents -> Algebra -> Linear Systems
```

If a learner misses a question on an advanced topic, the app dynamically tests prerequisite concepts until it finds the likely boundary between mastered and weak skills.

## Features

- Adaptive prerequisite-based quiz flow
- Knowledge graph visualization with Graphviz
- Real-time diagnostic timer
- Randomized question selection from a diverse question bank
- Skill-level evidence log for every attempt
- Concept-gap report with confidence scoring
- Recommended study actions for the detected gap
- Streamlit interface suitable for demos and portfolio presentation

## Tech Stack

- Python
- Streamlit
- Graphviz

## Project Structure

```text
NodeQuest/
├── main.py        # Streamlit app, quiz engine, report UI, graph rendering
├── topics.py      # Knowledge graph, topic metadata, question bank
├── README.md
├── requirements.txt
└── .gitignore
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Devanshi-08/NodeQuest.git
cd NodeQuest
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python -m streamlit run main.py
```

## How It Works

1. The learner chooses a target concept.
2. NodeQuest asks a question from that concept.
3. If the learner answers correctly, the app marks the concept as mastered.
4. If the learner answers incorrectly, the app moves to the prerequisite concept.
5. The final report identifies the most likely concept gap and suggests what to review next.

## Future Improvements

- Add teacher dashboards for class-level analytics
- Store learner sessions in a database
- Add generated practice sets for weak concepts
- Support multiple subjects and configurable curriculum graphs
- Export reports as PDF or CSV

## License

This project is intended for educational and portfolio use.
