import streamlit as st

from src.exporter import build_output_filename, save_markdown
from src.generator import generate_review_pack
from src.loader import extract_text_from_files


st.set_page_config(
    page_title="Learning OS",
    page_icon="📚",
    layout="wide",
)

st.title("Learning OS")
st.caption("课程资料 -> AI 期末复习包")

with st.sidebar:
    st.header("生成设置")
    course_name = st.text_input("课程名称", value="半导体物理")
    output_name = st.text_input("输出文件名", value="")
    st.divider()
    st.write("支持格式：PDF、PPTX、TXT、MD")

uploaded_files = st.file_uploader(
    "上传课程资料",
    type=["pdf", "pptx", "txt", "md"],
    accept_multiple_files=True,
)

generate_button = st.button("生成复习包", type="primary", disabled=not uploaded_files)

if generate_button:
    with st.status("正在整理课程资料...", expanded=True) as status:
        st.write("正在提取文字")
        documents = extract_text_from_files(uploaded_files)

        if not documents:
            st.error("没有提取到可用文字，请换一份资料试试。")
            st.stop()

        st.write("正在生成复习包")
        review_pack = generate_review_pack(course_name=course_name, documents=documents)

        filename = output_name.strip() or build_output_filename(course_name)
        saved_path = save_markdown(review_pack, filename)

        status.update(label="复习包生成完成", state="complete")

    st.success(f"已生成：{saved_path}")
    st.download_button(
        label="下载 Markdown 复习包",
        data=review_pack,
        file_name=filename,
        mime="text/markdown",
    )
    st.markdown(review_pack)
else:
    st.info("先上传一份或多份课程资料，然后点击生成复习包。")

