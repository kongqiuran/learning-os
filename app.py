import streamlit as st

from src.exporter import build_output_filename, save_markdown
from src.generator import generate_review_pack
from src.loader import extract_text_from_files


st.set_page_config(
    page_title="Learning OS",
    page_icon="LO",
    layout="wide",
)

st.title("Learning OS")
st.caption("Course materials -> AI review pack")

with st.sidebar:
    st.header("Generation settings")
    course_name = st.text_input("Course name", value="Semiconductor Physics")
    output_name = st.text_input("Output filename", value="")
    st.divider()
    st.write("Supported formats: PDF, PPTX, TXT, MD")

uploaded_files = st.file_uploader(
    "Upload course materials",
    type=["pdf", "pptx", "txt", "md"],
    accept_multiple_files=True,
)

generate_button = st.button(
    "Generate review pack",
    type="primary",
    disabled=not uploaded_files,
)

if generate_button:
    with st.status("Processing course materials...", expanded=True) as status:
        st.write("Extracting text")
        try:
            documents = extract_text_from_files(uploaded_files)
        except Exception as exc:
            status.update(label="Text extraction failed", state="error")
            st.error(f"Text extraction failed: {exc}")
            st.stop()

        if not documents:
            status.update(label="No usable text found", state="error")
            st.error("No usable text was extracted. Please try another file.")
            st.stop()

        st.write("Generating review pack")
        try:
            review_pack = generate_review_pack(
                course_name=course_name,
                documents=documents,
            )
        except Exception as exc:
            status.update(label="Review pack generation failed", state="error")
            st.error(f"Review pack generation failed: {exc}")
            st.stop()

        filename = output_name.strip() or build_output_filename(course_name)
        saved_path = save_markdown(review_pack, filename)

        status.update(label="Review pack generated", state="complete")

    download_filename = filename if filename.endswith(".md") else f"{filename}.md"
    st.success(f"Saved to: {saved_path}")
    st.download_button(
        label="Download Markdown review pack",
        data=review_pack,
        file_name=download_filename,
        mime="text/markdown",
    )
    st.markdown(review_pack)
else:
    st.info("Upload one or more course files, then generate a review pack.")
