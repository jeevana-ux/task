import sys
import os
from pathlib import Path
import dspy
from dspy.teleprompt import BootstrapFewShot
from dspy.evaluate import Evaluate

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.config import Config
from src.utils.dataset_loader import load_dataset
from src.dspy_modules.signatures import SchemeExtractionSignature
from src.training.metrics import validate_extraction

def optimize_extractor():
    """
    Optimizes the DSPy extractor using Few-Shot Bootstrapping and evaluates accuracy.
    """
    print("=== DSPy Few-Shot Optimization & Evaluation ===")
    
    # 1. Setup LM
    print(f"Configuring LM: {Config.DEFAULT_MODEL}")
    try:
        lm = dspy.LM(
            model=Config.DEFAULT_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENROUTER_BASE_URL,
            max_tokens=Config.MAX_TOKENS
        )
    except AttributeError:
        # Fallback for older versions just in case
        lm = dspy.OpenAI(
            model=Config.DEFAULT_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENROUTER_BASE_URL,
            max_tokens=4000
        )
        
    dspy.configure(lm=lm)
    
    # 2. Load Data
    train_file = project_root / "train" / "train.json"
    val_file = project_root / "train" / "val.json"
    
    print(f"Loading training data from: {train_file}")
    trainset = load_dataset(str(train_file))
    print(f"Loaded {len(trainset)} training examples.")
    
    print(f"Loading validation data from: {val_file}")
    # Check if val file exists
    if os.path.exists(val_file):
        valset = load_dataset(str(val_file))
        print(f"Loaded {len(valset)} validation examples.")
    else:
        valset = []
        print("⚠️ No validation file found. Accuracy metrics will be skipped.")
    
    if not trainset:
        print("❌ No training data found. Aborting.")
        return

    # 3. Initialize Teacher & Student
    student = dspy.ChainOfThought(SchemeExtractionSignature)
    
    # 4. Configure Teleprompter
    # This creates a DSPy few-shot prompt optimizer.
    teleprompter = BootstrapFewShot(
        metric=validate_extraction,
        max_bootstrapped_demos=2,
        max_labeled_demos=2,
    )
    
    # 5. Optimize
    print("\n--- Starting Optimization ---")
    compiled_program = teleprompter.compile(student, trainset=trainset)
    
    # 6. Evaluate (Calculate Accuracy)
    if valset:
        print("\n--- Evaluating Accuracy on Validation Set ---")
        evaluator = Evaluate(
            devset=valset, 
            metric=validate_extraction, 
            num_threads=1, 
            display_progress=True,
            display_table=False
        )
        
        # This returns the average score (0.0 to 1.0) based on our weighted metric
        score = evaluator(compiled_program)
        
        # dspy 2.5+ might return a float, earlier versions an object. Safe cast.
        try:
            score_val = float(score)
            print(f"\n✅ Validation Score: {score_val:.2f} / 1.00")
        except:
             print(f"\n✅ Validation Score: {score} / 1.00")

        print(f"   (Score based on weighted metrics: 3x Classification, 1x Structured, 0.5x Creative)")
    
    # 7. Save
    output_path = project_root / "src" / "dspy_modules" / "optimized_extractor.json"
    compiled_program.save(str(output_path))
    
    print(f"\n✅ Optimization Complete.")
    print(f"saved to: {output_path}")

if __name__ == "__main__":
    optimize_extractor()
