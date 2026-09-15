# Spec 06 — ML / Statistical Layer

**Status:** Draft
**Phase:** 2
**Depends on:** Specs 01, 02, 03, 04, 05
**Downstream:** Spec 07 (Runtime consumes ML outputs as one input among many), Spec 09 (Trade card surfaces model outputs)

---

## 1. Purpose

The ML / Statistical Layer produces **conditional evaluations** — "given the current context, what would history suggest about this setup?" — that supplement the deterministic rules in Spec 03 and the expectancy tables in Spec 05.

**This layer does NOT authorize trades.** It is an *evaluator*, never a decider. Its outputs go into the Trade Card (Spec 09) as evidence for the human's final approval.

---

## 2. Guiding Principles

### P1 — Evaluator, Never Decider
No model output can directly cause a trade to be placed. Rules gate; models describe.

### P2 — Interpretable Before Fancy
Prefer simple, interpretable models (logistic regression, gradient-boosted trees with SHAP explanations) over deep networks. Every prediction must be explainable to the trader.

### P3 — No Leakage, Ever
Any feature used at prediction time must have been observable at the historical prediction time. Any target must be strictly in the future relative to features.

### P4 — Sample Size Governs Trust
Model confidence is meaningless without adequate training data. Thin data = don't use the model.

### P5 — Models Decay
Every model has a decay schedule and a retraining cadence. A model that hasn't been retrained in 6 months is off.

### P6 — Version Everything
Model provider, model name, feature-set version, training window — all stamped on every prediction and every trade card.

---

## 3. Model Catalog

### 3.1 Model A — Setup Outcome Predictor
**Purpose:** Given a current setup candidate, predict the probability of reaching +1R before −1R within the expected holding window.
**Type:** Gradient-boosted classifier (XGBoost or LightGBM)
**Target:** Binary: `hit_1R_first = 1` if +1R was reached before stop, within 20 trading days
**Output:** Probability [0, 1] + SHAP explanation

### 3.2 Model B — Expected Holding Period Regressor
**Purpose:** Predict the number of trading days until first exit (any exit) for a fresh setup.
**Type:** Gradient-boosted regressor
**Target:** Actual holding days from historical outcome
**Output:** Predicted days + prediction interval

### 3.3 Model C — Regime Classifier (referenced from Spec 07)
Speced in Spec 07. Uses market-wide features to classify current regime. Consumed by Research Engine (Spec 05) and Runtime (Spec 07).

### 3.4 Future Models (Not Phase 2)
- Volatility-adjusted price forecast
- Drawdown probability estimator
- Correlation forecaster (portfolio risk)

**No models are added without an explicit spec extension and evidence of edge.**

---

## 4. Feature Engineering

### 4.1 Feature Groups

| Group | Examples |
|-------|----------|
| Trend | Distance from 20/50/200 EMA (in ATR units), slope of MAs, days in Stage 2 |
| Relative Strength | RS-line 63d high, RS slope, stock 63d return minus SPY 63d return |
| Pullback Character | Pullback depth (% and ATR), days in pullback, volume ratio during pullback |
| Volume | 20d/50d ADV ratio, recent volume vs baseline, up-vol / down-vol ratio |
| Volatility | ATR-14, ATR-14 / price, realized vol, VIX regime |
| Market Context | SPY 20/50/200 MA state, breadth, VIX level, VIX slope |
| Sector Context | Sector RS vs SPY, sector ranking, days in current sector leadership |
| Time Context | Days to next earnings, day of week, month of year, days since last earnings |
| Setup-Specific | For pullback setup: support type touched (EMA20/EMA50/pivot), overextension |

### 4.2 Forbidden Features
- Anything derived from future data (obvious)
- Anything not observable at prediction time
- Look-ahead earnings announcements
- Post-hoc corporate actions
- Later revised fundamentals

### 4.3 Feature Provenance
Every feature has:
- Definition (formula)
- Data source (per Spec 02)
- Computation cost tier (cheap / medium / expensive) — informs runtime latency

### 4.4 Feature Set Version
The complete feature set is versioned. Adding a feature bumps the version. Every model prediction is stamped with the feature-set version used.

---

## 5. Training Methodology

### 5.1 Data Partitioning
Strict time-based split, no random shuffling:
- **Training window:** oldest N years
- **Validation window:** next K months
- **Test window:** most recent M months — never used for training, never used for hyperparameter selection

### 5.2 Walk-Forward Retraining
Models retrain on a rolling schedule (default: monthly). New predictions use the most recently trained model. Historical predictions are made with the model that would have been current at that historical date (for backtesting the model's contribution).

### 5.3 Hyperparameter Selection
- Bayesian or grid search on the validation window only
- Chosen hyperparameters recorded with the model version
- No re-selection on the test window under any circumstance

### 5.4 Cross-Validation
Time-series cross-validation only. **No k-fold with random shuffling** — that leaks future information.

### 5.5 Class Imbalance
If the target class is imbalanced (e.g., only 30% of setups hit +1R first), use class weights or SMOTE — but only on the training set, never on validation or test.

---

## 6. Evaluation Metrics

For Model A (setup outcome predictor):

| Metric | Reported |
|--------|----------|
| Log loss | Yes |
| Brier score | Yes (probability calibration) |
| ROC AUC | Yes |
| Calibration curve | Yes (visual) |
| Precision at top decile | Yes |
| Actual expectancy of top-decile predictions | **Yes — this is the money metric** |
| Feature importance | SHAP values |

**A model can have a great AUC and produce no trading edge.** Always report the actual expectancy of trades the model recommended.

For Model B (holding period regressor):

| Metric | Reported |
|--------|----------|
| MAE | Yes |
| Prediction interval coverage | Yes (does the 80% PI actually cover 80%?) |

---

## 7. Output Contract

Every model prediction that reaches a trade card includes:

```
model_id:                Model A (Setup Outcome Predictor)
model_version:           2026-Q3-v4
feature_set_version:     v12
training_end_date:       2026-08-31
n_training_examples:     4,732
prediction:              0.62
prediction_interval:     [0.51, 0.72]
sample_size_at_context:  187 (similar contexts in training data)
top_features_shap:       [ RS_slope: +0.14, pullback_depth_atr: −0.08, ... ]
```

**If `sample_size_at_context < 30`, the trade card must display "LOW MODEL CONFIDENCE" and the prediction is treated as advisory only.**

---

## 8. Role in the Trade Decision

The trade card (Spec 09) displays:
- Deterministic rule outcome (setup detected: YES/NO, per Spec 03)
- Historical expectancy table stat (per Spec 05)
- Model prediction (this spec)

**Only the first is a gate.** The model prediction is *evidence* the trader considers, alongside the historical stat. The model prediction alone cannot approve or veto a trade.

If the model prediction disagrees strongly with the historical expectancy (e.g., historical +0.4R but model predicts 45% win probability), a `MODEL_HISTORY_DIVERGENCE` warning is added to the trade card.

---

## 9. Model Governance

### 9.1 Retraining Cadence
- **Default:** monthly, on the first weekend of each month
- **Ad-hoc:** manually triggered after a data schema change or a major regime shift

### 9.2 Model Decay Monitoring
Track live prediction accuracy over rolling 3 months. If:
- Brier score degrades by > 20% vs training-time score, OR
- Top-decile expectancy drops below 0

then the model is auto-marked `DEGRADED`. Trade cards continue to show the prediction but with a DEGRADED tag. The trader can choose to ignore model outputs during degradation.

### 9.3 Model Versioning and Rollback
- Every trained model persisted with version, training window, config
- Previous 3 versions retained for rollback
- Rolling back is a logged, timestamped event

### 9.4 Champion / Challenger
Optional (Phase 3+): run a challenger model alongside champion. Compare predictions and outcomes for 3 months before promoting a challenger.

---

## 10. Stories

### Story 6.1 — Feature Extraction Pipeline
**As:** engineering
**I want:** a versioned, deterministic feature extraction pipeline
**So that:** the same context always produces the same features across training and inference

**Acceptance criteria:**
- Feature set defined in a single manifest with formulas and provenance
- Pipeline produces identical features given identical historical data
- Feature-set version bumped when a feature is added, removed, or its formula changes
- Golden fixture test on a known date

### Story 6.2 — Time-Series Data Partitioner
**As:** research
**I want:** strict time-based partitioning with configurable train/validate/test windows
**So that:** future data cannot leak into training

**Acceptance criteria:**
- Partitioner takes date ranges only; random shuffling is not an option
- Refuses to partition if train/validate/test windows overlap
- Test partition inaccessible to hyperparameter selection tools (enforced by API)

### Story 6.3 — Setup Outcome Predictor Trainer (Model A)
**As:** research
**I want:** a trainer that produces Model A per §3.1
**So that:** the runtime has a probability estimate for each setup candidate

**Acceptance criteria:**
- Uses gradient-boosted classifier
- Reports all metrics in §6
- Persists model with version, training window, hyperparameters
- Retraining pipeline runs monthly

### Story 6.4 — Holding Period Regressor (Model B)
**As:** research
**I want:** Model B per §3.2
**So that:** trade cards can show an expected holding-period estimate

**Acceptance criteria:**
- Regressor with prediction intervals
- MAE and coverage reported
- Persisted with same governance as Model A

### Story 6.5 — Model Prediction Wrapper
**As:** the runtime
**I want:** a wrapper that calls a versioned model and returns the output contract in §7
**So that:** predictions are always accompanied by their metadata

**Acceptance criteria:**
- Returns model_id, model_version, feature_set_version, prediction, SHAP top-features, sample_size_at_context
- Fails safe (returns "MODEL_UNAVAILABLE") if the model is missing or errored — trade card proceeds without model input
- Latency < 500ms per prediction

### Story 6.6 — Sample-Size at Context
**As:** the runtime
**I want:** a query "how many training examples are similar to this context?"
**So that:** model confidence can be gated by density of similar historical setups

**Acceptance criteria:**
- Given a feature vector, returns count of training examples within a defined similarity radius
- Threshold < 30 triggers LOW_MODEL_CONFIDENCE tag on trade card
- Similarity metric documented (e.g., feature-space distance)

### Story 6.7 — Model Decay Monitor
**As:** the governance system
**I want:** rolling monitoring of live prediction accuracy
**So that:** degrading models are surfaced quickly

**Acceptance criteria:**
- Weekly job compares live prediction outcomes to model's training-time metrics
- If Brier degrades > 20% or top-decile expectancy < 0, marks model DEGRADED
- Alert to trader; trade cards flag DEGRADED status

### Story 6.8 — Model Registry
**As:** engineering
**I want:** a registry of all model versions with metadata
**So that:** rollback and audit are trivial

**Acceptance criteria:**
- Registry stores every trained model with version, date, config, metrics
- Rollback command promotes a previous version
- Every trade card records which model version was used

### Story 6.9 — Divergence Detector
**As:** the trade card
**I want:** a flag when model prediction and historical expectancy disagree strongly
**So that:** the trader is alerted to conflicting evidence

**Acceptance criteria:**
- Computes agreement between model probability and historical win rate
- Divergence beyond threshold sets MODEL_HISTORY_DIVERGENCE flag on trade card
- Threshold configurable; default: absolute difference > 15 percentage points

### Story 6.10 — Model Explainer Output
**As:** the trader
**I want:** the top 3–5 SHAP features per prediction on the trade card
**So that:** I can see *why* the model is favorable or unfavorable

**Acceptance criteria:**
- SHAP values computed per prediction
- Top features by absolute SHAP magnitude shown on trade card
- Feature names are human-readable (not `feat_073`)

---

## 11. Acceptance Criteria for Spec 06

- All stories 6.1–6.10 pass their acceptance criteria
- Leakage test: deliberately insert a leaky feature (uses future data); test suite detects and fails
- Backtest with model contribution: does the model actually improve out-of-sample expectancy vs deterministic rules alone? If not, the model is not deployed.
- Strongest available reasoning model has reviewed and APPROVED

---

## 12. Open Questions for the Trader

1. **Model types:** are we OK starting with gradient-boosted trees only, or interested in interpretable models like logistic regression as a first pass?
2. **Retraining cadence:** monthly — comfortable, or too frequent (overfitting to recent noise)?
3. **Model contribution:** if the model does not measurably improve out-of-sample expectancy vs rules alone, do we still include it (for context) or omit it entirely?
4. **Compute budget:** training monthly on 10 years of data on a laptop — acceptable, or move to cloud?
5. **Champion/challenger:** interested in Phase 2 or defer to Phase 3?
