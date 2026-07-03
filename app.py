import streamlit as st

from src.exporter import build_output_filename, save_markdown
from src.generator import generate_review_pack
from src.loader import extract_text_from_files


st.set_page_config(
    page_title="ExamPilot",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 ExamPilot")
st.subheader("48小时生成你的期末冲刺包")
st.write(
    "上传老师 PPT、PDF、讲义、作业，自动生成考点总结、公式表、题型分类、"
    "易错点、模拟卷和 7 天复习计划。"
)

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

generate_button = st.button(
    "生成期末冲刺包",
    type="primary",
    disabled=not uploaded_files,
)

if generate_button:
    with st.status("正在整理课程资料...", expanded=True) as status:
        st.write("正在提取文字")
        try:
            documents = extract_text_from_files(uploaded_files)
        except Exception as exc:
            status.update(label="资料读取失败", state="error")
            st.error(f"资料读取失败：{exc}")
            st.stop()

        if not documents:
            status.update(label="没有可用文字", state="error")
            st.error("没有提取到可用文字，请换一份资料试试。")
            st.stop()

        st.write("正在生成期末冲刺包")
        try:
            review_pack = generate_review_pack(
                course_name=course_name,
                documents=documents,
            )
        except Exception as exc:
            status.update(label="生成失败", state="error")
            st.error(f"生成失败：{exc}")
            st.stop()

        filename = output_name.strip() or build_output_filename(course_name)
        saved_path = save_markdown(review_pack, filename)

        status.update(label="期末冲刺包生成完成", state="complete")

    download_filename = filename if filename.endswith(".md") else f"{filename}.md"
    st.success(f"已保存到：{saved_path}")
    st.download_button(
        label="下载 Markdown 期末冲刺包",
        data=review_pack,
        file_name=download_filename,
        mime="text/markdown",
    )
    st.markdown(review_pack)
else:
    st.info("先上传一份或多份课程资料，然后点击生成期末冲刺包。")
