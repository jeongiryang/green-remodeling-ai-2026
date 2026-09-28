import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("harness", ROOT / "scripts/harness.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        # Keep tests independent of the real team's progress and private files.
        for name in ("harness", "research", "checks", "submissions", "contest"):
            shutil.copytree(ROOT / name, self.root / name)
        self.h = module.Harness(self.root)
        self.h.state = {"stage": "ideation", "selected_candidate": None,
                        "outcome": {"status": "pending", "evidence": ""},
                        "submission": {"at": "", "receipt": ""},
                        "final_submission": {"at": "", "receipt": ""}}
        self.h.sources, self.h.candidates, self.h.claims = [], [], []
        self.h.write("harness/state.json", self.h.state)
        self.h.write("research/sources.json", {"sources": []})
        self.h.write("research/candidates.json", {"candidates": []})
        self.h.write("research/claims.json", {"claims": []})
        for kind, keys in module.REVIEW_KEYS.items():
            self.h.write(f"checks/{kind}-review.json", {"reviewer": "", "reviewed_digest": "",
                         "checks": {key: {"passed": False, "evidence": ""} for key in keys}})
        self.h.write("submissions/preliminary/manifest.json", {"guardian_required": None, "files": []})
        self.h.write("submissions/final/manifest.json", {"rules_evidence": "", "files": []})

    def tearDown(self):
        self.temp.cleanup()

    def file(self, path, text="Test fixture evidence. Not real contest work."):
        full = self.h.path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(text, encoding="utf-8")
        return path

    def ideation(self):
        self.h.sources = [{"id": "S001", "title": "Fixture", "url": "https://example.org/source",
                           "checked_on": "2026-09-27", "locator": "page 1", "finding": "Fixture observation"}]
        self.h.candidates = []
        for i in range(3):
            row = {key: "Fixture content" for key in module.CANDIDATE_FIELDS}
            row.update(id=f"I{i + 1}", source_ids=["S001"],
                       evidence={role: ["S001"] for role in module.EVIDENCE_ROLES},
                       scores={key: {"score": 3, "reason": "Fixture reason"} for key in self.h.project["weights"]})
            self.h.candidates.append(row)
        self.h.write("research/sources.json", {"sources": self.h.sources})
        self.h.write("research/candidates.json", {"candidates": self.h.candidates})
        self.file(self.h.project["artifacts"]["comparison"])

    def proposal(self):
        self.ideation()
        self.h.state["selected_candidate"] = "I1"
        for name in ("decision", "proposal", "summary", "visuals", "ai_usage"):
            self.file(self.h.project["artifacts"][name])
        self.h.claims = [{"id": "C1", "text": "Fixture assertion", "kind": "fact",
                          "source_ids": ["S001"], "used_in": "slide 2", "method_path": ""}]
        self.h.write("research/claims.json", {"claims": self.h.claims})

    def package(self, slides=3):
        folder = self.root / "deliverables/submission"
        folder.mkdir(parents=True, exist_ok=True)
        ppt = folder / "proposal.pptx"
        with zipfile.ZipFile(ppt, "w") as z:
            xml = '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldIdLst>'
            xml += ''.join(f'<p:sldId id="{256 + i}"/>' for i in range(slides))
            z.writestr("ppt/presentation.xml", xml + '</p:sldIdLst></p:presentation>')
        rows = [{"kind": "proposal_pptx", "path": "deliverables/submission/proposal.pptx"}]
        for kind in ("proposal_pdf", "summary", "application", "pledge"):
            path = self.file(f"private/{kind}.pdf", "%PDF-1.7\nFixture only\n%%EOF")
            rows.append({"kind": kind, "path": path, "pages": slides if kind == "proposal_pdf" else 2})
        for i in range(3):
            path = self.file(f"private/member{i}.pdf", "%PDF-1.7\nFixture only\n%%EOF")
            rows.append({"kind": "eligibility", "path": path, "member_id": f"member{i}"})
        for row in rows:
            row.update(sha256=self.h.sha(row["path"]), opened=True)
        manifest = {"guardian_required": False, "files": rows}
        self.h.write("submissions/preliminary/manifest.json", manifest)
        return manifest

    def review(self):
        self.proposal()
        self.package()
        evidence = self.file("checks/evidence.md")
        review = {"reviewer": "Fixture reviewer", "reviewed_digest": "", "checks": {
            key: {"passed": True, "evidence": evidence} for key in module.REVIEW_KEYS["preliminary"]}}
        self.h.write("checks/preliminary-review.json", review)
        review["reviewed_digest"] = self.h.review_digest("preliminary")
        self.h.write("checks/preliminary-review.json", review)

    def test_empty_workspace_valid_but_not_ready(self):
        self.assertEqual([], self.h.validate())
        self.assertTrue(self.h.check())
        self.assertTrue(self.h.advance())
        self.assertEqual("ideation", self.h.read("harness/state.json")["stage"])

    def test_sources_cannot_escape_workspace(self):
        for path in ("../secret", "/secret", "C:\\secret", "..\\secret"):
            with self.assertRaises(ValueError):
                self.h.path(path)

    def test_original_tampering_is_detected(self):
        item = self.h.read("contest/source_manifest.json")[0]
        self.file("contest/originals/" + item["relative_path"].replace("\\", "/"), "Changed")
        self.assertTrue(any("원본 변경" in e for e in self.h.validate()))

    def test_valid_ideas_advance_once_and_record_history(self):
        self.ideation()
        self.assertEqual([], self.h.check())
        self.assertEqual([], self.h.advance())
        self.assertEqual("decision", self.h.read("harness/state.json")["stage"])
        self.assertTrue(self.h.evidence("harness/history.jsonl"))
        self.assertTrue(self.h.advance())  # Topic selection still missing.

    def test_unknown_source_and_out_of_range_score_fail(self):
        self.ideation()
        self.h.candidates[0]["source_ids"] = ["missing"]
        self.h.candidates[1]["scores"]["problem"]["score"] = 6
        self.assertGreaterEqual(len(self.h.check()), 2)

    def test_idea_requires_separate_ai_and_validation_details(self):
        self.ideation()
        self.h.candidates[0]["ai_necessity"] = ""
        self.h.candidates[1]["verification"] = ""
        self.assertEqual(2, sum("후보 설명·출처 미완성" in error for error in self.h.check()))

    def test_idea_requires_traceable_evidence_for_each_question(self):
        self.ideation()
        self.h.candidates[0]["evidence"]["data"] = []
        self.h.candidates[1]["evidence"]["alternative"] = ["missing"]
        self.assertEqual(2, sum("후보 문제·그린리모델링·데이터·기존 방식 근거" in error
                                for error in self.h.check()))

    def test_empty_template_is_not_evidence(self):
        self.ideation()
        self.file(self.h.project["artifacts"]["comparison"], "# comparison\nTODO")
        self.assertTrue(self.h.check())

    def test_claim_estimate_requires_method(self):
        self.proposal()
        self.h.claims[0]["kind"] = "estimate"
        self.assertTrue(any("계산 근거" in e for e in self.h.check("proposal")))

    def test_valid_preliminary_review(self):
        self.review()
        self.assertEqual([], self.h.check("review"))

    def test_file_edit_invalidates_review(self):
        self.review()
        self.file(self.h.project["artifacts"]["proposal"], "Changed manuscript")
        self.assertTrue(any("파일 변경" in e for e in self.h.check("review")))

    def test_estimate_calculation_edit_invalidates_review(self):
        self.review()
        method = self.file("research/calculation.md")
        self.h.claims[0].update(kind="estimate", method_path=method)
        self.h.write("research/claims.json", {"claims": self.h.claims})
        r = self.h.read("checks/preliminary-review.json")
        r["reviewed_digest"] = self.h.review_digest("preliminary")
        self.h.write("checks/preliminary-review.json", r)
        self.file(method, "Changed assumptions")
        self.assertTrue(any("파일 변경" in e for e in self.h.check("review")))

    def test_review_evidence_edit_invalidates_review(self):
        self.review()
        self.file("checks/evidence.md", "Changed review evidence")
        self.assertTrue(any("파일 변경" in e for e in self.h.check("review")))

    def test_package_hash_change_fails(self):
        self.review()
        self.file("private/summary.pdf", "%PDF-1.7\nChanged\n%%EOF")
        self.assertTrue(any("해시" in e for e in self.h.check("review")))

    def test_slide_limit(self):
        self.package(slides=16)
        self.assertTrue(any("1~15" in e for e in self.h.package_checks("preliminary")))

    def test_pptx_wrong_extension_returns_failure(self):
        manifest = self.package()
        manifest["files"][0]["path"] = self.file("private/wrong.ppt", "legacy fixture")
        self.h.write("submissions/preliminary/manifest.json", manifest)
        self.assertTrue(self.h.package_checks("preliminary"))

    def test_pdf_and_slides_must_match(self):
        manifest = self.package()
        manifest["files"][1]["pages"] = 4
        self.h.write("submissions/preliminary/manifest.json", manifest)
        self.assertTrue(any("쪽수 불일치" in e for e in self.h.package_checks("preliminary")))

    def test_missing_eligibility_and_guardian(self):
        manifest = self.package()
        manifest["files"].pop()
        manifest["guardian_required"] = True
        self.h.write("submissions/preliminary/manifest.json", manifest)
        errors = self.h.package_checks("preliminary")
        self.assertTrue(any("자격 증빙" in e for e in errors))
        self.assertTrue(any("보호자" in e for e in errors))

    def test_review_does_not_mean_submission(self):
        self.review()
        self.assertTrue(any("접수 확인" in e for e in self.h.check("submission")))

    def test_future_submission_time_fails(self):
        self.h.state["submission"] = {"at": "2999-01-01T00:00:00+09:00", "receipt": self.file("private/receipt.md")}
        self.assertTrue(self.h.receipt_checks("submission"))

    def test_finalist_plan_blocked_without_result(self):
        self.assertTrue(any("진출" in e for e in self.h.gate("results")))
        self.assertTrue(any("진출" in e for e in self.h.gate("finalist_plan")))

    def test_not_selected_closes_without_implementation(self):
        self.review()
        self.h.state.update(stage="results", submission={"at": "2026-01-01T00:00:00+09:00", "receipt": self.file("private/receipt.md")},
                            outcome={"status": "not_selected", "evidence": self.file("private/result.md")})
        self.assertEqual([], self.h.advance())
        self.assertEqual("closed", self.h.state["stage"])

    def test_final_manifest_uses_new_rules_not_preliminary_page_limits(self):
        rules = self.file("contest/final-rules.md")
        doc = self.file("deliverables/final/deck.pdf", "%PDF-1.7\nFixture\n%%EOF")
        self.h.write("submissions/final/manifest.json", {"rules_evidence": rules, "files": [
            {"kind": "final_deck", "path": doc, "sha256": self.h.sha(doc), "opened": True, "pages": 20}]})
        self.assertEqual([], self.h.package_checks("final"))

    def test_removing_review_criterion_fails_validation(self):
        review = self.h.read("checks/preliminary-review.json")
        del review["checks"]["blind_review"]
        self.h.write("checks/preliminary-review.json", review)
        self.assertTrue(any("검토 항목" in e for e in self.h.validate()))

    def test_complete_lifecycle_requires_final_receipt(self):
        self.review()
        self.h.state.update(stage="results", submission={"at": "2026-01-01T00:00:00+09:00", "receipt": self.file("private/receipt.md")},
                            outcome={"status": "advanced", "evidence": self.file("private/result.md")})
        self.assertEqual([], self.h.advance())
        self.assertEqual("finalist_plan", self.h.state["stage"])
        self.file(self.h.project["artifacts"]["implementation_plan"])
        rules = self.file("contest/final-rules.md")
        self.h.write("submissions/final/manifest.json", {"rules_evidence": rules, "files": []})
        self.assertEqual([], self.h.advance())
        self.assertEqual("implementation", self.h.state["stage"])
        for key in ("implementation_evidence", "demo"):
            self.file(self.h.project["artifacts"][key])
        self.assertEqual([], self.h.advance())
        doc = self.file("deliverables/final/deck.pdf", "%PDF-1.7\nFixture\n%%EOF")
        self.h.write("submissions/final/manifest.json", {"rules_evidence": rules, "files": [
            {"kind": "final_deck", "path": doc, "sha256": self.h.sha(doc), "opened": True}]})
        evidence = self.file("checks/final-evidence.md")
        review = {"reviewer": "Fixture", "reviewed_digest": "", "checks": {
            key: {"passed": True, "evidence": evidence} for key in module.REVIEW_KEYS["final"]}}
        self.h.write("checks/final-review.json", review)
        review["reviewed_digest"] = self.h.review_digest("final")
        self.h.write("checks/final-review.json", review)
        self.assertTrue(self.h.advance())
        self.assertEqual("final_review", self.h.state["stage"])
        self.h.state["final_submission"] = {"at": "2026-01-02T00:00:00+09:00", "receipt": self.file("private/final-receipt.md")}
        self.assertEqual([], self.h.advance())
        self.assertEqual("done", self.h.state["stage"])


if __name__ == "__main__":
    unittest.main()
