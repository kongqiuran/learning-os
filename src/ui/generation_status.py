import streamlit as st

from src.i18n import t


def run_generation_with_feedback(generate, language="zh", st_module=st):
    with st_module.status(
        t("generation_status_title", language),
        expanded=True,
    ) as status:
        st_module.info(t("generation_time_hint", language))
        status.write(f"📂 {t('generation_stage_reading', language)}")
        status.caption(t("generation_stage_reading_help", language))
        status.update(label=t("generation_stage_analysis", language), state="running")
        status.write(f"🧠 {t('generation_stage_analysis', language)}")
        status.caption(t("generation_stage_analysis_help", language))
        status.write(f"🔥 {t('generation_stage_content', language)}")
        status.caption(t("generation_stage_content_help", language))

        try:
            result = generate()
        except Exception:
            status.update(
                label=t("generation_failed_friendly", language),
                state="error",
                expanded=True,
            )
            raise

        status.update(label=t("generation_stage_packaging", language), state="running")
        status.write(f"📚 {t('generation_stage_packaging', language)}")
        status.caption(t("generation_stage_packaging_help", language))
        status.update(
            label=t("generation_complete", language),
            state="complete",
            expanded=False,
        )
        return result
