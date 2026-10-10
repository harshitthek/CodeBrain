import os
import sys
import json
import asyncio
import yaml
from django.core.management.base import BaseCommand, CommandError
from apps.ai_agents.iface_case_generator.runner import APITestRunner
from apps.ai_agents.iface_case_generator.views import _normalize_case_to_flat_contract
from apps.ai_agents.iface_case_generator.exporters import generate_pytest_script
from apps.core.exporters.junit_exporter import JUnitExporter


class Command(BaseCommand):
    help = "Headless CI/CD test runner for CodeBrain API test suites."

    def add_arguments(self, parser):
        parser.add_argument(
            '--spec-file',
            type=str,
            required=True,
            help='Path to API specification or test suite JSON/YAML file.'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            required=True,
            help='Target base URL (e.g. https://api.staging.example.com).'
        )
        parser.add_argument(
            '--output-junit',
            type=str,
            default=None,
            help='Optional destination file path for JUnit XML report (e.g. test-results.xml).'
        )
        parser.add_argument(
            '--output-pytest',
            type=str,
            default=None,
            help='Optional destination file path for standalone Pytest script.'
        )
        parser.add_argument(
            '--min-pass-rate',
            type=float,
            default=100.0,
            help='Minimum required pass rate percentage (default: 100.0).'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=5,
            help='Maximum concurrent HTTP requests (default: 5).'
        )

    def handle(self, *args, **options):
        spec_file = os.path.abspath(options['spec_file'])
        base_url = options['base_url'].strip()
        min_pass_rate = float(options['min_pass_rate'])
        concurrency = int(options['concurrency'])
        output_junit = options['output_junit']
        output_pytest = options['output_pytest']

        if not os.path.exists(spec_file):
            raise CommandError(f"Specification file not found: {spec_file}")

        self.stdout.write(self.style.NOTICE(f"Loading specification: {spec_file}"))
        self.stdout.write(self.style.NOTICE(f"Target Base URL: {base_url}"))

        # Load specification file in-memory without modifying source or creating .orig backups
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            if spec_file.lower().endswith(('.yaml', '.yml')):
                spec_data = yaml.safe_load(raw_content) or {}
            else:
                spec_data = json.loads(raw_content)
        except Exception as e:
            raise CommandError(f"Failed to parse specification file {spec_file}: {e}")

        test_cases = []
        if isinstance(spec_data, list):
            test_cases = [_normalize_case_to_flat_contract(c) for c in spec_data if isinstance(c, dict)]
        elif isinstance(spec_data, dict):
            if 'test_cases' in spec_data and isinstance(spec_data['test_cases'], list):
                test_cases = [_normalize_case_to_flat_contract(c) for c in spec_data['test_cases'] if isinstance(c, dict)]
            elif 'apiDefinitions' in spec_data:
                for api in spec_data.get('apiDefinitions', []):
                    if not isinstance(api, dict):
                        continue
                    case_list = api.get('apiTestCaseList', [])
                    if case_list:
                        for case in case_list:
                            if isinstance(case, dict):
                                test_cases.append(_normalize_case_to_flat_contract(case, api_defaults=api))
                    else:
                        synthesized = {
                            "name": api.get('name') or api.get('path', 'API'),
                            "method": api.get('method', 'GET'),
                            "path": api.get('path', '/'),
                            "request": api.get('request', {}),
                            "assertions": [{"expression": "code", "condition": "EQUALS", "expectedValue": 200}]
                        }
                        test_cases.append(_normalize_case_to_flat_contract(synthesized, api_defaults=api))

        if not test_cases:
            raise CommandError("No executable test cases found in specification file.")

        self.stdout.write(self.style.NOTICE(f"Discovered {len(test_cases)} test cases for execution."))

        # Optionally emit Pytest script
        if output_pytest:
            pytest_code = generate_pytest_script(test_cases, base_url=base_url)
            with open(output_pytest, 'w', encoding='utf-8') as pf:
                pf.write(pytest_code + "\n")
            self.stdout.write(self.style.SUCCESS(f"Saved Pytest test script: {output_pytest}"))

        # Execute tests via APITestRunner
        runner = APITestRunner(base_url=base_url, max_concurrency=concurrency)
        if not runner._is_safe_target(base_url):
            raise CommandError(f"Target base URL '{base_url}' rejected by security policy.")

        self.stdout.write("Executing test suite asynchronously...")
        summary = asyncio.run(runner.execute_suite(test_cases))

        # Output results table
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"{'Method':<8} {'Status':<8} {'Latency':<10} {'Name'}")
        self.stdout.write("-" * 70)

        for res in summary['results']:
            m = res.get('method', 'GET')
            st = res.get('status', 'UNKNOWN')
            lat = f"{res.get('latency_ms', 0)}ms"
            nm = res.get('name', 'N/A')[:40]

            if res.get('passed'):
                self.stdout.write(self.style.SUCCESS(f"{m:<8} {st:<8} {lat:<10} {nm}"))
            else:
                self.stdout.write(self.style.ERROR(f"{m:<8} {st:<8} {lat:<10} {nm}"))

        self.stdout.write("=" * 70)
        self.stdout.write(
            f"Total: {summary['total']} | "
            f"Passed: {summary['passed']} | "
            f"Failed: {summary['failed']} | "
            f"Pass Rate: {summary['pass_rate']}% | "
            f"Total Duration: {summary['total_duration_ms']}ms\n"
        )

        # Generate and save JUnit XML report
        junit_exporter = JUnitExporter(suite_name=f"CodeBrain-{os.path.basename(spec_file)}")
        junit_xml = junit_exporter.generate_junit_xml(summary['results'])

        if output_junit:
            with open(output_junit, 'w', encoding='utf-8') as jf:
                jf.write(junit_xml + "\n")
            self.stdout.write(self.style.SUCCESS(f"Saved JUnit XML report: {output_junit}"))

        # Determine exit code criteria (Invariant 4: Standard CI/CD Exit Codes)
        passed_all = (summary['failed'] == 0) and (summary['pass_rate'] >= min_pass_rate)

        if not passed_all:
            raise CommandError(
                f"Test suite failed quality gate: {summary['failed']} failures "
                f"({summary['pass_rate']}% pass rate, required >= {min_pass_rate}%)."
            )

        self.stdout.write(self.style.SUCCESS("All test assertions passed successfully."))
