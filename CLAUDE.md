# CLAUDE.md - Sidescroller Engine Guide

## Build & Run Commands
- **Run Engine**: `python src/main.py`
- **Run Tests**: `pytest tests/`
- **Run Single Test**: `pytest tests/test_file.py::test_function_name`
- **Debug Mode**: Set `DEBUG = True` in src/utils/constants.py

## Code Style Guidelines
- **Indentation**: 4 spaces (Python standard)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Imports**: Standard library first, then third-party (pygame), then local modules
- **File Structure**: Keep sprites in src/sprites/, utilities in src/utils/
- **Error Handling**: Use try/except for file/asset operations with informative error messages
- **Assets**: Store in resources/ directory with subdirectories for graphics, audio
- **Coordinate Systems**: Always specify coordinate system (world, grid, screen) in variable names
- **JSON Structure**: Follow level5.json format for level files

## Documentation
- Comment complex physics/collision calculations
- Keep Design Spec.txt updated when adding new features
- Document coordinate transformations between world/screen space
- Use type hints in function signatures