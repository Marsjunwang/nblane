"""Tests for the structured resume document (normalize / render / import)."""

from __future__ import annotations

import unittest

from nblane.core import resume_doc

RESUME_MD = """\
# 张三 | 具身智能算法工程师

28岁 | 硕士 | 📞 13800000000 | ✉️ zhangsan@example.com

## 工作概要

具身智能算法工程师，**主导 VLA 复现**。

## 核心技能

- **具身大模型**:VLA、VLM 多模态对齐
- **工程能力**:PyTorch、ROS

## 工作经历

### 示例机器人公司 | 具身算法工程师 | 2025/04 – 至今

**VLA(主线)**
- 主导 PI0.5 复现，成功率从 **20% 提升至 95%**。

**科研产出**
- 第一作者论文:*Example Paper*

### 示例汽车研究院 | 感知算法工程师 | 2022/08 – 2025/04

- 训练速度优化 60%。

### 示例车企(实习) | 2020/07 – 2020/09

- 测试支持。

## 教育经历

- 示例大学 | 车辆工程 硕士 | 2018/09 – 2021/06
- 示例大学 | 车辆工程 本科 | 2014/09 – 2018/06

## 荣誉与其他

- 数学建模竞赛一等奖

## 开源

- example/repo
"""


class ParseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = resume_doc.parse_resume_markdown(RESUME_MD, profile="zhang")

    def test_header_and_contacts(self) -> None:
        basics = self.doc["basics"]
        self.assertEqual(basics["name"], "张三")
        self.assertEqual(basics["title"], "具身智能算法工程师")
        self.assertEqual(basics["phone"], "13800000000")
        self.assertEqual(basics["email"], "zhangsan@example.com")
        self.assertEqual(basics["tagline"], "28岁 | 硕士")
        self.assertEqual(self.doc["lang"], "zh")

    def test_sections(self) -> None:
        self.assertIn("主导 VLA 复现", self.doc["summary"])
        self.assertEqual(self.doc["skill_groups"][0], {"label": "具身大模型", "text": "VLA、VLM 多模态对齐"})
        first = self.doc["experiences"][0]
        self.assertEqual((first["company"], first["role"], first["start"], first["end"]),
                         ("示例机器人公司", "具身算法工程师", "2025/04", "至今"))
        self.assertEqual([g["label"] for g in first["groups"]], ["VLA(主线)", "科研产出"])
        self.assertEqual(self.doc["experiences"][2]["company"], "示例车企(实习)")
        self.assertEqual(self.doc["education"][0]["school"], "示例大学")
        self.assertEqual(self.doc["education"][0]["degree"], "车辆工程 硕士")
        self.assertEqual(self.doc["honors"], ["数学建模竞赛一等奖"])
        # Unknown section kept verbatim, original section titles remembered.
        self.assertEqual(self.doc["extra_sections"], [{"title": "开源", "body": "- example/repo"}])
        self.assertEqual(self.doc["section_titles"]["skills"], "核心技能")

    def test_round_trip(self) -> None:
        rendered = resume_doc.render_resume_markdown(self.doc)
        self.assertEqual(resume_doc.parse_resume_markdown(rendered, profile="zhang"), self.doc)
        self.assertIn("### 示例机器人公司 | 具身算法工程师 | 2025/04 – 至今", rendered)
        self.assertIn("- **具身大模型**：VLA、VLM 多模态对齐", rendered)

    def test_fenced_and_target_comment_are_stripped(self) -> None:
        wrapped = "<!-- Target: x -->\n\n```markdown\n" + RESUME_MD + "```\n"
        self.assertEqual(resume_doc.parse_resume_markdown(wrapped, profile="zhang"), self.doc)


class NormalizeTest(unittest.TestCase):
    def test_legacy_shape_renders(self) -> None:
        legacy = {
            "profile": "alice",
            "visibility": "public",
            "basics": {"name": "Alice", "title": "Robotics Engineer", "email": "alice@example.com"},
            "summary": "Works on embodied AI.",
            "skills": ["VLA", "ROS 2"],
            "experiences": [{"role": "Engineer", "org": "Lab", "start": "2025", "end": "present",
                             "bullets": ["Built a public demo."]}],
            "custom_key": {"kept": True},
        }
        doc = resume_doc.normalize_resume(legacy)
        self.assertEqual(doc["experiences"][0]["company"], "Lab")
        self.assertEqual(doc["custom_key"], {"kept": True})
        md = resume_doc.render_resume_markdown(legacy)
        self.assertIn("# Alice | Robotics Engineer", md)
        self.assertIn("## Experience", md)
        self.assertIn("### Lab | Engineer | 2025 – present", md)

    def test_has_content(self) -> None:
        self.assertFalse(resume_doc.has_content({"profile": "a", "basics": {"name": "a"}}))
        self.assertTrue(resume_doc.has_content({"basics": {"name": "a"}, "summary": "x"}))


class HtmlTest(unittest.TestCase):
    def test_html_import(self) -> None:
        page = (
            "<html><head><style>h1{}</style></head><body><header><div>"
            "<h1>张三</h1><div class='subtitle'>算法工程师</div>"
            "<div class='contact'>28岁 &nbsp;|&nbsp; ✉️ zhangsan@example.com</div></div>"
            "<img src='photo.jpg'></header>"
            "<h2>工作经历</h2><h3>示例公司 · 工程师 <span class='meta'>2025/04 – 至今</span></h3>"
            "<div class='group'>主线</div><ul><li>做了 <strong>A</strong></li></ul>"
            "<h2>教育经历</h2><ul><li>甲大学 · 硕士 <span class='meta'>2018 – 2021</span>"
            " &nbsp;|&nbsp; 乙大学 · 本科 <span class='meta'>2014 – 2018</span></li></ul>"
            "</body></html>"
        )
        doc = resume_doc.parse_resume_markdown(resume_doc.html_resume_to_markdown(page))
        self.assertEqual(doc["basics"]["title"], "算法工程师")
        self.assertEqual(doc["basics"]["email"], "zhangsan@example.com")
        exp = doc["experiences"][0]
        self.assertEqual((exp["company"], exp["role"], exp["end"]), ("示例公司", "工程师", "至今"))
        self.assertEqual(exp["groups"], [{"label": "主线", "bullets": ["做了 **A**"]}])
        self.assertEqual([e["school"] for e in doc["education"]], ["甲大学", "乙大学"])

    def test_render_html_has_photo_and_header(self) -> None:
        doc = resume_doc.parse_resume_markdown(RESUME_MD)
        page = resume_doc.render_resume_html(
            resume_doc.render_resume_markdown(doc), photo_src="data:image/png;base64,AAAA",
            summary_title="工作概要",
        )
        self.assertIn('<div class="subtitle">具身智能算法工程师</div>', page)
        self.assertIn('class="photo" src="data:image/png;base64,AAAA"', page)
        self.assertIn('<p class="contact">', page)
        self.assertIn('<p class="summary">', page)
        self.assertIn('<span class="meta">2025/04 – 至今</span>', page)
        self.assertIn('<p class="group">VLA(主线)</p>', page)

    def test_html_escapes_script(self) -> None:
        page = resume_doc.render_resume_html("# X\n\n[a](javascript:alert(1))\n")
        self.assertNotIn("javascript:", page)


if __name__ == "__main__":
    unittest.main()
