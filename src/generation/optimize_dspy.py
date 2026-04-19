"""
DSPy BootstrapFewShot optimization script for ComicScript generation.

Loads training pairs from dspy_training_pairs.json, runs optimization,
and saves the optimized program for production use.

Usage:
    python -m src.generation.optimize_dspy
"""
import json
import os
import sys

# Ensure project root is on path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import dspy
from dspy.teleprompt import BootstrapFewShot

from src.generation.script_dspy import ComicScriptSignature, _configure_litellm_drop_params
from src.utils.config import LLM_MODEL, OPENAI_API_KEY, llm_temperature


def load_training_pairs(filepath: str) -> list:
    """Load training pairs from JSON file and convert to DSPy Examples."""
    print(f"Loading training pairs from {filepath}...")
    
    with open(filepath, "r", encoding="utf-8") as f:
        pairs = json.load(f)
    
    print(f"Found {len(pairs)} training pairs")
    
    # Convert to DSPy Example format
    trainset = []
    for pair in pairs:
        example = dspy.Example(
            user_message=pair["user_message"],
            comic_script_json=pair["comic_script_json"]
        ).with_inputs("user_message")
        trainset.append(example)
    
    return trainset


def validate_json_schema(example, pred, trace=None):
    """Metric function: validates that output is valid JSON with correct schema."""
    try:
        import json
        
        # Get the predicted JSON string
        pred_json = pred.comic_script_json if hasattr(pred, 'comic_script_json') else str(pred)
        
        # Parse JSON
        script = json.loads(pred_json)
        
        # Validate required fields
        if "panels" not in script:
            return False
        
        if not isinstance(script["panels"], list):
            return False
        
        # Check we have 3 panels
        if len(script["panels"]) != 3:
            return False
        
        # Validate each panel has required fields
        for i, panel in enumerate(script["panels"], start=1):
            if panel.get("panel_id") != i:
                return False
            if "visual_prompt" not in panel:
                return False
            if "dialogue" not in panel or not isinstance(panel["dialogue"], list):
                return False
        
        # Check top-level required fields
        for field in ["title", "style", "characters", "setting"]:
            if field not in script:
                return False
        
        return True
        
    except (json.JSONDecodeError, KeyError, TypeError):
        return False


def run_optimization():
    """Run BootstrapFewShot optimization on training data."""
    print("=" * 60)
    print("DSPy ComicScript Optimization - Starting")
    print("=" * 60)
    
    # Step 1: Configure DSPy
    print("\n[1/5] Configuring DSPy...")
    _configure_litellm_drop_params()
    
    kwargs = {
        "temperature": llm_temperature(),
        "max_tokens": 16000
    }
    if OPENAI_API_KEY:
        kwargs["api_key"] = OPENAI_API_KEY
    
    lm = dspy.LM(f"openai/{LLM_MODEL}", **kwargs)
    dspy.configure(lm=lm)
    print(f"✓ LM configured: {LLM_MODEL}")
    
    # Step 2: Load training data
    print("\n[2/5] Loading training data...")
    training_file = os.path.join(_project_root, "data", "dspy_training_pairs.json")
    
    if not os.path.exists(training_file):
        print(f"✗ Training file not found: {training_file}")
        print("  Run the pipeline first to collect training pairs!")
        sys.exit(1)
    
    trainset = load_training_pairs(training_file)
    print(f"✓ Loaded {len(trainset)} examples")
    
    # Step 3: Setup teleprompter
    print("\n[3/5] Setting up BootstrapFewShot...")
    teleprompter = BootstrapFewShot(
        metric=validate_json_schema,
        max_bootstrapped_demos=4,  # Use up to 4 examples as demos
        max_labeled_demos=4,
        max_rounds=2  # Number of bootstrapping rounds
    )
    print("✓ Teleprompter configured")
    
    # Step 4: Run optimization
    print("\n[4/5] Running optimization (this will take a few minutes)...")
    print("  Making API calls to bootstrap examples...")
    
    student = dspy.Predict(ComicScriptSignature)
    
    try:
        optimized_program = teleprompter.compile(
            student=student,
            teacher=student,
            trainset=trainset
        )
        print("✓ Optimization complete!")
    except Exception as e:
        print(f"✗ Optimization failed: {e}")
        print("  Trying with simpler configuration...")
        
        # Fallback: simpler optimization
        teleprompter = BootstrapFewShot(
            metric=validate_json_schema,
            max_bootstrapped_demos=3,
            max_labeled_demos=3,
            max_rounds=1
        )
        
        optimized_program = teleprompter.compile(
            student=student,
            teacher=student,
            trainset=trainset
        )
        print("✓ Optimization complete (simplified)!")
    
    # Step 5: Save optimized program
    print("\n[5/5] Saving optimized program...")
    # DSPy 3.x: save() expects .json extension but creates a directory
    output_path = os.path.join(_project_root, "data", "optimized_comic_program.json")
    
    # Remove old files/directories if they exist
    import shutil
    if os.path.exists(output_path):
        if os.path.isdir(output_path):
            shutil.rmtree(output_path)
        else:
            os.remove(output_path)
        print(f"  Removed old optimized program")
    
    if os.path.exists(output_path.replace('.json', '')):
        shutil.rmtree(output_path.replace('.json', ''))
    
    optimized_program.save(output_path)
    print(f"✓ Saved to: {output_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("OPTIMIZATION COMPLETE!")
    print("=" * 60)
    print(f"\nOptimized program saved to:")
    print(f"  {output_path}")
    print(f"\nThe optimized model will automatically load on next run!")
    print("=" * 60)


if __name__ == "__main__":
    run_optimization()
