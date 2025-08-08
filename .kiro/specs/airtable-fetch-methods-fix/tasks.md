# Implementation Plan

- [x] 1. Add field mapping dictionary to ConfigurableAirtableClient initialization


  - Modify the `__init__` method to create a `self.fields` dictionary that maps logical field names to actual Airtable field names
  - Add `self.default_limit` attribute with a sensible default value (10)
  - Ensure the field mapping includes all necessary fields: website, email, company_description, ai_message, contacted
  - _Requirements: 1.2, 2.2, 3.2, 4.2, 5.2_



- [ ] 2. Implement shared _fetch_records helper method
  - Create `_fetch_records(self, *, formula: Optional[str], limit: Optional[int]) -> List[Dict[str, Any]]` method
  - Handle limit parameter conversion to max_records with default fallback
  - Implement proper kwargs construction for pyairtable API calls
  - Add comprehensive error handling with logging and empty list return on failure


  - Use existing `_convert_records_to_leads` method for consistent record format
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. Implement defensive formula builders
  - Create `_formula_for_outreach(self) -> Optional[str]` method that builds formulas for leads needing website scraping
  - Create `_formula_for_message_generation(self) -> Optional[str]` method that builds formulas for leads needing AI messages


  - Create `_formula_for_engagement(self) -> Optional[str]` method that builds formulas for leads ready for engagement
  - Implement defensive field mapping access using `.get()` method
  - Return None when required field mappings are missing to trigger no-filter fallback
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_



- [ ] 4. Add get_leads_for_outreach method with limit parameter
  - Create `get_leads_for_outreach(self, limit: Optional[int] = None) -> List[Dict[str, Any]]` method
  - Call `_formula_for_outreach()` to get the appropriate filter formula
  - Use `_fetch_records()` helper with the formula and limit parameters
  - Add proper docstring explaining the method's purpose


  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 5. Add get_leads_for_message_generation method with limit parameter
  - Create `get_leads_for_message_generation(self, limit: Optional[int] = None) -> List[Dict[str, Any]]` method
  - Call `_formula_for_message_generation()` to get the appropriate filter formula


  - Use `_fetch_records()` helper with the formula and limit parameters
  - Add proper docstring explaining the method's purpose
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Add get_leads_for_engagement method with limit parameter



  - Create `get_leads_for_engagement(self, limit: Optional[int] = None) -> List[Dict[str, Any]]` method
  - Call `_formula_for_engagement()` to get the appropriate filter formula
  - Use `_fetch_records()` helper with the formula and limit parameters
  - Add proper docstring explaining the method's purpose
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 7. Add proper type hints and imports
  - Add `from __future__ import annotations` import for forward references
  - Ensure `Optional` and `List` are imported from typing module
  - Add proper type hints to all new methods and parameters
  - Verify all existing imports are still valid and add any missing ones
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8. Test the implementation with background job simulation
  - Create a simple test script that imports ConfigurableAirtableClient
  - Test calling each of the three new methods with and without limit parameters
  - Verify no AttributeError exceptions are raised
  - Verify methods return lists (even if empty) rather than raising exceptions
  - Test with various limit values including None, 0, and positive integers
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_