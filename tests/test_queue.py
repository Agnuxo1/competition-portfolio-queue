# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Behavioural tests for the register, the scheduler and the read-only tick."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from competition_queue.cli import main
from competition_queue.model import Competition, load_register, parse_utc, public_rows, validate
from competition_queue.render import private_list, public_list
from competition_queue.schedule import Pin, effective_deadline, lane, ordered, simulate
from competition_queue.tick import audit, queue_entries

NOW = datetime(2026, 11, 6, 8, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


def comp(cid="a", **kw):
    base = dict(
        id=cid, name=cid.upper(), platform="Kaggle", url=f"https://example.org/{cid}",
        region="Global", compute="gpu", stage="PREPARING",
        submission_utc="2026-11-10T00:00:00Z",
    )
    return Competition(**{**base, **kw})


def test_parse_utc_rejects_naive_timestamps():
    with pytest.raises(ValueError):
        parse_utc("2026-11-06T10:00:00")


def test_validate_accepts_a_clean_entry():
    assert validate([comp()]) == []


@pytest.mark.parametrize(
    "bad, fragment",
    [
        ({"stage": "NOPE"}, "unknown stage"),
        ({"compute": "tpu"}, "unknown compute"),
        ({"url": "http://example.org"}, "https"),
        ({"url": "https://mail.google.com/"}, "private material"),
        ({"repo": "x", "repo_visibility": "none"}, "without visibility"),
        ({"submission_utc": None}, "without any deadline"),
    ],
)
def test_validate_reports_each_defect(bad, fragment):
    assert any(fragment in e for e in validate([comp(**bad)]))


def test_validate_requires_a_real_boolean_for_registered():
    assert any("registered" in e for e in validate([comp(registered="false")]))


def test_validate_reports_duplicates():
    assert any("duplicate" in e for e in validate([comp(), comp()]))


def test_registration_counts_until_the_entry_is_registered():
    pending = comp(stage="ELIGIBLE", registration_utc="2026-11-07T00:00:00Z")
    done = comp(stage="ELIGIBLE", registration_utc="2026-11-07T00:00:00Z", registered=True)
    assert effective_deadline(pending, NOW) == parse_utc("2026-11-07T00:00:00Z")
    assert effective_deadline(done, NOW) == parse_utc("2026-11-10T00:00:00Z")


def test_lapsed_registration_ends_the_entry_and_is_reported():
    lapsed = comp(stage="READY", registration_utc="2026-11-06T07:30:00Z")
    assert effective_deadline(lapsed, NOW) is None
    assert ordered([lapsed], NOW) == []
    assert audit([lapsed], {}, NOW)["anomalies"]["registration_lapsed"][0]["id"] == "a"
    registered = comp(stage="READY", registration_utc="2026-11-06T07:30:00Z", registered=True)
    assert effective_deadline(registered, NOW) == parse_utc("2026-11-10T00:00:00Z")


def test_past_dates_do_not_count():
    gone = comp(submission_utc="2026-11-01T00:00:00Z")
    assert effective_deadline(gone, NOW) is None
    assert ordered([gone], NOW) == []


def test_order_is_earliest_deadline_first():
    a = comp("a", submission_utc="2026-11-20T00:00:00Z")
    b = comp("b", submission_utc="2026-11-08T00:00:00Z")
    assert [c.id for _, c in ordered([a, b], NOW)] == ["b", "a"]


def test_finished_stages_leave_the_order():
    assert ordered([comp(stage="SUBMITTED"), comp("b", stage="INELIGIBLE")], NOW) == []


@pytest.mark.parametrize(
    "kw, expected",
    [
        ({"stage": "TRAINING"}, "gpu"),
        ({"gate": "owner"}, "owner"),
        ({"gate": "organiser"}, "waiting"),
        ({"gpu_target_hours": 48}, "gpu"),
        ({"compute": "cpu"}, "agent"),
    ],
)
def test_lane_selection(kw, expected):
    assert lane(comp(**kw)) == expected


def test_simulate_fills_target_and_respects_freeze():
    c = comp(gpu_target_hours=48, submission_utc="2026-11-08T00:00:00Z")
    a = simulate([c], NOW)["a"]
    assert a.delivered == pytest.approx(48) and a.status == "FULL"
    assert a.last < a.stop


def test_simulate_marks_impossible_targets_partial():
    c = comp(gpu_target_hours=48, submission_utc="2026-11-06T14:00:00Z")
    a = simulate([c], NOW)["a"]
    assert 0 < a.delivered < 48 and a.status == "PARTIAL"
    assert a.delivered == pytest.approx(8)  # four usable hours on two cards


def test_partial_hours_are_not_rounded_up():
    start = parse_utc("2026-11-06T08:30:00Z")
    c = comp(gpu_target_hours=48, submission_utc="2026-11-06T12:00:00Z")
    a = simulate([c], start)["a"]
    assert a.delivered == pytest.approx(3)  # 08:30 to the 10:00 stop on two cards
    assert a.last == parse_utc("2026-11-06T10:00:00Z")


def test_pin_credit_stops_at_the_target_and_reports_the_surplus():
    c = comp(gpu_target_hours=1, submission_utc="2026-11-09T00:00:00Z")
    a = simulate([c], NOW, pins=(Pin("a", NOW, NOW + timedelta(hours=1), 2),))["a"]
    assert a.delivered == pytest.approx(1) and a.extra == pytest.approx(1)


def test_pin_never_credits_after_the_stop():
    c = comp(gpu_target_hours=48, submission_utc="2026-11-06T12:00:00Z")
    pin = Pin("a", NOW, NOW + timedelta(hours=24), 2)
    a = simulate([c], NOW, pins=(pin,))["a"]
    assert a.delivered == pytest.approx(4) and a.last <= a.stop


def test_pin_edges_inside_an_hour_are_exact():
    c = comp(gpu_target_hours=48, submission_utc="2026-11-06T12:00:00Z")
    other = comp("other", gpu_target_hours=48, submission_utc="2026-11-09T00:00:00Z")
    pin = Pin("other", NOW, NOW + timedelta(minutes=30), 2)
    r = simulate([c, other], NOW, pins=(pin,))
    assert r["a"].delivered == pytest.approx(3)


def test_pin_gives_no_credit_before_not_before():
    c = comp(gpu_target_hours=48, not_before_utc="2026-11-06T09:00:00Z")
    pin = Pin("a", NOW, NOW + timedelta(hours=2), 2)
    a = simulate([c], NOW, gpus=2, pins=(pin,))["a"]
    assert a.first == parse_utc("2026-11-06T09:00:00Z")
    pinned_only = simulate([comp(gpu_target_hours=48, not_before_utc="2026-11-06T09:00:00Z",
                                 submission_utc="2026-11-06T12:00:00Z")], NOW, pins=(pin,))["a"]
    assert pinned_only.delivered == pytest.approx(2)  # only 09:00-10:00 on two cards counts


def test_simulate_skips_a_lapsed_registration():
    c = comp(gpu_target_hours=48, registration_utc="2026-11-06T07:00:00Z")
    assert simulate([c], NOW) == {}


def test_simulate_stops_at_a_pending_registration():
    c = comp(gpu_target_hours=48, registration_utc="2026-11-06T09:00:00Z")
    a = simulate([c], NOW)["a"]
    assert a.delivered == pytest.approx(2) and a.stop == parse_utc("2026-11-06T09:00:00Z")


def test_simulate_ignores_a_completed_registration():
    c = comp(gpu_target_hours=4, registration_utc="2026-11-06T07:00:00Z", registered=True)
    assert simulate([c], NOW)["a"].delivered == pytest.approx(4)


@pytest.mark.parametrize("gpus, hours", [(-1, 1), (0, 1), (1, 0), (1, -1)])
def test_pin_rejects_invalid_values(gpus, hours):
    with pytest.raises(ValueError):
        Pin("a", NOW, NOW + timedelta(hours=hours), gpus)


def test_capacity_is_conserved():
    a = comp("a", gpu_target_hours=10, submission_utc="2026-11-06T14:00:00Z")
    b = comp("b", gpu_target_hours=10, submission_utc="2026-11-06T14:00:00Z")
    r = simulate([a, b], NOW)
    assert r["a"].delivered + r["b"].delivered == pytest.approx(8)


def test_pin_takes_capacity_from_other_entries():
    start, end = NOW, NOW + timedelta(hours=40)
    other = comp("other", gpu_target_hours=48, submission_utc="2026-11-07T22:00:00Z")
    free = simulate([other], NOW)["other"]
    pinned = simulate([other], NOW, pins=(Pin("x", start, end, 2),))["other"]
    assert free.status == "FULL" and pinned.delivered < free.delivered


def test_pinned_hours_count_for_their_own_entry():
    c = comp(gpu_target_hours=10, submission_utc="2026-11-09T00:00:00Z")
    a = simulate([c], NOW, pins=(Pin("a", NOW, NOW + timedelta(hours=5), 2),))["a"]
    assert a.delivered == pytest.approx(10)


def test_simulate_honours_not_before():
    c = comp(gpu_target_hours=4, not_before_utc="2026-11-08T00:00:00Z")
    a = simulate([c], NOW)["a"]
    assert a.first == parse_utc("2026-11-08T00:00:00Z")


def test_earlier_deadline_is_served_first():
    a = comp("a", gpu_target_hours=20, submission_utc="2026-11-08T00:00:00Z")
    b = comp("b", gpu_target_hours=20, submission_utc="2026-11-09T00:00:00Z")
    r = simulate([b, a], NOW)
    assert r["a"].first == NOW and r["b"].first > r["a"].first


def test_queue_entries_merges_strings_and_dicts():
    q = {"en_cola": [{"id": "x", "estado": "EN COLA"}], "pendiente_cierre": ["x", "y"]}
    e = queue_entries(q)
    assert e["x"]["estado"] == "EN COLA" and e["y"] == {"id": "y"}


def test_queue_entries_reads_the_raw_file_and_skips_final_states():
    raw = {"proyectos": {"a": {"estado": "EN COLA"}, "b": {"estado": "CERRADO"}, "c": {"estado": "ENTREGADO"}}}
    assert set(queue_entries(raw)) == {"a"}


def queue(**entry):
    return {"en_cola": [{"id": "a", "estado": "EN COLA", **entry}]}


def test_audit_flags_finished_entries_and_proposes_without_acting():
    report = audit([comp(stage="INELIGIBLE")], queue(cierre_utc="2026-11-30T00:00:00Z"), NOW)
    assert report["anomalies"]["finished_entry_still_queued"][0]["id"] == "a"
    assert report["mode"] == "observe"
    assert report["proposals"] == ["client.py cola cerrar a  # register stage INELIGIBLE"]


def test_audit_flags_deadline_mismatch_past_dates_and_unknown_entries():
    r = audit([comp()], queue(cierre_utc="2026-11-15T00:00:00Z"), NOW)
    assert "deadline_mismatch" in r["anomalies"]
    r = audit([comp()], queue(cierre_utc="2026-11-01T00:00:00Z"), NOW)
    assert "queue_date_already_past" in r["anomalies"]
    r = audit([], queue(), NOW)
    assert r["anomalies"]["queue_entry_not_in_register"] == [{"id": "a"}]


def test_audit_compares_the_queue_with_either_kind_of_deadline():
    item = comp(registration_utc="2026-11-08T00:00:00Z")
    r = audit([item], queue(cierre_utc="2026-11-08T00:00:00Z"), NOW)
    assert "deadline_mismatch" not in r["anomalies"]


def test_audit_ignores_the_registration_date_once_registered():
    item = comp(registration_utc="2026-11-08T00:00:00Z", registered=True)
    r = audit([item], queue(cierre_utc="2026-11-08T00:00:00Z"), NOW)
    assert "deadline_mismatch" in r["anomalies"]


def test_audit_reports_missing_dates_on_each_side():
    undated = comp(submission_utc=None, deadline_note="month only")
    assert "register_date_missing" in audit([undated], queue(cierre_utc="2026-11-08T00:00:00Z"), NOW)["anomalies"]
    assert "queue_date_missing" in audit([comp()], queue(), NOW)["anomalies"]
    assert "queue_date_missing" in audit([comp()], {"pendiente_cierre": ["a"]}, NOW)["anomalies"]


def test_audit_uses_aliases():
    item = comp("canonical", aliases=["a"])
    r = audit([item], queue(cierre_utc="2026-11-10T00:00:00Z"), NOW)
    assert "queue_entry_not_in_register" not in r["anomalies"]
    assert "active_entry_not_in_queue" not in r["anomalies"]


def test_audit_flags_public_repository_under_sharing_restrictions():
    item = comp(code_sharing="platform_only", repo="x", repo_visibility="public")
    assert "public_repo_while_sharing_restricted" in audit([item], {}, NOW)["anomalies"]


def test_audit_flags_missing_dedicated_repository():
    assert "no_dedicated_repository" in audit([comp()], {}, NOW)["anomalies"]


def test_public_rows_never_expose_overlay_or_private_repo_names():
    item = comp(
        repo="secret-repo", repo_visibility="private", gate="owner",
        next_action="private step", blocker="private blocker", rank="1/2",
    )
    text = json.dumps(public_rows([item]))
    for secret in ("secret-repo", "private step", "private blocker", "1/2", "gate"):
        assert secret not in text


def test_public_list_hides_overlay_and_private_list_shows_it():
    item = comp(gate="owner", next_action="firmar el formulario", repo="r", repo_visibility="private")
    assert "firmar" not in public_list([item], NOW)
    assert "private until release" in public_list([item], NOW)
    assert "firmar el formulario" in private_list([item], NOW)


def test_load_register_merges_overlay_and_rejects_unknown_fields(tmp_path):
    reg = tmp_path / "r.json"
    reg.write_text(json.dumps({"competitions": public_rows([comp()])}), encoding="utf-8")
    over = tmp_path / "o.json"
    over.write_text(json.dumps({"a": {"gate": "owner"}}), encoding="utf-8")
    assert load_register(reg, over)[0].gate == "owner"
    for bad in ({"typo": 1}, {"registered": True}, {"submission_utc": "2030-01-01T00:00:00Z"}):
        over.write_text(json.dumps({"a": bad}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_register(reg, over)


def test_cli_rejects_an_invalid_pin(tmp_path, capsys):
    reg = tmp_path / "r.json"
    reg.write_text(json.dumps({"competitions": public_rows([comp()])}), encoding="utf-8")
    pin = "a,2026-11-06T08:00:00Z,2026-11-06T10:00:00Z,-1"
    assert main(["--register", str(reg), "schedule", "--pin", pin]) == 2
    assert "invalid pin" in capsys.readouterr().err


def test_cli_validate_tick_and_failure(tmp_path, capsys):
    reg = tmp_path / "r.json"
    reg.write_text(json.dumps({"competitions": public_rows([comp()])}), encoding="utf-8")
    q = tmp_path / "q.json"
    q.write_text(json.dumps(queue(cierre_utc="2026-11-10T00:00:00Z")), encoding="utf-8")
    assert main(["--register", str(reg), "validate"]) == 0
    assert main(["--register", str(reg), "--now", "2026-11-06T08:00:00Z", "tick", "--queue", str(q)]) == 0
    assert '"mode": "observe"' in capsys.readouterr().out
    reg.write_text(json.dumps({"competitions": public_rows([comp(stage="NOPE")])}), encoding="utf-8")
    assert main(["--register", str(reg), "validate"]) == 1


def test_published_register_is_valid_and_public_safe():
    path = ROOT / "data" / "competitions.json"
    items = load_register(path)
    assert validate(items) == []
    text = path.read_text(encoding="utf-8")
    for fragment in ("mail.google.com", "D:/", "/mnt/", "next_action", "blocker", "gpu queue"):
        assert fragment.lower() not in text.lower()
