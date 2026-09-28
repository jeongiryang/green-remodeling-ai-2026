"""Contest workflow checks. Standard library only; no network or AI calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
STAGES = ["ideation", "decision", "proposal", "review", "submission", "results",
          "finalist_plan", "implementation", "final_review"]
NEXT = {
    "ideation": "harness/IDEATION.md에 따라 문제·데이터·기존 방식의 근거를 조사하고 후보 3개 이상을 심층 비교하세요.",
    "decision": "후보 선택 근거를 기록하고 state.selected_candidate를 지정하세요. research/decision.md",
    "proposal": "선정 아이디어의 제안서·요약서·시각자료·AI 활용기록·주장 목록을 작성하세요.",
    "review": "실제 제출 파일과 팀 서류를 완성하고 예선 검토 기록을 채운 뒤 seal-review preliminary를 실행하세요.",
    "submission": "온라인 신청과 자료 제출 후 state.submission에 실제 시각·접수 증빙을 기록하세요.",
    "results": "공식 결과를 확인한 뒤 state.outcome에 advanced 또는 not_selected와 증빙을 기록하세요.",
    "finalist_plan": "본선 공지와 추가 규격을 확인하고 최소 구현 계획을 작성하세요.",
    "implementation": "핵심 흐름을 구현하고 실행·테스트·실패 처리 증거 및 시연 대본을 작성하세요.",
    "final_review": "본선 제출 파일을 검토·확정하고 실제 제출 시각·증빙을 기록하세요.",
    "done": "본선 제출 증빙까지 기록되었습니다. 최종 파일과 회고를 보관하세요.",
    "closed": "미선정 결과를 기록했습니다. 제출본과 회고를 보관하세요.",
}
REVIEW_KEYS = {
    "preliminary": {"latest_rules", "problem_and_originality", "data_and_ai_feasibility",
                    "claims_and_sources", "visual_and_page_layout", "blind_review",
                    "ai_and_external_credits", "team_signatures_and_eligibility", "files_and_delivery_access"},
    "final": {"official_final_rules", "core_flow_and_failure_cases", "ai_baseline_and_limitations",
              "user_accessibility", "demo_and_questions", "final_files_and_credits"},
}
CANDIDATE_FIELDS = ("title", "building", "user", "problem", "green_link", "ai_role", "data_plan",
                    "baseline", "differentiation", "finalist_scope", "risks", "problem_evidence",
                    "data_access", "ai_input", "ai_method", "ai_output", "ai_necessity",
                    "verification", "user_flow", "preliminary_visual")
EVIDENCE_ROLES = ("problem", "green_link", "data", "alternative")
PROTOTYPE_FIELDS = ("core_flow", "data_mode", "components", "dependencies",
                    "effort_estimate", "fallback", "acceptance_test")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME)\b|작성 예정", re.I)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip()) and not PLACEHOLDER.search(value)


class Harness:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.project = self.read("harness/project.json")
        self.state = self.read("harness/state.json")
        self.sources = self.read("research/sources.json")["sources"]
        self.candidates = self.read("research/candidates.json")["candidates"]
        self.claims = self.read("research/claims.json")["claims"]

    def path(self, relative):
        if not isinstance(relative, str) or not relative.strip():
            raise ValueError("파일 경로가 비어 있습니다")
        # Reject Windows paths even on Linux CI, as well as traversal/symlink escapes.
        if Path(relative).is_absolute() or re.match(r"^[A-Za-z]:|^[/\\]", relative):
            raise ValueError(f"상대 경로만 허용: {relative}")
        path = (self.root / relative.replace("\\", "/")).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"프로젝트 밖 경로: {relative}")
        return path

    def read(self, relative):
        return json.loads(self.path(relative).read_text(encoding="utf-8-sig"))

    def write(self, relative, data):
        path = self.path(relative)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def evidence(self, relative):
        try:
            path = self.path(relative)
            if not path.is_file() or path.stat().st_size == 0:
                return False
            if path.suffix.lower() in {".md", ".txt"}:
                return nonempty(path.read_text(encoding="utf-8-sig"))
            return True
        except (ValueError, OSError, UnicodeError):
            return False

    def sha(self, relative):
        return hashlib.sha256(self.path(relative).read_bytes()).hexdigest()

    def validate(self):
        errors = []
        p, s = self.project, self.state
        if p.get("division") != "AI 플랫폼 아이디어":
            errors.append("참가 부문은 AI 플랫폼 아이디어여야 합니다")
        if s.get("stage") not in STAGES + ["done", "closed"]:
            errors.append("알 수 없는 단계")
        try:
            if datetime.fromisoformat(p["deadline"]).utcoffset() is None:
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            errors.append("마감 시각은 시간대가 포함된 ISO 형식이어야 합니다")
        if type(p.get("team_size")) is not int or not 2 <= p["team_size"] <= 4:
            errors.append("팀 인원은 2~4명")
        if type(p.get("minimum_candidates")) is not int or p["minimum_candidates"] < 1:
            errors.append("내부 후보 최소 개수는 양의 정수")
        if p.get("weights") != {"problem": 20, "fit": 20, "originality": 25, "feasibility": 20, "development": 15}:
            errors.append("예선 배점이 현재 공고와 다릅니다. 공식 변경 근거와 검사 코드도 함께 갱신하세요")
        expected_artifacts = {"comparison", "decision", "proposal", "summary", "visuals", "ai_usage",
                              "implementation_plan", "implementation_evidence", "demo"}
        if not isinstance(p.get("artifacts"), dict) or set(p["artifacts"]) != expected_artifacts:
            errors.append("산출물 경로 설정 누락")
        else:
            for value in p["artifacts"].values():
                try:
                    self.path(value)
                except ValueError as exc:
                    errors.append(str(exc))
        for key in ("submission", "final_submission"):
            if not isinstance(s.get(key), dict) or not {"at", "receipt"} <= s[key].keys():
                errors.append(f"state.{key} 형식 오류")
        if not isinstance(s.get("outcome"), dict) or s["outcome"].get("status") not in {"pending", "advanced", "not_selected"}:
            errors.append("결과 상태 형식 오류")
        for label, rows in (("sources", self.sources), ("candidates", self.candidates), ("claims", self.claims)):
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                errors.append(f"{label}은 객체 목록이어야 합니다")
                continue
            ids = [row.get("id") for row in rows]
            if any(not nonempty(value) for value in ids) or len(set(ids)) != len(ids):
                errors.append(f"{label} ID가 비어 있거나 중복됨")
        for kind, expected in REVIEW_KEYS.items():
            review = self.read(f"checks/{kind}-review.json")
            checks = review.get("checks")
            if not isinstance(checks, dict) or set(checks) != expected:
                errors.append(f"{kind} 검토 항목 누락·변경")
            elif any(not isinstance(v, dict) or type(v.get("passed")) is not bool or not isinstance(v.get("evidence"), str) for v in checks.values()):
                errors.append(f"{kind} 검토 항목 형식 오류")
        for kind in ("preliminary", "final"):
            manifest = self.read(f"submissions/{kind}/manifest.json")
            if not isinstance(manifest.get("files"), list) or any(not isinstance(v, dict) for v in manifest["files"]):
                errors.append(f"{kind} 제출 목록 형식 오류")
        # Downloaded sources must stay byte-identical, including extracted TXT files.
        for item in self.read("contest/source_manifest.json"):
            relative = "contest/originals/" + item["relative_path"].replace("\\", "/")
            if not self.evidence(relative) or self.sha(relative).lower() != item["sha256"].lower():
                errors.append(f"원본 변경·누락: {relative}")
        return errors

    def source_checks(self):
        errors = []
        for row in self.sources:
            if any(not nonempty(row.get(key)) for key in ("id", "title", "url", "checked_on", "locator", "finding")):
                errors.append(f"출처 필드 미완성: {row.get('id')}")
                continue
            if not re.match(r"https?://[^/\s]+", row["url"]):
                errors.append(f"출처 URL 오류: {row['id']}")
            try:
                datetime.strptime(row["checked_on"], "%Y-%m-%d")
            except ValueError:
                errors.append(f"출처 확인일 오류: {row['id']}")
        return errors

    def linked_sources(self, row):
        ids = row.get("source_ids")
        known = {s["id"] for s in self.sources}
        return isinstance(ids, list) and bool(ids) and all(isinstance(i, str) and i in known for i in ids)

    def artifact_checks(self, *names):
        return [f"산출물 미완성: {self.project['artifacts'][name]}" for name in names
                if not self.evidence(self.project["artifacts"][name])]

    def package_checks(self, kind):
        errors = []
        manifest = self.read(f"submissions/{kind}/manifest.json")
        files = manifest["files"]
        if not files:
            errors.append(f"{kind} 제출 파일 없음")
        if kind == "preliminary":
            kinds = [f.get("kind") for f in files]
            for required in ("proposal_pptx", "proposal_pdf", "summary", "application", "pledge"):
                if kinds.count(required) != 1:
                    errors.append(f"제출 항목은 정확히 하나 필요: {required}")
            members = [f.get("member_id") for f in files if f.get("kind") == "eligibility"]
            if len(members) != self.project["team_size"] or any(not nonempty(m) for m in members) or len(set(members)) != len(members):
                errors.append("팀원별 고유 ID와 자격 증빙 필요")
            if type(manifest.get("guardian_required")) is not bool:
                errors.append("미성년 팀원 유무 확인 필요")
            if manifest.get("guardian_required") is True and "guardian" not in kinds:
                errors.append("보호자 동의서 필요")
        elif not self.evidence(manifest.get("rules_evidence")):
            errors.append("본선 공식 규격 근거 필요")
        ppt_pages = pdf_pages = None
        for item in files:
            path, label = item.get("path"), item.get("kind")
            if not nonempty(label) or not self.evidence(path):
                errors.append(f"제출 파일 누락·미완성: {path}")
                continue
            if self.sha(path) != item.get("sha256"):
                errors.append(f"파일 해시 불일치: {path}")
            if item.get("opened") is not True:
                errors.append(f"파일 열기 검토 필요: {path}")
            extension = self.path(path).suffix.lower()
            if kind == "preliminary" and label == "proposal_pptx":
                try:
                    if extension != ".pptx":
                        raise ValueError("PPTX 필요")
                    with zipfile.ZipFile(self.path(path)) as archive:
                        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
                        ppt_pages = len(presentation.findall("{http://schemas.openxmlformats.org/presentationml/2006/main}sldIdLst/{http://schemas.openxmlformats.org/presentationml/2006/main}sldId"))
                    if not 1 <= ppt_pages <= 15:
                        errors.append("PPTX 표지 포함 1~15쪽 필요")
                except (ValueError, KeyError, zipfile.BadZipFile, ET.ParseError):
                    errors.append(f"PPTX 구조를 읽을 수 없음: {path}")
            if kind == "preliminary" and label in {"proposal_pdf", "summary"}:
                limit = 15 if label == "proposal_pdf" else 2
                allowed = {".pdf"} if label == "proposal_pdf" else {".pdf", ".hwp"}
                if extension not in allowed:
                    errors.append(f"파일 형식 오류: {path}")
                pages = item.get("pages")
                if type(pages) is not int or not 1 <= pages <= limit:
                    errors.append(f"직접 확인한 1~{limit}쪽 분량 필요: {path}")
                if label == "proposal_pdf":
                    pdf_pages = pages
            if extension == ".pdf" and not self.path(path).read_bytes().startswith(b"%PDF-"):
                errors.append(f"PDF 헤더 오류: {path}")
        if kind == "preliminary" and ppt_pages is not None and pdf_pages is not None and ppt_pages != pdf_pages:
            errors.append("제안서 PPTX와 PDF 쪽수 불일치")
        return errors

    def review_digest(self, kind):
        names = ["comparison", "decision", "proposal", "summary", "visuals", "ai_usage"]
        if kind == "final":
            names += ["implementation_plan", "implementation_evidence", "demo"]
        paths = {self.project["artifacts"][name] for name in names}
        paths.update(["harness/project.json", "research/sources.json", "research/candidates.json", "research/claims.json",
                      "contest/요구사항.md", f"submissions/{kind}/manifest.json"])
        paths.update(row["method_path"] for row in self.claims if row.get("method_path"))
        manifest = self.read(f"submissions/{kind}/manifest.json")
        paths.update(item["path"] for item in manifest["files"])
        if kind == "final":
            paths.add(manifest["rules_evidence"])
        review = self.read(f"checks/{kind}-review.json")
        paths.update(item["evidence"] for item in review["checks"].values())
        digest = hashlib.sha256()
        digest.update(json.dumps({"selected_candidate": self.state["selected_candidate"], "checks": review["checks"],
                                  "reviewer": review["reviewer"]}, sort_keys=True, ensure_ascii=False).encode())
        for path in sorted(paths):
            digest.update(path.encode("utf-8"))
            digest.update(bytes.fromhex(self.sha(path)))
        return digest.hexdigest()

    def review_checks(self, kind, sealed=True):
        errors = self.package_checks(kind)
        review = self.read(f"checks/{kind}-review.json")
        if not nonempty(review.get("reviewer")):
            errors.append(f"{kind} 검토자 미기록")
        for key, item in review["checks"].items():
            if item.get("passed") is not True or not self.evidence(item.get("evidence")):
                errors.append(f"검토 미완료: {kind}/{key}")
        if not errors and sealed:
            if review.get("reviewed_digest") != self.review_digest(kind):
                errors.append(f"{kind} 검토 미확정 또는 검토 이후 파일 변경")
        return errors

    def receipt_checks(self, key):
        record = self.state[key]
        errors = []
        if not self.evidence(record.get("receipt")):
            errors.append(f"{key} 접수 확인 증빙 필요")
        try:
            stamp = datetime.fromisoformat(record.get("at", ""))
            if stamp.utcoffset() is None or stamp > datetime.now(KST):
                raise ValueError()
        except (ValueError, TypeError):
            errors.append(f"{key} 실제 접수 시각(시간대 포함, 미래 불가) 필요")
        return errors

    def gate(self, stage):
        errors = []
        if stage == "ideation":
            errors += self.source_checks()
            if len(self.candidates) < self.project["minimum_candidates"]:
                errors.append(f"아이디어 후보 최소 {self.project['minimum_candidates']}개 필요")
            for row in self.candidates:
                if any(not nonempty(row.get(k)) for k in CANDIDATE_FIELDS) or not self.linked_sources(row):
                    errors.append(f"후보 설명·출처 미완성: {row.get('id')}")
                evidence = row.get("evidence")
                known = {source["id"] for source in self.sources}
                candidate_sources = row.get("source_ids")
                if not isinstance(evidence, dict) or set(evidence) != set(EVIDENCE_ROLES) or not isinstance(candidate_sources, list) or any(
                    not isinstance(evidence[role], list) or not evidence[role] or
                    any(not isinstance(source_id, str) or source_id not in known or source_id not in candidate_sources
                        for source_id in evidence[role]) for role in EVIDENCE_ROLES
                ):
                    errors.append(f"후보 문제·그린리모델링·데이터·기존 방식 근거 미완성: {row.get('id')}")
                prototype = row.get("prototype_plan")
                if not isinstance(prototype, dict) or prototype.get("readiness") not in {"ready", "conditional", "blocked"} or any(
                    not nonempty(prototype.get(field)) for field in PROTOTYPE_FIELDS
                ):
                    errors.append(f"후보 본선 구현성 검토 미완성: {row.get('id')}")
                for key in self.project["weights"]:
                    score = row.get("scores", {}).get(key, {})
                    if type(score.get("score")) not in (int, float) or not 0 <= score["score"] <= 5 or not nonempty(score.get("reason")):
                        errors.append(f"후보 내부평가 미완성: {row.get('id')}/{key}")
            errors += self.artifact_checks("comparison")
        elif stage == "decision":
            if self.state.get("selected_candidate") not in {row["id"] for row in self.candidates}:
                errors.append("선정 후보 ID 필요")
            else:
                selected = next(row for row in self.candidates if row["id"] == self.state["selected_candidate"])
                prototype = selected.get("prototype_plan")
                if not isinstance(prototype, dict) or prototype.get("readiness") != "ready":
                    errors.append("선정 후보는 본선 최소 시연 가능 상태(ready)로 검토되어야 합니다")
            errors += self.artifact_checks("decision")
        elif stage == "proposal":
            errors += self.artifact_checks("proposal", "summary", "visuals", "ai_usage")
            if not self.claims:
                errors.append("제안서 주장·근거 목록 필요")
            for row in self.claims:
                kind = row.get("kind")
                if kind not in {"fact", "estimate", "target", "hypothesis"} or not nonempty(row.get("text")) or not nonempty(row.get("used_in")):
                    errors.append(f"주장 형식 미완성: {row.get('id')}")
                if kind in {"fact", "estimate"} and not self.linked_sources(row):
                    errors.append(f"주장 출처 필요: {row.get('id')}")
                if kind == "estimate" and not self.evidence(row.get("method_path")):
                    errors.append(f"추정 계산 근거 필요: {row.get('id')}")
        elif stage == "review":
            errors += self.review_checks("preliminary")
        elif stage == "submission":
            errors += self.receipt_checks("submission")
        elif stage == "results":
            outcome = self.state["outcome"]
            if outcome.get("status") not in {"advanced", "not_selected"} or not self.evidence(outcome.get("evidence")):
                errors.append("공식 결과와 확인 증빙 필요. 본선 구현은 진출 확인 후 시작")
        elif stage == "finalist_plan":
            if self.state["outcome"].get("status") != "advanced":
                errors.append("본선 진출 기록 필요")
            errors += self.artifact_checks("implementation_plan")
            if not self.evidence(self.read("submissions/final/manifest.json").get("rules_evidence")):
                errors.append("본선 공식 안내·규격 필요")
        elif stage == "implementation":
            errors += self.artifact_checks("implementation_evidence", "demo")
        elif stage == "final_review":
            errors += self.review_checks("final")
            errors += self.receipt_checks("final_submission")
        return errors

    def check(self, stage=None):
        errors = self.validate()
        if errors:
            return errors
        stage = stage or self.state["stage"]
        end = STAGES.index(stage) if stage in STAGES else (5 if stage == "closed" else 8)
        for previous in STAGES[:end + 1]:
            errors += self.gate(previous)
        if stage == "closed" and self.state["outcome"]["status"] != "not_selected":
            errors.append("종료 상태와 결과 불일치")
        return errors

    def advance(self):
        errors = self.check()
        if errors:
            return errors
        before = self.state["stage"]
        if before in {"done", "closed"}:
            return ["이미 종료된 단계입니다"]
        after = "done" if before == "final_review" else STAGES[STAGES.index(before) + 1]
        if before == "results" and self.state["outcome"]["status"] == "not_selected":
            after = "closed"
        self.state["stage"] = after
        self.write("harness/state.json", self.state)
        with self.path("harness/history.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps({"at": datetime.now(KST).isoformat(), "from": before, "to": after}, ensure_ascii=False) + "\n")
        print(f"{before} → {after}. STATUS.md에 작업 결과와 다음 행동을 반영하세요.")
        return []


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "next", "validate", "advance"):
        sub.add_parser(name)
    check = sub.add_parser("check")
    check.add_argument("--stage", choices=STAGES)
    seal = sub.add_parser("seal-review")
    seal.add_argument("kind", choices=REVIEW_KEYS)
    seal.add_argument("--reviewer", required=True)
    sub.add_parser("hash").add_argument("path")
    args = parser.parse_args(argv)
    try:
        h = Harness()
        if args.command == "hash":
            print(h.sha(args.path))
            return 0
        errors = h.validate()
        if not errors and args.command == "check":
            errors = h.check(args.stage)
        elif not errors and args.command == "advance":
            errors = h.advance()
        elif not errors and args.command == "seal-review":
            # Check all earlier gates, but allow an unsealed review for the current package.
            previous = "proposal" if args.kind == "preliminary" else "implementation"
            errors = h.check(previous)
            if not nonempty(args.reviewer):
                errors.append("검토자 이름 필요")
            if not errors:
                path = f"checks/{args.kind}-review.json"
                review = h.read(path)
                review["reviewer"] = args.reviewer
                h.write(path, review)
                errors = h.review_checks(args.kind, sealed=False)
                if not errors:
                    review["reviewed_digest"] = h.review_digest(args.kind)
                    h.write(path, review)
                    print("검토 확정: " + args.kind)
        elif not errors and args.command in {"status", "next"}:
            print(f"부문: {h.project['division']} | 단계: {h.state['stage']}")
            if args.command == "status":
                deadline = datetime.fromisoformat(h.project["deadline"])
                hours = (deadline - datetime.now(KST)).total_seconds() / 3600
                print(f"예선 마감: {deadline.isoformat()} | {'남은' if hours >= 0 else '경과'} 시간: {abs(hours):.1f}시간")
                print(f"후보 {len(h.candidates)}개 | 선정: {h.state.get('selected_candidate') or '미정'}")
                for row in h.candidates:
                    try:
                        total = sum(row["scores"][key]["score"] / 5 * weight for key, weight in h.project["weights"].items())
                        print(f"  {row['id']}: 내부 비교 {total:.1f}/100 (심사점수 아님)")
                    except (KeyError, TypeError):
                        print(f"  {row['id']}: 내부평가 미완성")
            print(NEXT[h.state["stage"]])
        if errors:
            for message in errors:
                print("미충족: " + message)
            return 1
        if args.command in {"check", "validate"}:
            print("통과: " + ("구조·원본 검사 (제출 준비 완료와 별개)" if args.command == "validate" else "기록·파일 검사 (내용의 진실성·품질은 검토 기록 기준)"))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"입력·파일 오류: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
