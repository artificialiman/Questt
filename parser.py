#!/usr/bin/env python3
"""
Question Parser for 100Days-to-UTME
Parses .txt question files into JSON format for HTML embedding
Includes flexible subject name detection failsafe
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Subject keyword mapping (case-insensitive)
SUBJECT_KEYWORDS = {
    'physics': ['physics', 'phy'],
    'mathematics': ['mathematics', 'math', 'maths'],
    'english': ['english', 'eng'],
    'chemistry': ['chemistry', 'chem'],
    'biology': ['biology', 'bio'],
    'literature': ['literature', 'lit'],
    'government': ['government', 'govt'],
    'crs': ['crs', 'christian', 'religious'],
    'accounting': ['accounting', 'acct'],
    'commerce': ['commerce', 'comm'],
    'economics': ['economics', 'econ', 'eco']
}


def detect_subject(filename: str) -> Optional[str]:
    filename_lower = filename.lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return subject.capitalize()
    return None


def parse_question_file(file_path: Path) -> Tuple[List[Dict], str, List[str]]:
    questions = []
    errors = []

    subject = detect_subject(file_path.name)
    if not subject:
        errors.append(f"Could not detect subject from filename: {file_path.name}")
        subject = file_path.stem.replace('_', ' ').replace('-', ' ').title()

    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        errors.append(f"File encoding error - not UTF-8: {file_path.name}")
        return [], subject, errors
    except Exception as e:
        errors.append(f"Failed to read file: {str(e)}")
        return [], subject, errors

    content = content.replace('\r\n', '\n')
    question_blocks = re.split(r'\n\s*\n+', content.strip())

    # FIX: Skip header/non-question blocks (e.g. "JAMB MATHEMATICS - EXCEPTIONAL QUESTIONS (1-35)")
    question_blocks = [b for b in question_blocks if re.match(r'^\d+\.', b.strip())]

    for block_idx, block in enumerate(question_blocks):
        block = block.strip()
        if not block:
            continue

        try:
            question_data = parse_question_block(block, block_idx + 1)
            if question_data:
                questions.append(question_data)
            else:
                errors.append(f"Block {block_idx + 1}: Failed to parse question")
        except Exception as e:
            errors.append(f"Block {block_idx + 1}: {str(e)}")

    return questions, subject, errors


def parse_question_block(block: str, expected_num: int) -> Optional[Dict]:
    lines = [line.strip() for line in block.split('\n') if line.strip()]

    if len(lines) < 6:
        return None

    question_match = re.match(r'^(\d+)\.\s*(.+)$', lines[0])
    if not question_match:
        return None

    question_num = int(question_match.group(1))
    question_text = question_match.group(2).strip()

    options = {}
    option_pattern = re.compile(r'^([A-D])\.\s*(.+)$', re.IGNORECASE)

    for line in lines[1:]:
        option_match = option_pattern.match(line)
        if option_match:
            option_label = option_match.group(1).upper()
            option_text = option_match.group(2).strip()
            options[option_label] = option_text

    if len(options) != 4 or not all(opt in options for opt in ['A', 'B', 'C', 'D']):
        return None

    answer = None
    answer_pattern = re.compile(r'^Answer:\s*([A-D])$', re.IGNORECASE)

    for line in lines:
        answer_match = answer_pattern.match(line)
        if answer_match:
            answer = answer_match.group(1).upper()
            break

    if not answer or answer not in ['A', 'B', 'C', 'D']:
        return None

    return {
        'id': question_num,
        'text': question_text,
        'optionA': options['A'],
        'optionB': options['B'],
        'optionC': options['C'],
        'optionD': options['D'],
        'answer': answer
    }


def validate_questions(questions: List[Dict], expected_count: int = 35) -> List[str]:
    errors = []

    if len(questions) != expected_count:
        errors.append(f"Expected {expected_count} questions, got {len(questions)}")

    question_ids = [q['id'] for q in questions]
    if len(question_ids) != len(set(question_ids)):
        duplicates = [qid for qid in question_ids if question_ids.count(qid) > 1]
        errors.append(f"Duplicate question IDs: {set(duplicates)}")

    expected_ids = list(range(1, len(questions) + 1))
    actual_ids = sorted(question_ids)
    if actual_ids != expected_ids:
        missing = set(expected_ids) - set(actual_ids)
        if missing:
            errors.append(f"Missing question numbers: {sorted(missing)}")

    for q in questions:
        q_id = q['id']
        if not q['text']:
            errors.append(f"Question {q_id}: Empty question text")
        for opt in ['A', 'B', 'C', 'D']:
            if not q.get(f'option{opt}'):
                errors.append(f"Question {q_id}: Empty option {opt}")
        if q['answer'] not in ['A', 'B', 'C', 'D']:
            errors.append(f"Question {q_id}: Invalid answer '{q['answer']}'")

    return errors


def escape_html(text: str) -> str:
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    return text


def sanitize_questions(questions: List[Dict]) -> List[Dict]:
    sanitized = []
    for q in questions:
        sanitized.append({
            'id': q['id'],
            'text': escape_html(q['text']),
            'optionA': escape_html(q['optionA']),
            'optionB': escape_html(q['optionB']),
            'optionC': escape_html(q['optionC']),
            'optionD': escape_html(q['optionD']),
            'answer': q['answer']
        })
    return sanitized


def parse_file(file_path: str) -> Dict:
    path = Path(file_path)

    if not path.exists():
        return {
            'success': False,
            'subject': None,
            'questions': [],
            'question_count': 0,
            'errors': [f"File not found: {file_path}"],
            'filename': path.name
        }

    questions, subject, parse_errors = parse_question_file(path)
    validation_errors = validate_questions(questions) if questions else []
    all_errors = parse_errors + validation_errors

    if questions and not all_errors:
        questions = sanitize_questions(questions)

    return {
        'success': len(all_errors) == 0,
        'subject': subject,
        'questions': questions,
        'question_count': len(questions),
        'errors': all_errors,
        'filename': path.name
    }


def batch_parse(file_paths: List[str]) -> Dict[str, Dict]:
    results = {}
    for file_path in file_paths:
        result = parse_file(file_path)
        results[result['filename']] = result
    return results


if __name__ == '__main__':
    args = sys.argv[1:]

    # FIX: --json flag outputs pure JSON only, safe for piping into jq in GitHub Actions
    json_mode = '--json' in args
    if json_mode:
        args.remove('--json')

    if not args:
        print("Usage: python parser.py [--json] <question_file.txt> [additional_files...]")
        print("\nExamples:")
        print("  python parser.py JAMB_Physics_Q1-35.txt")
        print("  python parser.py --json JAMB_Physics_Q1-35.txt   # pure JSON, safe for scripts")
        print("  python parser.py physics.txt math.txt english.txt")
        sys.exit(1)

    if len(args) == 1:
        result = parse_file(args[0])

        if json_mode:
            # Pure JSON only — no headers, no decoration
            print(json.dumps(result))
        else:
            # Human-readable output
            print(f"\n{'='*60}")
            print(f"Parsing: {result['filename']}")
            print(f"{'='*60}")
            print(f"Subject: {result['subject']}")
            print(f"Questions Parsed: {result['question_count']}")
            print(f"Success: {result['success']}")

            if result['errors']:
                print(f"\nErrors ({len(result['errors'])}):")
                for error in result['errors']:
                    print(f"  ❌ {error}")
            else:
                print("\n✅ All validations passed!")
                if result['questions']:
                    q = result['questions'][0]
                    print(f"\nSample Question:")
                    print(f"  {q['id']}. {q['text']}")
                    print(f"     A. {q['optionA']}")
                    print(f"     B. {q['optionB']}")
                    print(f"     C. {q['optionC']}")
                    print(f"     D. {q['optionD']}")
                    print(f"     Answer: {q['answer']}")

            print(f"\n{'='*60}")
            print("JSON Output:")
            print(f"{'='*60}")
            print(json.dumps(result, indent=2))

    else:
        # Batch mode
        results = batch_parse(args)

        if json_mode:
            print(json.dumps(results))
        else:
            print(f"\n{'='*60}")
            print(f"Batch Parsing: {len(args)} files")
            print(f"{'='*60}\n")

            for filename, result in results.items():
                status = "✅" if result['success'] else "❌"
                print(f"{status} {filename}")
                print(f"   Subject: {result['subject']}")
                print(f"   Questions: {result['question_count']}")
                if result['errors']:
                    print(f"   Errors: {len(result['errors'])}")
                    for error in result['errors'][:3]:
                        print(f"      - {error}")
                    if len(result['errors']) > 3:
                        print(f"      ... and {len(result['errors']) - 3} more")
                print()

            successful = sum(1 for r in results.values() if r['success'])
            print(f"{'='*60}")
            print(f"Summary: {successful}/{len(results)} files parsed successfully")
            print(f"{'='*60}\n")

            output_file = "batch_parse_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"Full results saved to: {output_file}")
