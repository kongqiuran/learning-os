import streamlit as st

from src.i18n import t


def render_exam_focus_card(item, language="zh", st_module=st):
    data = _as_dict(item, "topic")
    title = data.get("topic") or t("untitled_topic", language)
    importance = _importance_stars(data.get("importance"))
    with st_module.container(border=True):
        st_module.markdown(f"### {title}  {importance}")
        explanation = data.get("core_explanation") or data.get("reason")
        _render_text_section(st_module, t("core_explanation", language), explanation)
        _render_list_section(st_module, t("must_master", language), data.get("must_master"))
        _render_list_section(
            st_module,
            t("formulas_or_rules", language),
            data.get("formulas_or_rules"),
        )
        _render_list_section(st_module, t("question_types", language), data.get("question_types"))
        _render_list_section(st_module, t("common_errors", language), data.get("common_errors"))
        _render_text_section(st_module, t("memory_tips", language), data.get("memory_tips"))
        _render_text_section(st_module, t("study_advice", language), data.get("study_advice"))
        _render_list_section(st_module, t("evidence", language), data.get("evidence"))


def render_formula_card(item, language="zh", st_module=st):
    data = _as_dict(item, "name")
    with st_module.container(border=True):
        st_module.markdown(f"### {data.get('name') or t('unnamed_formula', language)}")
        formula = data.get("formula")
        if formula:
            st_module.code(str(formula), language=None)
        _render_text_section(st_module, t("formula_meaning", language), data.get("meaning"))
        _render_text_section(st_module, t("formula_usage", language), data.get("usage"))
        _render_text_section(st_module, t("formula_variables", language), data.get("variables"))
        _render_text_section(
            st_module,
            t("example_application", language),
            data.get("example_application"),
        )
        _render_text_section(st_module, t("common_error", language), data.get("common_error"))
        _render_text_section(st_module, t("question_type", language), data.get("question_type"))


def render_question_card(item, index, language="zh", st_module=st):
    data = _as_dict(item, "question")
    question_type = data.get("question_type") or t("question", language)
    difficulty = data.get("difficulty") or t("difficulty_unknown", language)
    title = t("question_card_title", language).format(
        index=index,
        question_type=question_type,
        difficulty=difficulty,
    )
    with st_module.container(border=True):
        st_module.markdown(f"### {title}")
        st_module.write(data.get("question") or t("content_unavailable", language))
        knowledge_point = data.get("knowledge_point")
        if knowledge_point:
            st_module.caption(
                t("knowledge_point_value", language).format(value=knowledge_point)
            )
        trap = data.get("common_trap")
        if trap:
            st_module.warning(t("common_trap_value", language).format(value=trap))
        with st_module.expander(t("show_answer", language), expanded=False):
            _render_text_section(st_module, t("answer", language), data.get("answer"))
            _render_text_section(st_module, t("explanation", language), data.get("explanation"))


def render_chapter_card(item, language="zh", st_module=st):
    data = _as_dict(item, "chapter")
    title = data.get("chapter") or t("untitled_chapter", language)
    with st_module.expander(str(title), expanded=False):
        _render_text_section(st_module, t("chapter_overview", language), data.get("summary"))
        _render_list_section(st_module, t("key_concepts", language), data.get("key_concepts"))
        _render_list_section(
            st_module,
            t("important_formulas", language),
            data.get("important_formulas"),
        )
        _render_list_section(
            st_module,
            t("common_question_types", language),
            data.get("common_question_types"),
        )
        _render_text_section(st_module, t("learning_order", language), data.get("learning_order"))
        _render_list_section(
            st_module,
            t("common_mistakes", language),
            data.get("common_mistakes"),
        )


def _as_dict(value, fallback_key):
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {fallback_key: str(value)}


def _as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _importance_stars(value):
    try:
        importance = max(1, min(5, int(value)))
    except (TypeError, ValueError):
        importance = 3
    return "★" * importance + "☆" * (5 - importance)


def _render_text_section(st_module, label, value):
    if value not in (None, ""):
        st_module.markdown(f"**{label}**")
        st_module.write(value)


def _render_list_section(st_module, label, values):
    items = _as_list(values)
    if not items:
        return
    st_module.markdown(f"**{label}**")
    for item in items:
        st_module.markdown(f"- {item}")
