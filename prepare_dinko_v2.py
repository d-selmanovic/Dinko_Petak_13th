#!/usr/bin/env python3
"""Build per-call context from editable Excel rules and a candidate export.

Requires openpyxl. Reads local files only. Does not start calls or write to CRM.
"""

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

from openpyxl import load_workbook


def read_table(book, sheet_name, key_header):
    if sheet_name not in book.sheetnames:
        return [], []
    iterator = book[sheet_name].iter_rows(values_only=True)
    for row in iterator:
        headers = [str(value).strip() if value is not None else '' for value in row]
        if key_header in headers:
            populated = [header for header in headers if header]
            if len(populated) != len(set(populated)):
                raise ValueError(f'Doppelte Spaltenüberschrift in {sheet_name}')
            return headers, [
                dict(zip(headers, values))
                for values in iterator if any(value is not None for value in values)
            ]
    return [], []


def identifier(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip() if value is not None else ''


def present(value):
    return value is not None and value != '' and value != []


def date_value(value):
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    if not present(value):
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace('Z', '+00:00')).date().isoformat()
    except ValueError:
        pass
    for pattern in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y', '%d.%m.%Y.'):
        try:
            return datetime.strptime(str(value).strip(), pattern).date().isoformat()
        except ValueError:
            continue
    return None


def licence_categories(value):
    allowed = {'AM', 'A1', 'A2', 'A', 'B1', 'B', 'BE', 'C1', 'C1E', 'C', 'CE', 'D1', 'D1E', 'D', 'DE', 'F', 'G'}
    parts = re.split(r'[,;/\s]+', str(value or '').upper())
    return sorted({part for part in parts if part in allowed})


def build_context(rules_path, candidates_path, candidate_id, as_of, prefetch=None):
    rules_book = load_workbook(rules_path, read_only=True, data_only=True)
    source_book = load_workbook(candidates_path, read_only=True, data_only=True)
    try:
        _, mappings = read_table(rules_book, 'Datenfelder', 'Feld-ID')
        _, questions = read_table(rules_book, 'Fragen', 'Feld-ID')
        _, settings = read_table(rules_book, 'Casting', 'Schlüssel')
        if not mappings or not questions or not settings:
            raise ValueError('Die Steuerung braucht Datenfelder, Fragen und Casting mit ihren Spaltenüberschriften.')
        for rows, key in ((mappings, 'Feld-ID'), (questions, 'Feld-ID'), (settings, 'Schlüssel')):
            keys = [identifier(row.get(key)) for row in rows]
            if '' in keys or len(keys) != len(set(keys)):
                raise ValueError(f'Leere oder doppelte Kennung in {key}')
        id_mapping = next((row for row in mappings if row['Feld-ID'] == 'candidate_id'), None)
        if id_mapping is None:
            raise ValueError('Zuordnung candidate_id fehlt.')
        header = id_mapping['Quellspalte']
        _, candidates = read_table(source_book, id_mapping['Quellblatt'], header)
        matches = [row for row in candidates if identifier(row.get(header)) == identifier(candidate_id)]
        if len(matches) != 1:
            raise ValueError('Kandidaten-ID muss im ausgewählten Quellblatt genau einmal vorkommen.')
        cache = {id_mapping['Quellblatt']: (list(matches[0]), candidates)}
        fields, raw_codes, warnings = {}, {}, []
        for mapping in mappings:
            field = mapping['Feld-ID']
            sheet = mapping['Quellblatt']
            column = mapping['Quellspalte']
            key = mapping['Schlüsselspalte']
            kind = mapping['Datentyp']
            if kind not in {'Text', 'Datum', 'Führerschein', 'Klassen', 'Code', 'Liste'}:
                raise ValueError(f'Unbekannter Datentyp für {field}: {kind}')
            if sheet not in cache:
                cache[sheet] = read_table(source_book, sheet, key)
            headers, rows = cache[sheet]
            if key not in headers or column not in headers:
                warnings.append(f'Quelle fehlt für {field}: {sheet}/{column}')
                fields[field] = None
                continue
            selected = [row for row in rows if identifier(row.get(key)) == identifier(candidate_id)]
            values = [row.get(column) for row in selected if present(row.get(column))]
            if kind != 'Liste' and len(selected) > 1:
                raise ValueError(f'Mehrdeutige Quelle für {field}')
            value = values[0] if values else None
            if kind == 'Code':
                raw_codes[field] = value
                continue
            if kind == 'Liste':
                value = list(dict.fromkeys(str(item).strip() for item in values))
            elif kind == 'Datum':
                normalized = date_value(value)
                if present(value) and normalized is None:
                    warnings.append(f'Ungültiges Datum für {field}')
                value = normalized
            fields[field] = value

        declared = fields.get('driving_licence')
        categories = sorted(set(licence_categories(declared) + licence_categories(fields.get('driving_categories'))))
        answer = str(declared or '').strip().casefold()
        if answer in {'ne', 'nein', 'no'}:
            fields['driving_licence'] = False if not categories else None
            if categories:
                warnings.append('Führerschein verneint, aber Klassen vorhanden. Im Gespräch klären.')
        elif answer in {'da', 'ja', 'yes'} or categories:
            fields['driving_licence'] = True
        else:
            fields['driving_licence'] = None
        fields['driving_categories'] = categories
        fields['candidate_id'] = identifier(candidate_id)

        if prefetch:
            if identifier(prefetch.get('candidate_id')) != identifier(candidate_id):
                raise ValueError('Prefetch und ausgewählter Kandidat stimmen nicht überein.')
            updates = prefetch.get('fields', {})
            if not isinstance(updates, dict) or 'candidate_id' in updates:
                raise ValueError('Prefetch-Felder müssen ein Objekt ohne candidate_id sein.')
            fields.update(updates)
        if present(fields.get('birth_date')):
            normalized_birth = date_value(fields['birth_date'])
            if normalized_birth is None or date.fromisoformat(normalized_birth) > as_of:
                fields['birth_date'] = None
                warnings.append('Geburtsdatum ist ungültig oder liegt in der Zukunft.')
            else:
                fields['birth_date'] = normalized_birth
                birth = date.fromisoformat(normalized_birth)
                calculated_age = as_of.year - birth.year - ((as_of.month, as_of.day) < (birth.month, birth.day))
                if not prefetch or 'age_at_call' not in prefetch.get('fields', {}):
                    fields['age_at_call'] = calculated_age
                elif present(fields.get('age_at_call')) and fields['age_at_call'] != calculated_age:
                    warnings.append('Aktuelle Altersangabe weicht vom vorhandenen Geburtsdatum ab. Geburtsdatum bleibt ungeklärt.')

        rules = []
        for row in questions:
            if row.get('Aktiv') not in {'Ja', 'Nein'}:
                raise ValueError(f'Ungültiger Aktiv-Wert bei {row["Feld-ID"]}')
            if row['Aktiv'] == 'Nein':
                continue
            mode, condition = row.get('Abfragen'), row.get('Bedingung')
            if mode not in {'Bei fehlender Angabe', 'Bestätigen'}:
                raise ValueError(f'Ungültiger Abfragemodus bei {row["Feld-ID"]}')
            if condition not in {'Immer', 'Führerschein vorhanden', 'Erfahrung gering oder unklar'}:
                raise ValueError(f'Unbekannte Bedingung bei {row["Feld-ID"]}')
            if not present(row.get('Frage auf Bosnisch')):
                raise ValueError(f'Fragetext fehlt bei {row["Feld-ID"]}')
            order = float(row['Reihenfolge'])
            field = row['Feld-ID']
            state = 'known' if present(fields.get(field)) and mode != 'Bestätigen' else 'open'
            if condition == 'Führerschein vorhanden' and fields.get('driving_licence') is False:
                state = 'not_applicable'
            elif state == 'open' and condition != 'Immer':
                state = 'conditional'
            rules.append({'field_id':field,'order':order,'mode':mode,'condition':condition,
                          'question_bs':row['Frage auf Bosnisch'],'note':row.get('Hinweis'), 'initial_state':state})
        campaign, unresolved = {}, []
        for setting in settings:
            key, value = setting['Schlüssel'], setting.get('Wert')
            if setting.get('Status') not in {'Bestätigt', 'Offen'}:
                raise ValueError(f'Ungültiger Status für {key}')
            if setting['Status'] == 'Bestätigt' and present(value):
                campaign[key] = value.isoformat()[:10] if isinstance(value,(date,datetime)) else value
            else:
                unresolved.append({'key':key,'note':setting.get('Erläuterung')})
        return {'schema_version':2,'as_of':as_of.isoformat(),
                'source':{'kind':'local_export','primary_key':identifier(candidate_id),'live_read_verified':False},
                'candidate':fields,'uninterpreted_codes':raw_codes,
                'questions':sorted(rules,key=lambda rule:rule['order']),
                'campaign':campaign,'open_campaign_details':unresolved,'data_warnings':warnings,
                'team_review':{'invitation_approved':False,'reason':'Keine personenbezogene Teamfreigabe übergeben.'}}
    finally:
        rules_book.close()
        source_book.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rules', type=Path, required=True)
    parser.add_argument('--candidates', type=Path, required=True)
    parser.add_argument('--candidate-id', required=True)
    parser.add_argument('--as-of', type=date.fromisoformat,
                        default=datetime.now(ZoneInfo('Europe/Sarajevo')).date())
    parser.add_argument('--prefetch', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prefetch = json.loads(args.prefetch.read_text()) if args.prefetch else None
    result = build_context(args.rules,args.candidates,args.candidate_id,args.as_of,prefetch)
    # Exclusive creation prevents accidentally replacing another call's context.
    with args.output.open('x',encoding='utf-8') as output:
        json.dump(result,output,ensure_ascii=False,indent=2)
        output.write('\n')
    args.output.chmod(0o600)
    print(f'Kontext erstellt. Aktive Regeln: {len(result["questions"])}. Datenhinweise: {len(result["data_warnings"])}.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(f'Vorbereitung fehlgeschlagen: {error}',file=sys.stderr)
        sys.exit(1)
