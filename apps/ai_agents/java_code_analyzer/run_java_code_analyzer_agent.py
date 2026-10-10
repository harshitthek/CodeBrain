#!/usr/bin/env python3
"""
CLI runner for Java Code Analyzer AI Agent.

Usage:
    python apps/ai_agents/java_code_analyzer/run_java_code_analyzer_agent.py <repo_path> <base_commit> <new_commit>
    python apps/ai_agents/java_code_analyzer/run_java_code_analyzer_agent.py ./projects/education-service 95291763 4cbb6ab4 --model deepseek-chat
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.ai_agents.java_code_analyzer.tools import GitTools
from apps.ai_agents.java_code_analyzer.java_code_analyzer_agent import JavaCodeAnalyzerAgent


def main():
    """Run analysis"""
    parser = argparse.ArgumentParser(
        description="Run test scope analysis Agent using LangChain framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument("repo_path", nargs='?', help="Java project path", default="./projects/java-callgraph2")
    parser.add_argument("base_commit", nargs='?', help="Base commit hash", default="75f4c93a")
    parser.add_argument("new_commit", nargs='?', help="Target commit hash", default="20b84145")
    parser.add_argument("--java_analyzer_service_url", help="Java analyzer API URL")
    parser.add_argument("--max-iterations", type=int, help="Max iterations", default=300)
    parser.add_argument("--model", help="Model name (overrides env var)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    
    args = parser.parse_args()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    base_url = os.getenv("OPENAI_BASE_URL")
    model = args.model or os.getenv("OPENAI_MODEL", "deepseek-reasoner")
    
    print("="*70)
    print("🤖 LangChain Test Scope Analysis Agent")
    print("="*70)
    print(f"📁 Repository Path: {args.repo_path}")
    print(f"🔄 Change Range: {args.base_commit[:8]} → {args.new_commit[:8]}")
    print(f"🧠 Model: {model}")
    if base_url:
        print(f"🌐 API URL: {base_url}")
    if args.java_analyzer_service_url:
        print(f"🔧 Analyzer Service: {args.java_analyzer_service_url}")
    print("="*70)
    print()

    # Pull latest code
    git_tools = GitTools(args.repo_path)
    print("\n🔄 Pulling latest code...")
    git_tools.pull_latest() 

    # Record current ref
    print("\n🔍 Recording current Git status...")
    original_ref = git_tools.get_current_ref()
    print(f"   Current ref: {original_ref}")
    
    # Initialize Agent
    try:
        print(f"\n🔄 Switching to target commit: {args.new_commit}")
        git_tools.checkout_version(args.new_commit)
        print(f"✅ Switched to: {args.new_commit}")

        agent = JavaCodeAnalyzerAgent(
            repo_path=args.repo_path,
            api_key=api_key,
            base_url=base_url,
            java_analyzer_service_url=args.java_analyzer_service_url,
            max_iterations=args.max_iterations,
            verbose=not args.quiet
        )
        print("✓ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🚀 Starting analysis...")
    print("="*70)
    print()
    
    try:
        result = agent.analyze(args.base_commit, args.new_commit)
        
        if result["success"]:
            print("\n" + "="*70)
            
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = Path(f"langchain_analysis_{args.base_commit[:8]}_{args.new_commit[:8]}.md")
            
            output_path.write_text(result["output"], encoding='utf-8')
            print(f"\n✓ Report saved to: {output_path}")
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\n" + "="*70)
        print("✅ Analysis finished!")
        print("="*70)
        print(f"\n🔄 Restoring to original ref: {original_ref}")
        GitTools(args.repo_path).checkout_version(original_ref)
        print(f"✅ Restored to: {original_ref}")


if __name__ == "__main__":
    main()
