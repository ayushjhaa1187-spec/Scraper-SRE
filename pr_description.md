🧪 [testing improvement] Add unit tests for analyzer.detect_drift

🎯 **What:** The testing gap addressed
The pure function `detect_drift` inside `backend/app/analyzer.py` lacked test coverage. This function is critical for catching anomalies like null spikes and schema changes. Also, accidentally committed `__pycache__/*.pyc` files have been untracked and added to a new `.gitignore` file.

📊 **Coverage:** What scenarios are now tested
10 test cases have been written in `backend/tests/test_analyzer.py` that cover:
- Edge cases: When `last_run` or `current_run` are missing completely, or missing the `extracted_data_sample`.
- Happy paths: Successfully capturing scenarios with no drift or both runs being completely empty.
- Null Spikes: Catching the transition from populated values to zero values.
- Schema Changes: Detecting missing keys, added keys, and a combination of both.

✨ **Result:** The improvement in test coverage
The `detect_drift` logic is now robustly covered by automated tests, making refactoring safe and ensuring zero regressions on the anomaly detection behavior.
