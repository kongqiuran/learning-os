# Learning OS Step11-4 上传体验优化报告

## 1. 实现结果

课程资料区新增四个直接可见的分类入口：

| 用户入口 | document_type | 说明 |
|---|---|---|
| 上传教材 | TEXTBOOK | 教材、参考书或章节讲义 |
| 上传课件 | SLIDES | 老师 PPT 或课堂幻灯片 |
| 上传笔记 | NOTES | 课堂笔记或复习笔记 |
| 上传试卷 | EXAM | 历年试卷或模拟题 |

用户点击入口后，上传弹窗已经自动选中对应类型。弹窗内使用可读的分类卡片替代下拉框，仍可切换类型。

为保证老用户和已有能力兼容，HOMEWORK 和 OTHER 继续保留为“作业”“其他资料”分类，没有修改数据库约束、后端 `DOCUMENT_TYPES` 或历史数据。

## 2. 修改文件

- `frontend/src/components/course/uploadCategories.ts`
  - 单一管理资料类型、用户文案和主入口属性。
- `frontend/src/components/course/CourseMaterials.tsx`
  - 增加四个分类上传入口；空状态引导优先上传教材或课件。
- `frontend/src/components/course/UploadDocumentDialog.tsx`
  - 接收入口预选类型；用分类卡片代替技术型下拉框。
- `tests/test_upload_experience_frontend.py`
  - 验证四个入口映射、弹窗提交类型和原 API FormData 字段。

## 3. 兼容性

- `POST /api/courses/{course_id}/documents` 未修改；
- multipart 字段仍为 `file` 和 `document_type`；
- 后端仍接受 TEXTBOOK、SLIDES、NOTES、EXAM、HOMEWORK、OTHER；
- 已有文档和已有分析结果不受影响；
- AI 生成逻辑、Prompt 和权重没有修改。

## 4. 测试结果

- `pnpm build`：通过；
- `pytest`：117 passed，1 个既有依赖弃用警告；
- 新增上传体验契约测试：3 项通过；
- 原上传 API、不同文档类型和多用户隔离测试继续通过。

## 5. 验收建议

1. 在有资料和无资料课程中分别检查四个入口；
2. 点击每个入口后确认弹窗默认高亮对应类型；
3. 上传后在文件列表和后端数据中确认 document_type；
4. 使用“作业”和“其他资料”确认兼容入口可用；
5. 上传 PDF、PPTX、TXT、MD 各一份，确认原格式校验不变。
