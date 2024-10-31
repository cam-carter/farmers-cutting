# 0.1.1a (2024-10-31)

## Added
- Added `enable_logging` option to control file operation logging per mod
  - Defaults to `false` if not specified
  - Controls both cleanup and generation messages
  - Errors are always logged regardless of setting
  - See [template.json](template.json) for reference

## Changed
- Fixed dye recipe filenames to include `_dye` suffix for tag-based recipes
- Refactored file operations for better maintainability

# 0.1.1 (2024-10-29)

## Added
- `stem` and `hyphae` recipe types

## Changed
- Simplified version string format for single-platform builds
  - Before: `1.20.1-1.0-fabric`
  - After: `1.20.1-1.0` (when only one platform)
- Updated [template.json](template.json) custom recipe format
