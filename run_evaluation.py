#!/usr/bin/env python3
"""
Relational Context and Sycophancy Evaluation Script

This script tests whether Claude responds differently to the same question
depending on how the user frames themselves or their emotional state.

It sends prompt pairs (neutral vs. emotionally invested framings) to the
Claude API and logs the responses for analysis.
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
# This is where we'll store the API key securely
load_dotenv()


class SycophancyEvaluator:
    """
    Main class for running the sycophancy evaluation.

    This class handles:
    - Loading prompt pairs from a JSON file
    - Sending requests to the Claude API
    - Logging responses to both JSON and CSV formats
    """

    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the evaluator.

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
            model: Which Claude model to use (default: Claude 3.5 Sonnet)
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key found. Please set ANTHROPIC_API_KEY in .env file "
                "or pass api_key parameter."
            )

        # Initialize the Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

        # Create results directory if it doesn't exist
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

    def load_prompt_pairs(self, filepath: str = "prompt_pairs.json") -> List[Dict]:
        """
        Load prompt pairs from a JSON file.

        Args:
            filepath: Path to the JSON file containing prompt pairs

        Returns:
            List of prompt pair dictionaries
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data['prompt_pairs']

    def send_prompt(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Send a single prompt to Claude and get the response.

        Args:
            prompt: The text prompt to send
            max_tokens: Maximum tokens in the response

        Returns:
            Claude's response text
        """
        try:
            # Create a message using the Anthropic SDK
            # This is the core API call that sends your prompt to Claude
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the text from the response
            # The API returns a message object, we want just the text content
            return message.content[0].text

        except Exception as e:
            # If something goes wrong, log the error and return it
            print(f"Error sending prompt: {e}")
            return f"ERROR: {str(e)}"

    def run_evaluation(self, prompt_pairs_file: str = "prompt_pairs.json"):
        """
        Run the full evaluation on all prompt pairs.

        This is the main method that:
        1. Loads all prompt pairs
        2. Sends each variant (neutral and invested) to Claude
        3. Logs all responses
        4. Saves results to both JSON and CSV

        Args:
            prompt_pairs_file: Path to the JSON file with prompt pairs
        """
        # Load all the prompt pairs
        prompt_pairs = self.load_prompt_pairs(prompt_pairs_file)

        # This will store all our results
        results = []

        # Generate a timestamp for this evaluation run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"Starting evaluation with {len(prompt_pairs)} prompt pairs...")
        print(f"Using model: {self.model}\n")

        # Loop through each prompt pair
        for i, pair in enumerate(prompt_pairs, 1):
            prompt_id = pair['id']
            category = pair['category']
            base_question = pair['base_question']

            print(f"[{i}/{len(prompt_pairs)}] Processing: {prompt_id}")
            print(f"  Category: {category}")
            print(f"  Base question: {base_question[:60]}...")

            # Process the NEUTRAL framing
            print("  → Sending neutral framing...")
            neutral_response = self.send_prompt(pair['neutral_framing'])

            results.append({
                'prompt_id': prompt_id,
                'category': category,
                'base_question': base_question,
                'framing_type': 'neutral',
                'full_prompt': pair['neutral_framing'],
                'response': neutral_response,
                'timestamp': datetime.now().isoformat(),
                'model': self.model
            })

            # Process the INVESTED framing
            print("  → Sending invested framing...")
            invested_response = self.send_prompt(pair['invested_framing'])

            results.append({
                'prompt_id': prompt_id,
                'category': category,
                'base_question': base_question,
                'framing_type': 'invested',
                'full_prompt': pair['invested_framing'],
                'response': invested_response,
                'timestamp': datetime.now().isoformat(),
                'model': self.model
            })

            print("  ✓ Completed\n")

        # Save results in both formats
        self._save_results_json(results, timestamp)
        self._save_results_csv(results, timestamp)

        print(f"\n✓ Evaluation complete!")
        print(f"  Results saved to results/ directory")
        print(f"  - JSON: results/evaluation_{timestamp}.json")
        print(f"  - CSV: results/evaluation_{timestamp}.csv")

        return results

    def _save_results_json(self, results: List[Dict], timestamp: str):
        """Save results to a JSON file."""
        output_file = self.results_dir / f"evaluation_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                'metadata': {
                    'timestamp': timestamp,
                    'model': self.model,
                    'total_prompts': len(results)
                },
                'results': results
            }, f, indent=2)

    def _save_results_csv(self, results: List[Dict], timestamp: str):
        """Save results to a CSV file."""
        output_file = self.results_dir / f"evaluation_{timestamp}.csv"

        # Define the columns for our CSV
        fieldnames = [
            'prompt_id',
            'category',
            'base_question',
            'framing_type',
            'full_prompt',
            'response',
            'timestamp',
            'model'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)


def main():
    """
    Main entry point for the script.

    This runs when you execute: python run_evaluation.py
    """
    print("=" * 60)
    print("Relational Context and Sycophancy: A Pilot Evaluation")
    print("=" * 60)
    print()

    # Create the evaluator
    # This will read your API key from the .env file
    evaluator = SycophancyEvaluator()

    # Run the evaluation
    # This will process all prompt pairs in prompt_pairs.json
    evaluator.run_evaluation()


if __name__ == "__main__":
    main()
