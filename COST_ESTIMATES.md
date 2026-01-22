# Cost & Time Estimates - OpenRouter

**Last Updated**: 2026-01-22
**Based on**: Actual run data from tau-bench

## Summary: What Can You Run for Under $5?

✅ **ALL MODELS ON ALL TASKS = $3.78**

You can run:
- All 3 Qwen models (8B, 14B, 32B)
- On all 685 tasks (635 retail + 50 airline)
- For only **$3.78 total**

---

## Cost Breakdown by Model

### Retail Domain (635 tasks)

| Model | Agent Cost | User Cost | **Total Cost** | Per Task |
|-------|------------|-----------|----------------|----------|
| Qwen3-8B | $0.89 | $0.06 | **$0.95** | $0.0015 |
| Qwen3-14B | $1.24 | $0.06 | **$1.30** | $0.0020 |
| Qwen3-32B | $1.19 | $0.06 | **$1.25** | $0.0020 |

**All 3 models on retail: $3.50**

### Airline Domain (50 tasks)

| Model | Agent Cost | User Cost | **Total Cost** | Per Task |
|-------|------------|-----------|----------------|----------|
| Qwen3-8B | $0.07 | $0.00 | **$0.07** | $0.0015 |
| Qwen3-14B | $0.10 | $0.00 | **$0.10** | $0.0020 |
| Qwen3-32B | $0.10 | $0.00 | **$0.10** | $0.0020 |

**All 3 models on airline: $0.27**

### Combined (685 tasks total)

| Scenario | Cost |
|----------|------|
| All 3 models on retail only | $3.50 |
| All 3 models on airline only | $0.27 |
| **All 3 models on all tasks** | **$3.78** |

---

## Time Estimates

### 635 Retail Tasks

| Concurrency | Time | Recommended For |
|-------------|------|-----------------|
| 1 | 4h 36m | Testing single task |
| 5 | 55m | Moderate runs |
| 10 | 27m | **Recommended** |
| 20 | 13m | Fast full runs |

### 50 Airline Tasks

| Concurrency | Time | Recommended For |
|-------------|------|-----------------|
| 1 | 22m | Testing |
| 5 | 4m | Quick runs |
| 10 | 2m | **Recommended** |

---

## Recommended Run Plans

### Plan 1: Quick Test ($0.15, ~5 minutes)
```bash
# Test with 8B on 20 retail tasks
python run.py \
  --model qwen/qwen3-8b --model-provider openrouter \
  --env retail --task-split dev \
  --max-concurrency 10 \
  --env-file .env
```
**Cost**: ~$0.03 (20 tasks)
**Time**: ~1 minute

### Plan 2: Full Retail Comparison ($3.50, ~81 minutes)
```bash
# Run all 3 models on retail
for model in qwen/qwen3-8b qwen/qwen3-14b qwen/qwen3-32b; do
  python run.py \
    --model $model --model-provider openrouter \
    --env retail --task-split test \
    --max-concurrency 10 \
    --env-file .env
done
```
**Cost**: $3.50
**Time**: ~81 minutes (27m × 3 models)

### Plan 3: Everything ($3.78, ~90 minutes)
```bash
# All models on all tasks (retail + airline)
for model in qwen/qwen3-8b qwen/qwen3-14b qwen/qwen3-32b; do
  # Retail
  python run.py \
    --model $model --model-provider openrouter \
    --env retail --task-split test \
    --max-concurrency 10 \
    --env-file .env

  # Airline
  python run.py \
    --model $model --model-provider openrouter \
    --env airline \
    --max-concurrency 10 \
    --env-file .env
done
```
**Cost**: $3.78
**Time**: ~90 minutes

### Plan 4: Training Set ($1.50, ~43 minutes)
```bash
# Run 8B on full training set (500 tasks)
python run.py \
  --model qwen/qwen3-8b --model-provider openrouter \
  --env retail --task-split train \
  --max-concurrency 10 \
  --env-file .env
```
**Cost**: ~$1.50
**Time**: ~43 minutes

---

## Detailed Pricing (Per Million Tokens)

### Agent Models (OpenRouter)
| Model | Input | Output | Context |
|-------|-------|--------|---------|
| Qwen3-8B | $0.04 | $0.14 | 32K |
| Qwen3-14B | $0.05 | $0.25 | 32K |
| Qwen3-32B | $0.05 | $0.22 | 32K |

### User Simulator
| Model | Input | Output | Context |
|-------|-------|--------|---------|
| GPT-OSS-20B | $0.02 | $0.10 | 131K |

---

## Token Usage (Average per Task)

Based on actual benchmark runs:

| Metric | Amount |
|--------|--------|
| Total messages per task | 18.8 |
| Agent calls per task | 8.7 |
| Agent input tokens | ~26,100 |
| Agent output tokens | ~2,610 |
| User input tokens | ~4,000 |
| User output tokens | ~1,000 |

---

## Cost Optimization Tips

### 1. Use Task IDs for Testing
```bash
# Test on 5 tasks first
--task-ids 0 1 2 3 4
```
**Saves**: 99% of cost during development

### 2. Use Dev Split for Quick Validation
```bash
--task-split dev  # Only 20 tasks
```
**Saves**: 97% of cost vs full test set

### 3. Use 8B for Development
```bash
--model qwen/qwen3-8b
```
**Saves**: 27% vs 14B, 24% vs 32B

### 4. Increase Concurrency
```bash
--max-concurrency 20  # Instead of 1
```
**Saves**: 95% of time (4.6h → 13m)

### 5. Skip Easy Tasks
```bash
--task-ids 10 20 30 40 50  # Run every 10th task
```
**Saves**: 90% of cost while sampling performance

---

## Budget Calculator

### By Number of Tasks

| Tasks | 8B | 14B | 32B | All 3 |
|-------|-----|-----|-----|-------|
| 10 | $0.02 | $0.02 | $0.02 | $0.06 |
| 20 (dev) | $0.03 | $0.04 | $0.04 | $0.11 |
| 50 (airline) | $0.07 | $0.10 | $0.10 | $0.27 |
| 100 | $0.15 | $0.20 | $0.20 | $0.55 |
| 115 (retail test) | $0.17 | $0.23 | $0.22 | $0.62 |
| 500 (retail train) | $0.75 | $1.00 | $0.99 | $2.74 |
| 635 (all retail) | $0.95 | $1.30 | $1.25 | $3.50 |
| 685 (all tasks) | $1.02 | $1.40 | $1.35 | $3.78 |

### Budget Scenarios

**$1 Budget**:
- 635 retail tasks with 8B ($0.95)
- OR 500 train tasks with 14B ($1.00)

**$2 Budget**:
- All retail with 8B + 14B ($2.25)
- OR All tasks with 8B + airline with 14B/32B ($1.22)

**$3 Budget**:
- All retail with 8B + 14B ($2.25) + 200 train tasks with 32B ($0.62) = $2.87

**$5 Budget**:
- All tasks with all 3 models ($3.78)
- + 800 extra retail tasks with 8B ($1.20) = $4.98

---

## Notes

1. **Costs are estimates** based on actual run data (8.7 agent calls/task)
2. **User simulator cost is actual** measured data from runs
3. **Concurrency doesn't affect cost**, only time
4. **API rate limits** may require lower concurrency
5. **Failed tasks** still incur costs for attempted API calls
6. **Costs may vary** slightly based on:
   - Task complexity (more tool calls = higher cost)
   - Response length (some tasks need longer outputs)
   - Provider routing (OpenRouter may route to different backends)

---

## Safety Margin

**Recommended**: Budget 20% extra for:
- Failed tasks that need retries
- Longer than average conversations
- API rate limit delays

**Example**: For $5 budget, plan to spend ~$4 on actual runs

---

## Sources

- [Qwen3-8B Pricing](https://pricepertoken.com/pricing-page/model/qwen-qwen3-8b)
- [Qwen3-32B Pricing](https://openrouter.ai/qwen/qwen3-32b:free/providers)
- [GPT-OSS-20B Pricing](https://pricepertoken.com/pricing-page/model/openai-gpt-oss-20b)
- [OpenRouter Pricing Calculator](https://invertedstone.com/calculators/openrouter-pricing)
