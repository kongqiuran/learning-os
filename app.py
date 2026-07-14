import streamlit as st

from src.auth.session import clear_current_user, get_current_user, set_current_user
from src.database import create_database_tables
from src.exporter import build_output_filename, save_markdown
from src.generator import generate_review_pack
from src.loader import extract_text_from_files
from src.services.course_service import (
    create_course,
    delete_course_for_user,
    get_course_for_user,
    list_courses_for_user,
)
from src.services.analysis_service import analyze_course, get_learning_package
from src.services.document_service import (
    DocumentUploadError,
    delete_document_for_user,
    list_documents_for_course,
    save_uploaded_document,
)
from src.services.user_service import (
    UserAlreadyExistsError,
    authenticate_user,
    register_user,
)


st.set_page_config(
    page_title="Learning OS",
    page_icon="🎓",
    layout="wide",
)

create_database_tables()


def render_auth_page():
    st.title("🎓 Learning OS")
    st.subheader("把课程资料整理成结构化知识体系")

    login_tab, register_tab = st.tabs(["登录", "注册"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("邮箱", key="login_email")
            login_password = st.text_input("密码", type="password", key="login_password")
            login_submitted = st.form_submit_button("登录", type="primary")

        if login_submitted:
            user = authenticate_user(login_email, login_password)
            if user is None:
                st.error("邮箱或密码错误。")
            else:
                set_current_user(user.id)
                st.rerun()

    with register_tab:
        with st.form("register_form"):
            register_email = st.text_input("邮箱", key="register_email")
            register_password = st.text_input("密码", type="password", key="register_password")
            confirm_password = st.text_input("确认密码", type="password")
            register_submitted = st.form_submit_button("创建账号", type="primary")

        if register_submitted:
            if register_password != confirm_password:
                st.error("两次输入的密码不一致。")
            else:
                try:
                    register_user(register_email, register_password)
                except UserAlreadyExistsError:
                    st.error("该邮箱已经注册。")
                except ValueError as exc:
                    if "Email" in str(exc):
                        st.error("邮箱不能为空。")
                    else:
                        st.error("密码不能为空。")
                else:
                    st.success("注册成功，请切换到登录页登录。")


def render_account_sidebar(current_user):
    with st.sidebar:
        st.caption(f"Signed in as: {current_user.email}")
        if st.button("Sign out", use_container_width=True):
            clear_current_user()
            st.session_state.pop("workspace_page", None)
            st.session_state.pop("current_course_id", None)
            st.rerun()


def render_dashboard(current_user):
    st.title("🎓 My Learning Workspace")
    st.write(f"Welcome, {current_user.email}")

    with st.expander("＋ Create course", expanded=False):
        with st.form("create_course_form", clear_on_submit=True):
            course_name = st.text_input("Course name", placeholder="Signal and Systems")
            course_description = st.text_area(
                "Course description (optional)",
                placeholder="Microelectronics major course",
            )
            create_submitted = st.form_submit_button("Create course", type="primary")

        if create_submitted:
            try:
                create_course(current_user.id, course_name, course_description)
            except ValueError:
                st.error("Course name is required.")
            else:
                st.success("Course created.")
                st.rerun()

    st.subheader("My courses")
    courses = list_courses_for_user(current_user.id)
    if not courses:
        st.info("No courses yet. Create your first learning workspace.")
        return

    for course in courses:
        with st.container(border=True):
            st.markdown(f"### 📘 {course.name}")
            st.write(course.description or "No course description")
            st.caption(f"Created: {course.created_at.strftime('%Y-%m-%d %H:%M')}")

            enter_column, delete_column = st.columns([1, 1])
            if enter_column.button("Open course", key=f"enter_course_{course.id}", type="primary"):
                st.session_state.current_course_id = course.id
                st.session_state.workspace_page = "course_detail"
                st.rerun()
            if delete_column.button("Delete course", key=f"delete_course_{course.id}"):
                delete_course_for_user(course.id, current_user.id)
                st.rerun()


def render_course_detail(current_user):
    course_id = st.session_state.get("current_course_id")
    course = get_course_for_user(course_id, current_user.id)
    if course is None:
        st.session_state.workspace_page = "dashboard"
        st.session_state.pop("current_course_id", None)
        st.warning("The course does not exist or you do not have access.")
        if st.button("Back to my courses"):
            st.rerun()
        return

    if st.button("← Back to my courses"):
        st.session_state.workspace_page = "dashboard"
        st.session_state.pop("current_course_id", None)
        st.rerun()

    st.title(f"📘 {course.name}")
    st.write(course.description or "No course description")
    st.caption(f"Created: {course.created_at.strftime('%Y-%m-%d %H:%M')}")

    st.divider()
    st.subheader("Course status")
    documents = list_documents_for_course(current_user.id, course.id)
    st.metric("Documents", len(documents))
    st.write("Knowledge structure: not generated")

    st.divider()
    st.subheader("Upload course materials")
    uploaded_files = st.file_uploader(
        "Choose PDF, PPTX, TXT, or Markdown files",
        type=["pdf", "pptx", "txt", "md"],
        accept_multiple_files=True,
        key=f"course_upload_{course.id}",
    )
    document_type = st.selectbox(
        "Material type",
        ["TEXTBOOK", "SLIDES", "EXAM", "HOMEWORK", "NOTES", "OTHER"],
        index=5,
        key=f"document_type_{course.id}",
    )
    if st.button("Save uploaded files", type="primary", disabled=not uploaded_files):
        uploaded_count = 0
        for uploaded_file in uploaded_files:
            try:
                save_uploaded_document(
                    current_user.id,
                    course.id,
                    uploaded_file,
                    document_type=document_type,
                )
            except DocumentUploadError as exc:
                st.error(f"{uploaded_file.name}: {exc}")
            else:
                uploaded_count += 1
        if uploaded_count:
            st.success(f"Saved {uploaded_count} file(s).")
            st.rerun()

    st.divider()
    st.subheader("AI learning package")
    action_column, view_column = st.columns(2)
    if action_column.button(
        "Generate AI learning package",
        type="primary",
        disabled=not documents,
        use_container_width=True,
    ):
        with st.spinner("Analyzing course materials..."):
            try:
                analyze_course(course.id, current_user.id)
            except Exception as exc:
                st.error(f"Learning package generation failed: {exc}")
            else:
                st.success("Learning package generated.")
                st.session_state.workspace_page = "learning_package"
                st.rerun()
    if view_column.button(
        "View latest learning package",
        disabled=get_learning_package(course.id, current_user.id) is None,
        use_container_width=True,
    ):
        st.session_state.workspace_page = "learning_package"
        st.rerun()

    st.subheader("Course materials")
    if not documents:
        st.info("No course materials uploaded yet.")
        return

    for document in documents:
        with st.container(border=True):
            name_column, status_column, action_column = st.columns([4, 2, 1])
            name_column.markdown(f"📄 **{document.original_filename}**")
            name_column.caption(
                f"{format_file_size(document.file_size)} · "
                f"Uploaded {document.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
            )
            status_column.write(f"Status: `{document.processing_status}`")
            status_column.caption(f"Type: {document.document_type}")
            if action_column.button("Delete", key=f"delete_document_{document.id}"):
                delete_document_for_user(document.id, current_user.id, course.id)
                st.rerun()


def render_learning_package(current_user):
    course_id = st.session_state.get("current_course_id")
    course = get_course_for_user(course_id, current_user.id)
    if course is None:
        st.session_state.workspace_page = "dashboard"
        st.rerun()

    if st.button("Back to course"):
        st.session_state.workspace_page = "course_detail"
        st.rerun()

    st.title(f"{course.name} · Learning Package")
    package = get_learning_package(course.id, current_user.id)
    if package is None:
        st.info("No learning package has been generated yet.")
        return
    st.caption(f"Version {package.version} · Status: {package.status}")
    if package.status != "completed":
        st.warning("The latest learning package is not available.")
        return

    content = package.content_json or {}
    sections = [
        ("Course Knowledge Map", "course_map"),
        ("Chapter Summary", "chapter_summary"),
        ("Key Points", "key_points"),
        ("Formula Book", "formula_book"),
        ("Exam Focus", "exam_focus"),
        ("Practice Questions", "questions"),
    ]
    for title, key in sections:
        st.subheader(title)
        value = content.get(key, {} if key == "course_map" else [])
        if value:
            st.json(value, expanded=True)
        else:
            st.caption("No content generated for this section.")


def format_file_size(file_size):
    if file_size < 1024:
        return f"{file_size} B"
    if file_size < 1024 * 1024:
        return f"{file_size / 1024:.1f} KB"
    return f"{file_size / (1024 * 1024):.1f} MB"


current_user = get_current_user()
if current_user is None:
    render_auth_page()
    st.stop()

render_account_sidebar(current_user)
workspace_page = st.session_state.get("workspace_page", "dashboard")
if workspace_page == "course_detail":
    render_course_detail(current_user)
elif workspace_page == "learning_package":
    render_learning_package(current_user)
else:
    render_dashboard(current_user)
st.stop()

st.title("🎓 ExamPilot")
st.subheader("48小时生成你的期末冲刺包")
st.write(
    "上传老师 PPT、PDF、讲义、作业，自动生成考点总结、公式表、题型分类、"
    "易错点、模拟卷和 7 天复习计划。"
)

with st.sidebar:
    st.caption(f"当前用户：{current_user.email}")
    if st.button("退出登录", use_container_width=True):
        clear_current_user()
        st.rerun()
    st.divider()
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
