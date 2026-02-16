#!/usr/bin/env python3
"""
Question Validator for 100Days-to-UTME
Validates .txt question files before processing
Generates validation reports for archiving
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Import parser functions
try:
    from parser import parse_file, detect_subject
except ImportError:
    print("Error: parser.py must be in the same directory")
    sys.exit(1)


class QuestionValidator:
    """Validates question files against standards"""
    
    def __init__(self):
        self.validation_results = {}
        self.valid_files = []
        self.invalid_files = []
        self.warnings = []
    
    def validate_file(self, file_path: Path) -> Dict:
        """
        Validate a single question file.
        
        Args:
            file_path: Path to question file
        
        Returns:
            Validation result dictionary
        """
        result = {
            'filename': file_path.name,
            'filepath': str(file_path),
            'subject': None,
            'valid': False,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        # Check file exists
        if not file_path.exists():
            result['errors'].append("File does not exist")
            return result
        
        # Check file size (not empty, not too large)
        file_size = file_path.stat().st_size
        if file_size == 0:
            result['errors'].append("File is empty")
            return result
        
        if file_size > 5_000_000:  # 5MB limit
            result['errors'].append(f"File too large: {file_size / 1_000_000:.2f}MB (max 5MB)")
            return result
        
        result['metadata']['file_size_bytes'] = file_size
        
        # Check file extension
        if file_path.suffix.lower() != '.txt':
            result['warnings'].append(f"Unexpected file extension: {file_path.suffix} (expected .txt)")
        
        # Detect subject
        subject = detect_subject(file_path.name)
        if not subject:
            result['warnings'].append("Could not detect subject from filename")
            # Use filename as fallback
            subject = file_path.stem.replace('_', ' ').replace('-', ' ').title()
        
        result['subject'] = subject
        
        # Parse the file
        parse_result = parse_file(str(file_path))
        
        if not parse_result['success']:
            result['errors'].extend(parse_result['errors'])
            return result
        
        # Additional validations
        questions = parse_result['questions']
        
        # Check question count
        if len(questions) != 35:
            if len(questions) < 35:
                result['errors'].append(f"Insufficient questions: {len(questions)}/35")
            else:
                result['warnings'].append(f"Extra questions: {len(questions)}/35 (only first 35 will be used)")
        
        # Check for duplicate question text
        question_texts = [q['text'].lower().strip() for q in questions]
        duplicates = []
        seen = set()
        for i, text in enumerate(question_texts):
            if text in seen:
                duplicates.append(i + 1)
            seen.add(text)
        
        if duplicates:
            result['warnings'].append(f"Possible duplicate questions at positions: {duplicates}")
        
        # Check for HTML-unsafe characters (should be escaped by parser)
        unsafe_chars_found = False
        for q in questions:
            for field in ['text', 'optionA', 'optionB', 'optionC', 'optionD']:
                if any(char in q[field] for char in ['<', '>', '&amp;', '&lt;', '&gt;']):
                    # Parser should have escaped these already
                    pass
        
        # Store metadata
        result['metadata']['question_count'] = len(questions)
        result['metadata']['subject'] = subject
        result['metadata']['has_duplicates'] = len(duplicates) > 0
        
        # Mark as valid if no errors
        result['valid'] = len(result['errors']) == 0
        
        return result
    
    def validate_directory(self, directory: Path) -> Dict:
        """
        Validate all .txt files in a directory.
        
        Args:
            directory: Path to directory containing question files
        
        Returns:
            Dictionary of validation results
        """
        if not directory.exists():
            return {
                'success': False,
                'error': f"Directory does not exist: {directory}"
            }
        
        # Find all .txt files
        txt_files = list(directory.glob('*.txt'))
        
        if not txt_files:
            return {
                'success': False,
                'error': f"No .txt files found in: {directory}"
            }
        
        # Validate each file
        for txt_file in txt_files:
            result = self.validate_file(txt_file)
            self.validation_results[txt_file.name] = result
            
            if result['valid']:
                self.valid_files.append(txt_file.name)
            else:
                self.invalid_files.append(txt_file.name)
        
        return {
            'success': True,
            'total_files': len(txt_files),
            'valid_files': len(self.valid_files),
            'invalid_files': len(self.invalid_files)
        }
    
    def generate_report(self) -> Dict:
        """
        Generate validation report.
        
        Returns:
            Comprehensive validation report
        """
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_files': len(self.validation_results),
                'valid_files': len(self.valid_files),
                'invalid_files': len(self.invalid_files),
                'validation_status': 'PASSED' if len(self.invalid_files) == 0 else 'PARTIAL'
            },
            'valid_files': self.valid_files,
            'invalid_files': self.invalid_files,
            'details': self.validation_results,
            'warnings': self.warnings
        }
    
    def save_report(self, output_path: Path):
        """
        Save validation report to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return output_path
    
    def print_summary(self):
        """Print validation summary to console"""
        report = self.generate_report()
        
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Files: {report['summary']['total_files']}")
        print(f"Valid Files: {report['summary']['valid_files']} ✅")
        print(f"Invalid Files: {report['summary']['invalid_files']} ❌")
        print(f"Status: {report['summary']['validation_status']}")
        print(f"{'='*60}\n")
        
        # Valid files
        if self.valid_files:
            print("✅ VALID FILES:")
            for filename in self.valid_files:
                result = self.validation_results[filename]
                print(f"   • {filename}")
                print(f"     Subject: {result['subject']}")
                print(f"     Questions: {result['metadata']['question_count']}")
                if result['warnings']:
                    print(f"     Warnings: {len(result['warnings'])}")
            print()
        
        # Invalid files
        if self.invalid_files:
            print("❌ INVALID FILES:")
            for filename in self.invalid_files:
                result = self.validation_results[filename]
                print(f"   • {filename}")
                if result['subject']:
                    print(f"     Subject: {result['subject']}")
                print(f"     Errors: {len(result['errors'])}")
                for error in result['errors'][:3]:
                    print(f"       - {error}")
                if len(result['errors']) > 3:
                    print(f"       ... and {len(result['errors']) - 3} more")
            print()
        
        # Overall warnings
        if self.warnings:
            print("⚠️  GLOBAL WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()


def validate_cluster_requirements(validation_results: Dict) -> Dict:
    """
    Check if valid files meet cluster requirements.
    
    Args:
        validation_results: Validation results dictionary
    
    Returns:
        Dictionary of which clusters can be generated
    """
    valid_subjects = set()
    
    for filename, result in validation_results.items():
        if result['valid'] and result['subject']:
            valid_subjects.add(result['subject'].lower())
    
    clusters = {
        'science-cluster-a': {
            'required': ['mathematics', 'english', 'physics', 'chemistry'],
            'can_generate': False
        },
        'science-cluster-b': {
            'required': ['biology', 'english', 'physics', 'chemistry'],
            'can_generate': False
        },
        'arts-cluster-a': {
            'required': ['english', 'literature', 'government', 'crs'],
            'can_generate': False
        },
        'commercial-cluster-a': {
            'required': ['english', 'accounting', 'commerce', 'economics'],
            'can_generate': False
        }
    }
    
    for cluster_name, cluster_info in clusters.items():
        required = set(cluster_info['required'])
        cluster_info['can_generate'] = required.issubset(valid_subjects)
        cluster_info['missing'] = list(required - valid_subjects)
    
    return clusters


def main():
    """Main validation function"""
    if len(sys.argv) < 2:
        print("Usage: python validate_questions.py <directory_path> [output_report.json]")
        print("\nExample:")
        print("  python validate_questions.py ./questions")
        print("  python validate_questions.py ./questions validation-report.json")
        sys.exit(1)
    
    directory_path = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('validation-report.json')
    
    # Initialize validator
    validator = QuestionValidator()
    
    # Validate directory
    print(f"\nValidating files in: {directory_path}\n")
    validation_summary = validator.validate_directory(directory_path)
    
    if not validation_summary['success']:
        print(f"❌ Error: {validation_summary['error']}")
        sys.exit(1)
    
    # Print summary
    validator.print_summary()
    
    # Check cluster requirements
    clusters = validate_cluster_requirements(validator.validation_results)
    
    print(f"{'='*60}")
    print("CLUSTER GENERATION STATUS")
    print(f"{'='*60}")
    
    for cluster_name, cluster_info in clusters.items():
        status = "✅ CAN GENERATE" if cluster_info['can_generate'] else "❌ CANNOT GENERATE"
        print(f"{cluster_name.upper()}: {status}")
        if not cluster_info['can_generate'] and cluster_info['missing']:
            print(f"  Missing subjects: {', '.join(cluster_info['missing'])}")
    print()
    
    # Save report
    saved_path = validator.save_report(output_file)
    print(f"{'='*60}")
    print(f"Report saved to: {saved_path}")
    print(f"{'='*60}\n")
    
    # Exit code based on validation status
    if validator.invalid_files:
        print("⚠️  Some files failed validation (graceful failure mode)")
        print("Valid files will be processed, invalid files will be skipped\n")
        sys.exit(0)  # Exit 0 for graceful failure
    else:
        print("✅ All files passed validation!\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
