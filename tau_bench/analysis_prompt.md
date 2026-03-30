# **Prompt: Analyze Tau-Bench Agent Performance**

## **Role and Goal**

You are an expert AI Engineer. Your task is to analyze the results of an agent's performance on a modified version of the Tau-Bench benchmark. The provided JSON file contains a list of task results. Your goal is to produce a concise, professional analysis document that includes quantitative results, a qualitative assessment of strengths and weaknesses, and notable case examples.

---

## **Input Data**

The input will be a JSON object containing a list of task results. Each task result includes a `task_id`, a final `reward` score, and detailed `info` about the task trajectory. Make sure you read all the tasks, and use them to do the output analysis.

**Key features of the modified benchmark:**
- **Granular Reward Score:** The `reward` is a composite score where `1.0` is a perfect success. `0.0` is a failure. `0.0 < reward < 1.0` is a success with some penalty.
  - Scores below `1.0` can indicate partial success.
  - An **Efficiency Penalty** of `-0.01` is applied for each step.
  - A **Resilience Bonus** of `+0.1` is awarded if the agent successfully recovers from a simulated API error.
- **Simulated API Errors:** The environment can introduce non-deterministic errors (e.g., `503 Service Unavailable`), which the agent must handle.

---

## **Output Format**

Please structure your output in Markdown, following this format:

1.  **Quantitative Results**
2.  **Strengths and Weaknesses**
3.  **Notable Cases Analysis**
    * Notable Success Example
    * Notable Failure Example

---

## **Instructions**

Follow these steps to generate the analysis. Show your chain of thought for the quantitative calculations.

### **Step 1: Quantitative Analysis**

Analyze the entire list of tasks in the provided JSON to calculate the following metrics:

1.  **Overall Success and Error Rate:**
    * Success Rate: Calculate the percentage of tasks where the final `base_success = 1.0`.
    * Error Rate: Calculate the percentage of tasks where the final `base_success = 0.0`.

2.  **Average Normalized Score:**
    * Calculate the mean of the `reward` field across ALL tasks. This is the primary performance metric.

3.  **Resilience Rate:**
    * First, count the total number of tasks where a simulated API error occurred. (You can identify these by looking for error responses in the tool outputs within the trajectory).
    * Next, count the number of tasks that received the `+0.1` Resilience Bonus.
    * Calculate the rate: `(Tasks with Resilience Bonus) / (Total Tasks with Simulated Errors)`.

4.  **Efficiency Analysis:**
    * Calculate the average trajectory length (number of turns) for "Successful Tasks" (`base_success = 1.0`) vs. "Failed Tasks" (`base_success = 0.0`).
    * Calculate the average tool call for "Successful Tasks" (`base_success = 1.0`) vs. "Failed Tasks" (`base_success = 0.0`).

5.  **Failure Breakdown:**
    * Categorize the failed tasks (`base_success = 0.0`) and get the breakdown number by case:
        * **Incomplete Task / Missed Instruction**
        * **Incorrect Reasoning / Logical Error**
        * **Incorrect Tool Usage (Wrong Parameters)**
    * Next we want to dive down into which tools cause the most difficulty to the model leading to the failures. This should include both the incorrect decision to use the tool  due to reasoning or logical error, and the incorrect tool usage (wrong parameter). Provide the result breakdown by tool.

### **Step 2: Strengths and Weaknesses**

Based on the quantitative results, provide a concise but insightful qualitative assessment of the agent's performance.

* **Strengths:** Look for evidence of high resilience, efficiency in successful tasks, and patterns in how the agent achieves high scores.
* **Weaknesses:** Analyze the failure breakdown. Does the agent struggle more with complete failures or partial credit scenarios? Is the Resilience Rate low? Does inefficiency significantly impact its scores?

### **Step 3: Notable Cases Analysis**

Scan the whole JSON file to find specific `task_id` examples that clearly illustrate the agent's capabilities.

1.  **Notable Success Example:**
    * Find a task with a high score that prominently features the **Resilience Bonus**.
    * Briefly describe the task instruction.
    * Explain how the agent encountered a simulated error and successfully retried, demonstrating its robustness.

2.  **Notable Failure Examples:**
    * Find 1-3 tasks with a low or negative score.
    * Briefly describe the task instruction.
    * Analyze its trajectory to explain *why* it failed, connecting it directly to the new scoring system (e.g., "The agent failed to recover from an API error and then entered an inefficient loop, causing its score to become negative due to the accumulated efficiency penalty.").
    * For each task, propose the brief suggestion on how to improve the model, such as fine-tuning strategies, architectural changes, or data augmentation technique as appropriate.

---
