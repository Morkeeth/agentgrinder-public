import json
from agentgrinder.cli import main
from agentgrinder.native_sittings import sittings, choose, cursor_time
from agentgrinder.ingest import parse_codex_session


def resumed(tmp_path):
    path=tmp_path/'resumed.jsonl'
    rows=[{'type':'session_meta','timestamp':'2026-09-01T09:00:00Z','payload':{'cwd':str(tmp_path)}}]
    for stamp,kind in [('2026-09-01T09:30:00Z','user_message'),('2026-09-01T09:31:00Z','function_call'),('2026-09-04T10:00:00Z','user_message'),('2026-09-04T10:02:00Z','function_call')]:
        rows.append({'type':'event_msg' if kind=='user_message' else 'response_item','timestamp':stamp,'payload':{'type':kind,'message':'Go','call_id':stamp}})
    path.write_text('\n'.join(json.dumps(row) for row in rows))
    return path


def test_resumed_run_excludes_idle_days_and_session_creation(tmp_path):
    path=resumed(tmp_path)
    groups=sittings(path,'codex')
    assert len(groups)==2
    first=parse_codex_session(str(path),records=choose(groups,1))
    latest=parse_codex_session(str(path),records=choose(groups,-1))
    assert first['started']=='2026-09-01T09:30:00+00:00'
    assert first['duration_s']==60
    assert latest['duration_s']==120
    assert latest['turns_typed']==1
    assert latest['trace'][0]['second']==0
    assert latest['parser_version']=='codex-sittings-2026-09-05'


def test_auto_named_native_and_list_pick_coach_opt_out(tmp_path,capsys):
    path=resumed(tmp_path)
    assert main(['grind',str(path),'--list','--no-series'])==0
    listed=json.loads(capsys.readouterr().out)
    assert [row['sitting'] for row in listed]==[1,2]
    assert main(['grind',str(path),'--pick','1','--coach','none','--json','--no-series'])==0
    run=json.loads(capsys.readouterr().out)
    assert run['duration_s']==60
    assert 'coach_verdict' not in run


def test_cursor_timezone_is_explicit():
    stamp=cursor_time('<timestamp>Friday, Sep 04, 2026, 10:00 AM (UTC+02:00)</timestamp>')
    assert stamp.isoformat()=='2026-09-04T08:00:00+00:00'
    assert cursor_time('<timestamp>Friday, Sep 04, 2026, 10:00 AM (UTC-00:30)</timestamp>').isoformat()=='2026-09-04T10:30:00+00:00'
    assert cursor_time('<timestamp>Friday, Sep 04, 2026, 10:00 AM</timestamp>') is None


def test_flex_counts_sittings_and_does_not_invent_a_publication_count(tmp_path):
    from agentgrinder.flex import _native_stats, format_flex
    row = _native_stats([str(resumed(tmp_path))], 'codex')
    assert row['grinds'] == 2
    assert row['moving_s'] == 180
    text = format_flex([row])
    assert 'elapsed session time' in text
    assert 'ghost flex' not in text


def test_a2a_export_selects_codex_and_latest_sitting(tmp_path, monkeypatch, capsys):
    import agentgrinder.ingest as ingest
    path = resumed(tmp_path)
    monkeypatch.setattr(ingest, 'latest_codex_session', lambda: str(path))
    monkeypatch.setattr(ingest, 'latest_session', lambda: None)
    monkeypatch.setattr(ingest, 'detect_rig', lambda: {})
    assert main(['a2a', 'export', '--harness', 'codex']) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc['harness'] == 'codex'
    assert doc['duration_s'] == 120
    assert doc['turns_typed'] == 1
    assert doc['source']['ingest'] == 'native-codex-jsonl'


def test_codex_send_time_rows_do_not_hide_an_idle_gap(tmp_path):
    # Codex writes turn_context and task_started at the moment of sending, under 2 s before the
    # typed turn (measured 2 Oct 2026 over 346 real turns). Idle is the gap BEFORE those rows.
    path=tmp_path/'desktop.jsonl'
    rows=[{'type':'session_meta','timestamp':'2026-09-01T09:00:00Z','payload':{'cwd':str(tmp_path)}}]
    for day,hour in (('01','09'),('01','12')):
        rows.append({'type':'turn_context','timestamp':f'2026-09-{day}T{hour}:00:00Z','payload':{}})
        rows.append({'type':'event_msg','timestamp':f'2026-09-{day}T{hour}:00:00.500Z','payload':{'type':'task_started'}})
        rows.append({'type':'event_msg','timestamp':f'2026-09-{day}T{hour}:00:01Z','payload':{'type':'user_message','message':'Go'}})
        rows.append({'type':'response_item','timestamp':f'2026-09-{day}T{hour}:05:00Z','payload':{'type':'function_call','call_id':hour}})
    path.write_text('\n'.join(json.dumps(row) for row in rows))
    assert len(sittings(path,'codex'))==2
