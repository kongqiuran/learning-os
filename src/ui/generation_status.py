import time

import streamlit as st

from src.i18n import t


def run_generation_with_feedback(
    generate,
    language="zh",
    st_module=st,
    completion_delay=3,
    sleep_func=time.sleep,
):
    with st_module.status(
        t("generation_status_title", language),
        expanded=True,
    ) as status:
        st_module.info(t("generation_time_hint", language))
        status.write(f"✅ {t('generation_stage_reading', language)}")
        status.caption(t("generation_stage_reading_help", language))
        status.update(
            label=t("generation_stage_analysis", language),
            state="running",
            expanded=True,
        )
        status.write(f"🔄 {t('generation_stage_analysis', language)}")
        status.caption(t("generation_stage_analysis_help", language))
        status.write(f"⬜ {t('generation_stage_content', language)}")
        status.caption(t("generation_stage_content_help", language))
        status.write(f"⬜ {t('generation_stage_packaging', language)}")
        status.caption(t("generation_stage_packaging_help", language))

        try:
            result = generate()
        except Exception:
            status.update(
                label=t("generation_failed_status", language),
                state="error",
                expanded=True,
            )
            raise

        status.write(f"✅ {t('generation_stage_analysis', language)}")
        status.write(f"✅ {t('generation_stage_content', language)}")
        status.write(f"✅ {t('generation_stage_packaging', language)}")
        status.update(
            label=t("generation_complete", language),
            state="complete",
            expanded=True,
        )
        sleep_func(completion_delay)
        return result
