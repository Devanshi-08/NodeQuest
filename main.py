"""NodeQuest: adaptive concept-gap analysis for small prerequisite graphs."""

from __future__ import annotations

import random
import time

import graphviz
import streamlit as st

from topics import KNOWLEDGE_GRAPH, QUESTION_BANK, TOPICS, topic_order


APP_TITLE = "NodeQuest"
DEFAULT_TARGET = "Linear Systems"
STATUS_UNVISITED = "unvisited"
STATUS_CURRENT = "current"
STATUS_MASTERED = "mastered"
STATUS_REVIEW = "needs_review"


st.set_page_config(page_title=APP_TITLE, page_icon="NQ", layout="wide")


st.markdown(
    """
    <style>
    :root {
        --nq-blue: #2563eb;
        --nq-ink: #111827;
        --nq-muted: #6b7280;
        --nq-border: #d1d5db;
        --nq-surface: #f8fafc;
    }

    .nq-title {
        font-size: 2.5rem;
        font-weight: 760;
        color: var(--nq-ink);
        letter-spacing: 0;
        margin: 0 0 0.15rem 0;
    }

    .nq-subtitle {
        color: var(--nq-muted);
        font-size: 1.05rem;
        margin-bottom: 1.25rem;
    }

    .nq-pill {
        display: inline-block;
        border: 1px solid var(--nq-border);
        border-radius: 999px;
        padding: 0.22rem 0.65rem;
        margin: 0 0.35rem 0.35rem 0;
        color: #374151;
        background: white;
        font-size: 0.86rem;
    }

    .nq-callout {
        border-left: 4px solid var(--nq-blue);
        background: var(--nq-surface);
        padding: 0.85rem 1rem;
        border-radius: 0.4rem;
        color: #1f2937;
    }

    [data-testid="stMetricValue"] {
        color: var(--nq-ink);
        font-size: 1.55rem !important;
        font-weight: 720 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    defaults = {
        "target_topic": DEFAULT_TARGET,
        "current_topic": DEFAULT_TARGET,
        "history": {},
        "attempt_log": [],
        "seen_questions": {},
        "active_question": None,
        "start_time": time.time(),
        "quiz_complete": False,
        "diagnosis": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state.active_question is None:
        st.session_state.active_question = choose_question(st.session_state.current_topic)


def reset_quiz(target_topic: str) -> None:
    st.session_state.target_topic = target_topic
    st.session_state.current_topic = target_topic
    st.session_state.history = {}
    st.session_state.attempt_log = []
    st.session_state.seen_questions = {}
    st.session_state.active_question = choose_question(target_topic)
    st.session_state.start_time = time.time()
    st.session_state.quiz_complete = False
    st.session_state.diagnosis = None


def choose_question(topic: str) -> dict:
    seen = st.session_state.get("seen_questions", {}).setdefault(topic, set())
    candidates = [q for q in QUESTION_BANK[topic] if q["id"] not in seen]

    if not candidates:
        seen.clear()
        candidates = QUESTION_BANK[topic]

    question = random.choice(candidates)
    seen.add(question["id"])
    return question


def dependency_path(topic: str) -> list[str]:
    path = [topic]
    parent = KNOWLEDGE_GRAPH[topic]

    while parent:
        path.append(parent)
        parent = KNOWLEDGE_GRAPH[parent]

    return path


def downstream_topics(topic: str) -> list[str]:
    children = [
        candidate
        for candidate, parent in KNOWLEDGE_GRAPH.items()
        if parent == topic
    ]
    results = []

    for child in children:
        results.append(child)
        results.extend(downstream_topics(child))

    return results


def status_for(topic: str) -> str:
    if not st.session_state.quiz_complete and topic == st.session_state.current_topic:
        return STATUS_CURRENT

    return st.session_state.history.get(topic, {}).get("status", STATUS_UNVISITED)


def record_attempt(topic: str, question: dict, selected_choice: str, is_correct: bool) -> None:
    topic_state = st.session_state.history.setdefault(
        topic,
        {
            "attempts": 0,
            "correct": 0,
            "status": STATUS_UNVISITED,
            "skills": set(),
            "misconceptions": [],
            "last_explanation": "",
        },
    )

    topic_state["attempts"] += 1
    topic_state["correct"] += int(is_correct)
    topic_state["status"] = STATUS_MASTERED if is_correct else STATUS_REVIEW
    topic_state["skills"].add(question["skill"])
    topic_state["last_explanation"] = question["explanation"]

    if not is_correct:
        topic_state["misconceptions"].append(question["misconception"])

    st.session_state.attempt_log.append(
        {
            "topic": topic,
            "skill": question["skill"],
            "question": question["question"],
            "selected": selected_choice,
            "correct_answer": question["choices"][question["correct"]],
            "is_correct": is_correct,
            "explanation": question["explanation"],
        }
    )


def build_diagnosis() -> dict:
    path = dependency_path(st.session_state.target_topic)
    failed_topics = [
        topic
        for topic in path
        if st.session_state.history.get(topic, {}).get("status") == STATUS_REVIEW
    ]
    mastered_topics = [
        topic
        for topic in path
        if st.session_state.history.get(topic, {}).get("status") == STATUS_MASTERED
    ]

    if not failed_topics:
        gap_topic = None
        confidence = 92
        summary = "No gap detected on this diagnostic path."
    else:
        gap_topic = failed_topics[-1]
        supporting_mastery = len(mastered_topics)
        confidence = min(95, 62 + 9 * len(failed_topics) + 5 * supporting_mastery)
        summary = f"The most likely concept gap is {gap_topic}."

    return {
        "gap_topic": gap_topic,
        "confidence": confidence,
        "summary": summary,
        "path": path,
        "failed_topics": failed_topics,
        "mastered_topics": mastered_topics,
        "affected_topics": downstream_topics(gap_topic) if gap_topic else [],
    }


def evaluate_answer(selected_choice: str) -> None:
    topic = st.session_state.current_topic
    question = st.session_state.active_question
    is_correct = question["choices"].index(selected_choice) == question["correct"]

    record_attempt(topic, question, selected_choice, is_correct)

    if is_correct:
        st.session_state.diagnosis = build_diagnosis()
        st.session_state.quiz_complete = True
        return

    prerequisite = KNOWLEDGE_GRAPH[topic]
    if prerequisite is None:
        st.session_state.diagnosis = build_diagnosis()
        st.session_state.quiz_complete = True
        return

    st.session_state.current_topic = prerequisite
    st.session_state.active_question = choose_question(prerequisite)


@st.fragment(run_every="1s")
def render_timer() -> None:
    elapsed = int(time.time() - st.session_state.start_time)
    mins, secs = divmod(elapsed, 60)
    st.metric("Time", f"{mins:02d}:{secs:02d}")


def render_graph() -> graphviz.Digraph:
    dot = graphviz.Digraph("nodequest_map")
    dot.attr(rankdir="BT", bgcolor="transparent", splines="ortho", nodesep="0.45", ranksep="0.55")
    dot.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="10")
    dot.attr("edge", color="#9ca3af", arrowsize="0.75")

    colors = {
        STATUS_CURRENT: ("#eff6ff", "#2563eb", "#1d4ed8"),
        STATUS_MASTERED: ("#ecfdf5", "#10b981", "#047857"),
        STATUS_REVIEW: ("#fef2f2", "#ef4444", "#b91c1c"),
        STATUS_UNVISITED: ("#ffffff", "#d1d5db", "#6b7280"),
    }
    labels = {
        STATUS_CURRENT: "Testing now",
        STATUS_MASTERED: "Mastered",
        STATUS_REVIEW: "Needs review",
        STATUS_UNVISITED: "Not tested",
    }

    for topic in topic_order():
        status = status_for(topic)
        fill, border, font = colors[status]
        dot.node(
            topic,
            f"{topic}\\n{labels[status]}",
            fillcolor=fill,
            color=border,
            fontcolor=font,
            penwidth="2" if status in {STATUS_CURRENT, STATUS_REVIEW} else "1.2",
        )

    for child, parent in KNOWLEDGE_GRAPH.items():
        if parent:
            child_status = status_for(child)
            dot.edge(
                parent,
                child,
                color="#ef4444" if child_status == STATUS_REVIEW else "#9ca3af",
                penwidth="2" if child_status == STATUS_REVIEW else "1.2",
            )

    return dot


def render_topic_pills(topic: str) -> None:
    details = TOPICS[topic]
    path = dependency_path(topic)
    chips = [
        f"Level: {details['level']}",
        f"Diagnostic path: {len(path)} concepts",
        f"Question pool: {sum(len(QUESTION_BANK[node]) for node in path)} items",
    ]
    st.markdown(
        "".join(f'<span class="nq-pill">{chip}</span>' for chip in chips),
        unsafe_allow_html=True,
    )


def render_quiz() -> None:
    topic = st.session_state.current_topic
    question = st.session_state.active_question
    details = TOPICS[topic]

    st.markdown(f"#### Current concept: {topic}")
    render_topic_pills(topic)
    st.caption(details["description"])

    with st.container(border=True):
        st.markdown(f"**Skill being tested:** {question['skill']}")
        st.markdown(f"### {question['question']}")

    form_key = f"quiz_form_{question['id']}_{len(st.session_state.attempt_log)}"
    with st.form(form_key, clear_on_submit=False):
        selected = st.radio("Select one answer", question["choices"])
        submitted = st.form_submit_button("Submit answer", use_container_width=True)

    if submitted:
        evaluate_answer(selected)
        st.rerun()


def render_report() -> None:
    diagnosis = st.session_state.diagnosis or build_diagnosis()
    gap_topic = diagnosis["gap_topic"]

    st.markdown("### Diagnostic report")

    if gap_topic is None:
        st.success("No concept gap detected on the selected path. The learner is ready for the target topic.")
    else:
        st.error(f"Primary focus area: {gap_topic}")
        st.markdown(
            f"""
            <div class="nq-callout">
            {diagnosis["summary"]} NodeQuest found this by walking backward through the prerequisite chain
            until it reached the learner's strongest demonstrated foundation.
            </div>
            """,
            unsafe_allow_html=True,
        )

    metric_cols = st.columns(3)
    metric_cols[0].metric("Confidence", f"{diagnosis['confidence']}%")
    metric_cols[1].metric("Concepts tested", len(st.session_state.history))
    metric_cols[2].metric("Attempts", len(st.session_state.attempt_log))

    if gap_topic:
        st.markdown("#### Recommended intervention")
        for action in TOPICS[gap_topic]["study_actions"]:
            st.write(f"- {action}")

        if diagnosis["affected_topics"]:
            st.markdown("#### Downstream concepts at risk")
            st.write(", ".join(diagnosis["affected_topics"]))

    st.markdown("#### Evidence log")
    for attempt in st.session_state.attempt_log:
        result = "Correct" if attempt["is_correct"] else "Needs review"
        with st.expander(f"{attempt['topic']} - {attempt['skill']} - {result}"):
            st.write(f"Question: {attempt['question']}")
            st.write(f"Selected answer: {attempt['selected']}")
            st.write(f"Correct answer: {attempt['correct_answer']}")
            st.info(attempt["explanation"])

    col_a, col_b = st.columns(2)
    if col_a.button("Run a new diagnostic", use_container_width=True):
        reset_quiz(st.session_state.target_topic)
        st.rerun()
    if col_b.button("Practice the focus area", use_container_width=True, disabled=gap_topic is None):
        reset_quiz(gap_topic)
        st.rerun()


initialize_state()


with st.sidebar:
    st.markdown("## NodeQuest")
    st.caption("Adaptive concept-gap diagnostics for prerequisite-based learning.")

    selected_target = st.selectbox(
        "Target concept",
        list(TOPICS.keys()),
        index=list(TOPICS.keys()).index(st.session_state.target_topic),
    )

    if selected_target != st.session_state.target_topic:
        reset_quiz(selected_target)
        st.rerun()

    st.divider()
    render_timer()
    st.metric("Questions answered", len(st.session_state.attempt_log))
    st.metric("Concepts touched", len(st.session_state.history))

    st.divider()
    st.markdown("#### Diagnostic path")
    for node in dependency_path(st.session_state.target_topic):
        prefix = "Now" if node == st.session_state.current_topic and not st.session_state.quiz_complete else "-"
        st.write(f"{prefix} {node}")

    st.divider()
    if st.button("Restart diagnostic", use_container_width=True):
        reset_quiz(st.session_state.target_topic)
        st.rerun()


left_column, right_column = st.columns([1.15, 1.0], gap="large")

with left_column:
    st.markdown('<p class="nq-title">NodeQuest</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nq-subtitle">An adaptive quiz engine that traces missed answers back to prerequisite concepts.</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.quiz_complete:
        render_report()
    else:
        render_quiz()


with right_column:
    st.markdown("### Learning map")
    st.caption("The graph shows the target topic, prerequisites, and evidence collected during this diagnostic.")
    with st.container(border=True):
        st.graphviz_chart(render_graph(), use_container_width=True)

    with st.container(border=True):
        st.markdown("#### Model notes")
        st.write("A wrong answer sends the learner to the prerequisite concept.")
        st.write("A correct answer after one or more misses marks the likely boundary of the concept gap.")
        st.write("The report combines the path, answer evidence, and remediation guidance.")
