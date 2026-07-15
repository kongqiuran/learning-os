import streamlit as st

from src.i18n import t
from src.ui.cards import (
    render_chapter_card,
    render_exam_focus_card,
    render_formula_card,
    render_question_card,
)


def render_package_view(course, package, document_count, language="zh", st_module=st):
    content = package.content_json if isinstance(package.content_json, dict) else {}
    created_at = getattr(package, "created_at", None)
    generated_time = created_at.strftime("%Y-%m-%d %H:%M") if created_at else "—"

    with st_module.container(border=True):
        st_module.markdown(f"## 🎓 {course.name}")
        columns = st_module.columns(3)
        columns[0].metric(t("course_name", language), course.name)
        columns[1].metric(t("documents", language), document_count)
        columns[2].metric(t("generated_at", language), generated_time)

    strategy = content.get("study_strategy") or content.get("exam_strategy") or {}
    st_module.subheader(t("study_route", language))
    _render_strategy(strategy, language, st_module)

    _render_simple_overview(content, language, st_module)

    st_module.subheader(t("exam_focus", language))
    exam_focus = _as_list(content.get("exam_focus"))
    if exam_focus:
        for item in exam_focus:
            render_exam_focus_card(item, language, st_module)
    else:
        st_module.info(t("empty_section", language))

    st_module.subheader(t("formula_book", language))
    formulas = _as_list(content.get("formula_book"))
    if formulas:
        for item in formulas:
            render_formula_card(item, language, st_module)
    else:
        st_module.info(t("empty_section", language))

    st_module.subheader(t("chapter_summary", language))
    chapters = _as_list(content.get("chapter_summary"))
    if chapters:
        for item in chapters:
            render_chapter_card(item, language, st_module)
    else:
        st_module.info(t("empty_section", language))

    st_module.subheader(t("practice_questions", language))
    questions = _as_list(content.get("questions"))
    if questions:
        for index, item in enumerate(questions, start=1):
            render_question_card(item, index, language, st_module)
    else:
        st_module.info(t("empty_section", language))


def _render_strategy(strategy, language, st_module):
    data = strategy if isinstance(strategy, dict) else {}
    with st_module.container(border=True):
        _render_bullets(st_module, t("priority_order", language), data.get("priority_order"))
        _render_bullets(
            st_module,
            t("before_exam_focus", language),
            data.get("before_exam_focus"),
        )
        _render_bullets(
            st_module,
            t("avoid_wasting_time", language),
            data.get("avoid_wasting_time"),
        )
        schedule = data.get("recommended_schedule") or data.get("study_advice")
        if schedule:
            st_module.markdown(f"**{t('recommended_schedule', language)}**")
            st_module.write(schedule)
        if not data:
            st_module.caption(t("empty_section", language))


def _render_simple_overview(content, language, st_module):
    course_map = content.get("course_map")
    key_points = _as_list(content.get("key_points"))
    if course_map:
        with st_module.expander(t("course_map", language), expanded=False):
            if isinstance(course_map, dict):
                for topic, relations in course_map.items():
                    st_module.markdown(f"**{topic}**")
                    _render_plain_items(st_module, relations)
            else:
                st_module.write(course_map)
    if key_points:
        with st_module.expander(t("key_points", language), expanded=False):
            _render_plain_items(st_module, key_points)


def _as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def _render_bullets(st_module, title, values):
    items = _as_list(values)
    if not items:
        return
    st_module.markdown(f"**{title}**")
    _render_plain_items(st_module, items)


def _render_plain_items(st_module, values):
    for item in _as_list(values):
        st_module.markdown(f"- {item}")
