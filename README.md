# ARC-AGI-3-Agents

## Quickstart

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if not aready installed.

1. Clone the ARC-AGI-3-Agents repo and enter the directory.

```bash
git clone https://github.com/arcprize/ARC-AGI-3-Agents.git
cd ARC-AGI-3-Agents
```

2. Copy .env.example to .env

```bash
cp .env.example .env
```

3. Get an API key from the [ARC-AGI-3 Website](https://three.arcprize.org/) and set it as an environment variable in your .env file.

```bash
export ARC_API_KEY="your_api_key_here"
```

4. Run the random agent (generates random actions) against the ls20 game.

```bash
uv run main.py --agent=random --game=ls20
```

For more information, see the [documentation](https://three.arcprize.org/docs#quick-start) or the [tutorial video](https://youtu.be/xEVg9dcJMkw).

## Changelog
## [0.9.3] - 2026-01-29
**Note: This will be a breaking change is you use the fields outline below**

### Added
- `FrameData` had two field names changes. 
  - `score` changed to `levels_completed`
  - `win_score` changed to `win_levels`
- Updated to use the new [ARC-AGI](https://github.com/arcprize/ARC-AGI) tool
  - Allows local execution of environments
  - Allows the creation of your own environments, see [Creating an Environment](https://docs.arcprize.org/add_game)
  - If you want to continue to use the online API/Replays set `ONLINE_ONLY` to `True` in `.env.example`

## [0.9.2] - 2025-08-19

### Added
- `available_actions` to `FrameData`
- `ACTION7` as possible `GameAction`

## [0.9.1] - 2025-07-18

Initial Release

## Contest Submission

To submit your agent for the ARC-AGI-3 competition, please use this form: https://forms.gle/wMLZrEFGDh33DhzV9.

## Contributing

We welcome contributions! To contribute to ARC-AGI-3-Agents, please follow these steps:

1.  Fork the repository and create a new branch for your feature or bugfix.
2.  Make your changes and ensure that all tests pass, you are welcome to add more tests for your specific fixes.
3.  This project uses `ruff` for linting and formatting. Please set up the pre-commit hooks to ensure your contributions match the project's style.
    ```bash
    pip install pre-commit
    pre-commit install
    ```
4.  Write clear commit messages describing your changes.
5.  Open a pull request with a description of your changes and the motivation behind them.

If you have questions or need help, feel free to open an issue.

## Tests

To run the tests, you will need to have `pytest` installed. Run the tests like this:

```bash
pytest
```

For more information on tests, please see the [tests documentation](https://three.arcprize.org/docs#testing).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
