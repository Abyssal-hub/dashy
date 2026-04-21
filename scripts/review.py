#!/usr/bin/env python3
"""
GStack Review V2 — Executable Review Script

Usage: python review.py <file_to_review>

Adversarial review that finds bugs that pass CI but fail in production.
"""

import sys
import re
import os
from pathlib import Path

# Severity levels
CRITICAL = "CRITICAL"
MAJOR = "MAJOR"
MINOR = "MINOR"

class Reviewer:
    """Staff Engineer persona — skeptical, thorough, constructive."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.issues = []
        self.asks = []
        self.infos = []
        self.lines = []
        self.content = ""

    def load(self):
        if not self.file_path.exists():
            print(f"❌ File not found: {self.file_path}")
            sys.exit(1)
        self.content = self.file_path.read_text()
        self.lines = self.content.split('\n')

    def check_xss(self):
        """Check for XSS vulnerabilities in innerHTML with unescaped user data."""
        # Find innerHTML assignments
        innerhtml_pattern = re.finditer(r'(\w+)\.innerHTML\s*=\s*`([^`]+)`', self.content)
        for match in innerhtml_pattern:
            var_name = match.group(1)
            template = match.group(2)
            line_num = self.content[:match.start()].count('\n') + 1

            # Check if template contains interpolation without escapeHtml
            interpolations = re.findall(r'\$\{([^}]+)\}', template)
            for interp in interpolations:
                if 'escapeHtml' not in interp and 'getIcon' not in interp:
                    self.issues.append({
                        'severity': CRITICAL,
                        'line': line_num,
                        'title': f'XSS via innerHTML — unescaped `{interp}`',
                        'description': f'Template literal interpolates `{interp}` into innerHTML without escaping. Malicious input can inject scripts.',
                        'fix': f'Wrap with escapeHtml(): `${{escapeHtml({interp})}}`'
                    })

    def check_inline_onclick(self):
        """Check for inline onclick handlers."""
        onclick_pattern = re.finditer(r'onclick="([^"]+)"', self.content)
        for match in onclick_pattern:
            handler = match.group(1)
            line_num = self.content[:match.start()].count('\n') + 1
            self.issues.append({
                'severity': MAJOR,
                'line': line_num,
                'title': f'Inline onclick handler: `{handler}`',
                'description': 'Inline event handlers violate frontend conventions. Use addEventListener() for separation of concerns and CSP compatibility.',
                'fix': f'Remove onclick, add ID to element, attach via JS: document.getElementById("...").addEventListener("click", {handler.split("(")[0]})'
            })

    def check_api_data_extraction(self):
        """Check for correct API response data extraction."""
        # Look for direct access to response.data.property
        bad_pattern = re.finditer(r'response\.data\.\w+', self.content)
        for match in bad_pattern:
            line_num = self.content[:match.start()].count('\n') + 1
            # Check if it's already extracted
            line = self.lines[line_num - 1]
            if 'const data = response.data' not in line and 'responseData.data' not in line:
                self.issues.append({
                    'severity': MAJOR,
                    'line': line_num,
                    'title': 'Incorrect API data access pattern',
                    'description': 'Accessing response.data.property directly instead of extracting response.data first.',
                    'fix': 'const data = response.data; // Extract first, then access data.property'
                })

    def check_accessibility(self):
        """Check for basic accessibility."""
        # Check for buttons without aria-label
        button_pattern = re.finditer(r'<button[^>]*>', self.content)
        for match in button_pattern:
            tag = match.group(0)
            line_num = self.content[:match.start()].count('\n') + 1
            if 'aria-label' not in tag and 'aria-labelledby' not in tag:
                # Skip if it has visible text
                if not re.search(r'<button[^>]*>[^<]+</button>', tag):
                    self.issues.append({
                        'severity': MINOR,
                        'line': line_num,
                        'title': 'Button missing aria-label',
                        'description': 'Icon-only buttons need aria-label for screen readers.',
                        'fix': 'Add aria-label="Descriptive text" to the button'
                    })

    def check_debounce(self):
        """Check for debounced input handlers."""
        if 'debounce' not in self.content and 'addEventListener' in self.content:
            self.issues.append({
                'severity': MINOR,
                'line': 1,
                'title': 'No debounce on input handlers',
                'description': 'Input handlers should be debounced (300ms) to prevent excessive API calls.',
                'fix': 'Implement debounce utility: const debounced = debounce(handler, 300)'
            })

    def check_error_handling(self):
        """Check for error boundaries and user-friendly errors."""
        if 'alert(' in self.content:
            self.issues.append({
                'severity': MINOR,
                'line': 1,
                'title': 'Using alert() for errors',
                'description': 'alert() is intrusive and bad UX. Use inline error messages or toast notifications.',
                'fix': 'Replace alert() with DOM-based error display'
            })

    def run_all_checks(self):
        self.check_xss()
        self.check_inline_onclick()
        self.check_api_data_extraction()
        self.check_accessibility()
        self.check_debounce()
        self.check_error_handling()

    def generate_report(self):
        report = []
        report.append("# Review Report")
        report.append(f"**File:** `{self.file_path}`")
        report.append(f"**Date:** {os.popen('date -Iseconds').read().strip()}")
        report.append(f"**Reviewer:** GStack Review V2 (Automated)")
        report.append("")

        # Summary
        critical = len([i for i in self.issues if i['severity'] == CRITICAL])
        major = len([i for i in self.issues if i['severity'] == MAJOR])
        minor = len([i for i in self.issues if i['severity'] == MINOR])

        report.append("## Summary")
        report.append(f"- **CRITICAL:** {critical}")
        report.append(f"- **MAJOR:** {major}")
        report.append(f"- **MINOR:** {minor}")
        report.append(f"- **Total:** {len(self.issues)}")
        report.append("")

        # Issues by severity
        if self.issues:
            report.append("## Issues Found")
            for issue in sorted(self.issues, key=lambda x: (x['severity'] != CRITICAL, x['severity'] != MAJOR, x['line'])):
                report.append(f"### [{issue['severity']}] Line {issue['line']}: {issue['title']}")
                report.append(f"- **Description:** {issue['description']}")
                report.append(f"- **Fix:** {issue['fix']}")
                report.append("")

        # Ask section
        if self.asks:
            report.append("## [ASK] Human Decision Required")
            for ask in self.asks:
                report.append(f"- {ask}")
            report.append("")

        # Info section
        if self.infos:
            report.append("## [INFO] Observations")
            for info in self.infos:
                report.append(f"- {info}")
            report.append("")

        # Recommendation
        if critical > 0:
            report.append("## Recommendation: 🔴 FIX_THEN_SHIP")
            report.append("Critical issues must be resolved before deployment.")
        elif major > 0:
            report.append("## Recommendation: 🟡 FIX_THEN_SHIP")
            report.append("Major issues should be fixed before deployment.")
        elif minor > 0:
            report.append("## Recommendation: 🟢 SHIP_WITH_NOTES")
            report.append("Minor issues noted, can be addressed in next iteration.")
        else:
            report.append("## Recommendation: 🟢 SHIP")
            report.append("No issues found. Ready for deployment.")

        return '\n'.join(report)

def main():
    if len(sys.argv) < 2:
        print("Usage: python review.py <file_to_review>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"🔍 Reviewing: {file_path}")

    reviewer = Reviewer(file_path)
    reviewer.load()
    reviewer.run_all_checks()

    report = reviewer.generate_report()
    print(report)

    # Save report
    output_path = Path(file_path).parent / f"review-{Path(file_path).name}.md"
    output_path.write_text(report)
    print(f"\n💾 Report saved to: {output_path}")

if __name__ == '__main__':
    main()
