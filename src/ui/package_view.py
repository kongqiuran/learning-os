import streamlit as st

from src.i18n import t
from src.ui.cards import (
    render_chapter_card,
    render_exam_diagnosis_card,
    render_exam_focus_card,
    render_formula_card,
    render_question_card,
    render_strategy_card,
)


def render_package_view(course, package, document_count, language="zh", st_module=st):
    content = package.content_json if isinstance(package.content_json, dict) else {}
    created_at = getattr(package, "created_at", None)
    generated_time = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "—"

    st_module.subheader(t("exam_diagnosis", language))
    render_exam_diagnosis_card(
        course.name,
        content,
        document_count,
        generated_time,
        language,
        st_module,
    )

    st_module.subheader(t("must_exam_focus", language))
    exam_focus = _as_list(content.get("exam_focus"))
    if exam_focus:
        for item in exam_focus:
            render_exam_focus_card(item, language, st_module)
    else:
        st_module.info(t("no_data", language))

    strategy = content.get("study_strategy") or content.get("exam_strategy") or {}
    st_module.subheader(t("study_route", language))
    render_strategy_card(strategy, language, st_module)

    st_module.subheader(t("formula_quick_reference", language))
    formulas = _as_list(content.get("formula_book"))
    if formulas:
        for item in formulas:
            render_formula_card(item, language, st_module)
    else:
        st_module.info(t("no_data", language))

    st_module.subheader(t("high_frequency_questions", language))
    questions = _as_list(content.get("questions"))
    if questions:
        for index, item in enumerate(questions, start=1):
            render_question_card(item, index, language, st_module)
    else:
        st_module.info(t("no_data", language))

    _render_knowledge_map(content.get("course_map"), language, st_module)

    st_module.subheader(t("chapter_summary", language))
    chapters = _as_list(content.get("chapter_summary"))
    if chapters:
        for item in chapters:
            render_chapter_card(item, language, st_module)
    else:
        st_module.info(t("no_data", language))


def _render_knowledge_map(course_map, language, st_module):
    st_module.subheader(t("course_map", language))
    if course_map:
        with st_module.expander(t("course_map", language), expanded=False):
            if isinstance(course_map, dict):
                for topic, relations in course_map.items():
                    st_module.markdown(f"**{topic}**")
                    _render_plain_items(st_module, relations)
            else:
                st_module.write(course_map)
    else:
        st_module.info(t("no_data", language))


def _as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def _render_plain_items(st_module, values):
    for item in _as_list(values):
        st_module.markdown(f"- {item}")
