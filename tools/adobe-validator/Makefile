# Run from the Unison repository root, using macOS make.
# SDK_ROOT / BUILD_DIR / JOBS are read from the recipe environment by Python,
# never interpolated into shell source. This target never executes SDK outputs.
.PHONY: experimental-link
experimental-link:
	python3 tools/adobe-validator/experimental_build.py
