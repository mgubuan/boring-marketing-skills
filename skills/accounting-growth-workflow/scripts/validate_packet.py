"""Offline research-packet validation. Never sends, imports or mutates data."""
import argparse
import datetime
import json
from pathlib import Path


def validate(record):
    errors = []
    if not isinstance(record, dict):
        return ['record must be an object']
    for field in ('id', 'company', 'domain', 'status', 'relationship', 'duplicate', 'ai_team', 'draft_state'):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f'{field} is required')
    status = record.get('status')
    if status not in ('hold', 'disqualified', 'qualified_for_draft'):
        errors.append('invalid status')
    if record.get('ai_team') not in ('confirmed_team', 'competing_provider', 'no_evidence_found', 'unknown'):
        errors.append('invalid ai_team evidence class')
    if record.get('relationship') not in ('non_client', 'client', 'unknown'):
        errors.append('invalid relationship')
    if record.get('duplicate') not in ('clear', 'duplicate', 'unchecked'):
        errors.append('invalid duplicate state')
    if type(record.get('excluded')) is not bool:
        errors.append('excluded must be a boolean')
    if record.get('draft_state') not in ('brief_only', 'pending_review', 'approved', 'rejected'):
        errors.append('invalid draft state')
    disqualified = (record.get('excluded') is True or record.get('relationship') == 'client'
                    or record.get('ai_team') in ('confirmed_team', 'competing_provider'))
    if disqualified and status != 'disqualified':
        errors.append('disqualifying evidence cannot be overridden')
    if record.get('ai_team') in ('confirmed_team', 'competing_provider') and not record.get('ai_team_sources'):
        errors.append('AI exclusion needs sources')
    if status == 'qualified_for_draft':
        if record.get('relationship') != 'non_client' or record.get('duplicate') != 'clear':
            errors.append('relationship and dedupe must be resolved')
        if record.get('ai_team') != 'no_evidence_found':
            errors.append('AI screen must be completed')
        if record.get('research_complete') is not True or not record.get('fit_hypothesis') or not record.get('sources'):
            errors.append('complete sourced enrichment and fit hypothesis required')
        contact = record.get('contact', {})
        if not isinstance(contact, dict) or contact.get('route') != 'email' or contact.get('verification') != 'official_source' or not contact.get('value'):
            errors.append('email draft requires official-source recipient')
        try:
            datetime.date.fromisoformat(record.get('checked_at', ''))
        except (ValueError, TypeError):
            errors.append('checked_at requires ISO date')
        if record.get('draft_state') == 'rejected':
            errors.append('rejected draft cannot enter draft-ready queue')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.packet.read_text())
    except (OSError, ValueError):
        print('Packet unreadable or invalid JSON; no data changed.')
        return 2
    if not isinstance(data, list):
        print('Packet must be a JSON list; no data changed.')
        return 2
    issues = [(i + 1, validate(row)) for i, row in enumerate(data)]
    for number, errors in issues:
        for error in errors:
            print(f'Record {number}: {error}')
    print(f'Checked {len(data)} research records. This is not send approval.')
    return int(any(errors for _, errors in issues))


if __name__ == '__main__':
    raise SystemExit(main())
