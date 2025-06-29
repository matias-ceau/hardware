# Test Fixtures

This directory contains test fixtures for the hardware inventory system.

## Required Files for Full Testing

To run all tests, you may want to add:

1. **test_component.png** - A sample image of electronic components for OCR testing
   - Should contain visible component labels (resistors, capacitors, etc.)
   - Recommended size: 800x600 or larger
   - Clear text showing values like "10kΩ", "100uF", quantities, etc.

2. **test_datasheet.pdf** - A sample component datasheet for resources testing
   - Any electronic component datasheet in PDF format
   - Used to test PDF parsing and content extraction

## Mock Data

The tests use the existing `data/electronics_updated_1.jsonld` file for database testing.

## Creating Test Images

For OCR testing, you can:
1. Take photos of electronic components with clear labels
2. Create mock component labels with text like:
   ```
   10kΩ Resistor
   ±5% Tolerance
   Carbon Film
   25 pieces
   $0.05 each
   ```
3. Use any clear image with electronic component text

## Security Note

Do not commit actual component photos or proprietary datasheets to the repository.
Use only generic test data or create mock images for testing purposes.