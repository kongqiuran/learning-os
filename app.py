import logging

import streamlit as st

from src.auth.session import clear_current_user, get_current_user, set_current_user
from src.database import create_database_tables
from src.exporter import build_output_filename, save_markdown
from src.generator import generate_review_pack
from src.i18n import t
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
from src.ui import render_package_view, run_generation_with_feedback


logger = logging.getLogger(__name__)


st.set_page_config(
    page_title=t("app_title", "zh"),
    page_icon="🎓",
    layout="wide",
)

create_database_tables()


MATERIAL_INBOX = (
    ("TEXTBOOK", "material_textbook", "material_textbook_description", ("pdf",)),
    ("SLIDES", "material_slides", "material_slides_description", ("pdf", "pptx")),
    ("EXAM", "material_exam", "material_exam_description", ("pdf",)),
    ("HOMEWORK", "material_homework", "material_homework_description", ("pdf", "txt")),
    ("NOTES", "material_notes", "material_notes_description", ("pdf", "txt", "md")),
    ("OTHER", "material_other", "material_other_description", ("pdf", "pptx", "txt", "md")),
)


def get_language():
    if "language" not in st.session_state:
        st.session_state.language = "zh"
    return st.session_state.language


def tr(key, **values):
    text = t(key, get_language())
    return text.format(**values) if values else text


def render_language_selector():
    _, language_column = st.columns([8, 2])
    with language_column:
        st.selectbox(
            tr("language"),
            options=["zh", "en"],
            format_func=lambda value: t("chinese" if value == "zh" else "english", value),
            key="language",
            label_visibility="collapsed",
        )


render_language_selector()


def request_package_generation(course_id):
    st.session_state[f"generation_requested_{course_id}"] = True
    st.session_state[f"generation_in_progress_{course_id}"] = True


def save_inbox_uploads(user_id, course_id, pending_uploads):
    saved = {}
    errors = []
    for document_type, allowed_types, uploaded_files in pending_uploads:
        for uploaded_file in uploaded_files or []:
            extension = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
            if extension not in allowed_types:
                errors.append((uploaded_file.name, "unsupported"))
                continue
            try:
                save_uploaded_document(
                    user_id,
                    course_id,
                    uploaded_file,
                    document_type=document_type,
                )
            except DocumentUploadError as exc:
                errors.append((uploaded_file.name, str(exc)))
            else:
                saved.setdefault(document_type, []).append(uploaded_file.name)
    return saved, errors


def render_auth_page():
    st.title(tr("app_title"))
    st.subheader(tr("app_tagline"))

    login_tab, register_tab = st.tabs([tr("login"), tr("register")])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input(tr("email"), key="login_email")
            login_password = st.text_input(tr("password"), type="password", key="login_password")
            login_submitted = st.form_submit_button(tr("login"), type="primary")

        if login_submitted:
            user = authenticate_user(login_email, login_password)
            if user is None:
                st.error(tr("invalid_credentials"))
            else:
                set_current_user(user.id)
                st.rerun()

    with register_tab:
        with st.form("register_form"):
            register_email = st.text_input(tr("email"), key="register_email")
            register_password = st.text_input(tr("password"), type="password", key="register_password")
            confirm_password = st.text_input(tr("confirm_password"), type="password")
            register_submitted = st.form_submit_button(tr("create_account"), type="primary")

        if register_submitted:
            if register_password != confirm_password:
                st.error(tr("password_mismatch"))
            else:
                try:
                    register_user(register_email, register_password)
                except UserAlreadyExistsError:
                    st.error(tr("user_exists"))
                except ValueError as exc:
                    if "Email" in str(exc):
                        st.error(tr("email_required"))
                    else:
                        st.error(tr("password_required"))
                else:
                    st.success(tr("register_success"))


def render_account_sidebar(current_user):
    with st.sidebar:
        st.caption(tr("signed_in_as", email=current_user.email))
        if st.button(tr("sign_out"), use_container_width=True):
            clear_current_user()
            st.session_state.pop("workspace_page", None)
            st.session_state.pop("current_course_id", None)
            st.rerun()


def render_dashboard(current_user):
    st.title(tr("workspace_title"))
    st.write(tr("welcome", email=current_user.email))

    with st.expander(tr("create_course"), expanded=False):
        with st.form("create_course_form", clear_on_submit=True):
            course_name = st.text_input(tr("course_name"), placeholder=tr("course_name_placeholder"))
            course_description = st.text_area(
                tr("course_description"),
                placeholder=tr("course_description_placeholder"),
            )
            create_submitted = st.form_submit_button(tr("create_course"), type="primary")

        if create_submitted:
            try:
                create_course(current_user.id, course_name, course_description)
            except ValueError:
                st.error(tr("course_name_required"))
            else:
                st.success(tr("course_created"))
                st.rerun()

    st.subheader(tr("my_courses"))
    courses = list_courses_for_user(current_user.id)
    if not courses:
        st.info(tr("no_courses"))
        return

    for course in courses:
        with st.container(border=True):
            st.markdown(f"### 📘 {course.name}")
            st.write(course.description or tr("no_description"))
            st.caption(tr("created_at", time=course.created_at.strftime('%Y-%m-%d %H:%M')))

            enter_column, delete_column = st.columns([1, 1])
            if enter_column.button(tr("open_course"), key=f"enter_course_{course.id}", type="primary"):
                st.session_state.current_course_id = course.id
                st.session_state.workspace_page = "course_detail"
                st.rerun()
            if delete_column.button(tr("delete_course"), key=f"delete_course_{course.id}"):
                delete_course_for_user(course.id, current_user.id)
                st.rerun()


def render_course_detail(current_user):
    course_id = st.session_state.get("current_course_id")
    course = get_course_for_user(course_id, current_user.id)
    if course is None:
        st.session_state.workspace_page = "dashboard"
        st.session_state.pop("current_course_id", None)
        st.warning(tr("course_not_found"))
        if st.button(tr("back_to_courses")):
            st.rerun()
        return

    if st.button(tr("back_to_courses")):
        st.session_state.workspace_page = "dashboard"
        st.session_state.pop("current_course_id", None)
        st.rerun()

    st.title(f"📘 {course.name}")
    st.write(course.description or tr("no_description"))
    st.caption(tr("created_at", time=course.created_at.strftime('%Y-%m-%d %H:%M')))

    st.divider()
    st.subheader(tr("course_status"))
    documents = list_documents_for_course(current_user.id, course.id)
    st.metric(tr("documents"), len(documents))
    st.write(tr("knowledge_not_generated"))

    st.divider()
    st.subheader(tr("upload_materials"))
    st.caption(tr("material_inbox_help"))
    pending_uploads = []
    feedback = st.session_state.get(f"upload_feedback_{course.id}", {})
    inbox_columns = st.columns(2)
    for index, (document_type, title_key, description_key, allowed_types) in enumerate(MATERIAL_INBOX):
        with inbox_columns[index % 2].container(border=True):
            st.markdown(f"### {tr(title_key)}")
            st.write(tr(description_key))
            st.caption(tr("supported_formats", formats=", ".join(item.upper() for item in allowed_types)))
            uploaded_files = st.file_uploader(
                tr("drop_files"),
                type=list(allowed_types),
                accept_multiple_files=True,
                key=f"course_upload_{course.id}_{document_type.lower()}",
            )
            pending_uploads.append((document_type, allowed_types, uploaded_files))
            if feedback.get(document_type):
                st.success(tr("saved_category_files", category=tr(title_key)))
                for filename in feedback[document_type]:
                    st.write(f"✓ {filename}")

    has_pending_files = any(uploaded_files for _, _, uploaded_files in pending_uploads)
    if st.button(tr("save_files"), type="primary", disabled=not has_pending_files):
        saved, errors = save_inbox_uploads(current_user.id, course.id, pending_uploads)
        for filename, error in errors:
            if error == "unsupported":
                st.error(f"{filename}: {tr('unsupported_material_format')}")
            else:
                st.error(tr("upload_failed", filename=filename, error=error))
        if saved:
            uploaded_count = sum(len(filenames) for filenames in saved.values())
            st.session_state[f"upload_feedback_{course.id}"] = saved
            st.success(tr("saved_files", count=uploaded_count))
            st.rerun()

    st.divider()
    st.subheader(tr("learning_package"))
    generation_requested_key = f"generation_requested_{course.id}"
    generation_in_progress_key = f"generation_in_progress_{course.id}"
    generation_error_key = f"generation_error_{course.id}"
    generation_in_progress = st.session_state.get(generation_in_progress_key, False)
    if st.session_state.pop(generation_error_key, False):
        st.error(tr("generation_failed_friendly"))
        st.button(
            tr("retry_generation"),
            key=f"retry_generation_{course.id}",
            on_click=request_package_generation,
            args=(course.id,),
        )
    action_column, view_column = st.columns(2)
    action_column.button(
        tr("generate_package"),
        type="primary",
        disabled=not documents or generation_in_progress,
        use_container_width=True,
        key=f"generate_package_{course.id}",
        on_click=request_package_generation,
        args=(course.id,),
    )
    if view_column.button(
        tr("view_package"),
        disabled=get_learning_package(course.id, current_user.id) is None,
        use_container_width=True,
    ):
        st.session_state.workspace_page = "learning_package"
        st.rerun()

    if st.session_state.pop(generation_requested_key, False):
        try:
            run_generation_with_feedback(
                lambda: analyze_course(
                    course.id,
                    current_user.id,
                    language=get_language(),
                ),
                language=get_language(),
            )
        except Exception:
            logger.exception(
                "Learning package generation failed for course_id=%s user_id=%s",
                course.id,
                current_user.id,
            )
            st.session_state[generation_error_key] = True
        else:
            st.session_state.workspace_page = "learning_package"
        finally:
            st.session_state[generation_in_progress_key] = False
        st.rerun()

    st.subheader(tr("course_materials"))
    if not documents:
        st.info(tr("no_materials"))
        return

    for document in documents:
        with st.container(border=True):
            name_column, status_column, action_column = st.columns([4, 2, 1])
            name_column.markdown(f"📄 **{document.original_filename}**")
            name_column.caption(
                f"{format_file_size(document.file_size)} · "
                f"{tr('uploaded_at', time=document.uploaded_at.strftime('%Y-%m-%d %H:%M'))}"
            )
            translated_status = tr(f"status_{document.processing_status}")
            translated_type = tr(f"document_type_{document.document_type.lower()}")
            status_column.write(tr("status", status=translated_status))
            status_column.caption(tr("type", type=translated_type))
            if action_column.button(tr("delete"), key=f"delete_document_{document.id}"):
                delete_document_for_user(document.id, current_user.id, course.id)
                st.rerun()


def render_learning_package(current_user):
    course_id = st.session_state.get("current_course_id")
    course = get_course_for_user(course_id, current_user.id)
    if course is None:
        st.session_state.workspace_page = "dashboard"
        st.rerun()

    if st.button(tr("back_to_course")):
        st.session_state.workspace_page = "course_detail"
        st.rerun()

    st.title(tr("package_title", course=course.name))
    package = get_learning_package(course.id, current_user.id)
    if package is None:
        st.info(tr("no_package"))
        return
    package_status = tr(f"status_{package.status}")
    st.caption(tr("package_version", version=package.version, status=package_status))
    if package.status != "completed":
        st.warning(tr("package_unavailable"))
        return

    document_count = len(list_documents_for_course(current_user.id, course.id))
    render_package_view(
        course,
        package,
        document_count,
        language=get_language(),
    )


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
