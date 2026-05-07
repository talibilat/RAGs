# Agent Rules - Superpowers Integration

## Skill Activation
- **ALWAYS** check `.agent/skills/using-superpowers/SKILL.md` at the start of every turn.
- Follow the **"1% Rule"**: If there is even a 1% chance a skill applies (like `brainstorming`, `writing-plans`, or `test-driven-development`), you **MUST** activate it before taking any other action.
- Announce when you are using a skill: *"I'm using the [skill-name] superpower to [purpose]."*

## Test-Driven Development (TDD) Core Principles
When performing TDD, always adhere to these Superpowers standards:
1. **The Iron Law**: Never write a single line of production code without a failing test first.
2. **Watch it Fail**: You must verify the test fails with the expected error message before implementing the fix.
3. **Listen to the Test**: If a test is difficult to set up, treat it as a signal that the code design is too coupled or complex. Refactor the design, don't just "power through" with mocks.
4. **Minimalism (YAGNI)**: Write the absolute minimum code required to make the test pass. Avoid "future-proofing" or adding features not yet covered by a test.
5. **No Mocks by Default**: Prefer real implementations or simple stubs over complex mocking frameworks. If you must mock, mock interfaces you own, not third-party libraries.
6. **Clean Output**: Tests must run silently. Any warnings, logs, or side effects during test runs must be cleaned up or suppressed.

## Planning & Execution
- Use the `writing-plans` skill for any task involving more than two files or significant logic changes.
- Use the `executing-plans` skill to track progress once a plan is approved.
