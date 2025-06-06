# Potter Refactoring Plan

## Overview

This document outlines a systematic approach to refactoring the Potter codebase while maintaining existing functionality. The refactoring will be done in phases to minimize risk and ensure continuous operation.

## Guiding Principles

1. **Test First**: Write comprehensive tests before refactoring
2. **Small Steps**: Make incremental changes that can be easily verified
3. **Maintain Compatibility**: Ensure the app continues to work throughout the process
4. **Clean Architecture**: Separate concerns and establish clear boundaries
5. **Document Everything**: Update documentation as we refactor

## Phase 1: Testing Foundation (Week 1)

### Goals
- Achieve 80%+ test coverage on critical components
- Establish CI/CD pipeline
- Create integration test suite

### Tasks
1. ✅ Create unit tests for:
   - ✅ LLM Client Manager
   - ✅ Text Processor
   - ✅ Prompts Manager
   - ⬜ Settings Manager
   - ⬜ Service orchestrator
   - ⬜ Hotkey Manager
   - ⬜ Permission Manager

2. ⬜ Set up pytest configuration with:
   - Coverage reporting
   - Parallel test execution
   - Test categorization (unit/integration/e2e)

3. ⬜ Create integration tests for:
   - Full text processing workflow
   - Settings persistence
   - API key validation
   - Hotkey registration

4. ⬜ Set up GitHub Actions for:
   - Running tests on PR
   - Coverage reporting
   - Build verification

## Phase 2: Extract Settings UI Components (Week 2-3)

### Goals
- Break down the 4,237-line cocoa_settings.py file
- Create reusable UI components
- Separate UI from business logic

### New Module Structure
```
src/
├── ui/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── window.py          # Main settings window (< 300 lines)
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   ├── prompt_dialog.py
│   │   │   ├── confirmation_dialog.py
│   │   │   └── base_dialog.py
│   │   ├── sections/
│   │   │   ├── __init__.py
│   │   │   ├── general_section.py
│   │   │   ├── prompts_section.py
│   │   │   ├── advanced_section.py
│   │   │   └── logs_section.py
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── hotkey_capture.py
│   │   │   ├── api_key_field.py
│   │   │   ├── prompt_table.py
│   │   │   └── theme_aware_icon.py
│   │   └── validators/
│   │       ├── __init__.py
│   │       ├── api_key_validator.py
│   │       ├── prompt_validator.py
│   │       └── hotkey_validator.py
```

### Refactoring Steps
1. ⬜ Extract custom widgets (HotkeyCapture, PasteableTextField, etc.)
2. ⬜ Extract dialog classes (PromptDialog, confirmation dialogs)
3. ⬜ Extract section views (General, Prompts, Advanced, Logs)
4. ⬜ Extract validation logic into separate validators
5. ⬜ Create base classes for common UI patterns
6. ⬜ Update imports and test everything works

## Phase 3: Implement Clean Architecture (Week 4-5)

### Goals
- Establish clear architectural boundaries
- Implement dependency injection
- Create domain models

### New Architecture
```
src/
├── domain/              # Business entities
│   ├── models/
│   │   ├── prompt.py
│   │   ├── settings.py
│   │   ├── api_key.py
│   │   └── hotkey.py
│   └── interfaces/      # Abstract interfaces
│       ├── llm_provider.py
│       ├── settings_repository.py
│       └── notification_service.py
├── application/         # Use cases
│   ├── process_text.py
│   ├── manage_prompts.py
│   ├── validate_api_key.py
│   └── update_settings.py
├── infrastructure/      # External services
│   ├── llm/
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── google_provider.py
│   ├── persistence/
│   │   ├── json_settings_repository.py
│   │   └── secure_api_key_storage.py
│   └── system/
│       ├── clipboard_service.py
│       ├── hotkey_service.py
│       └── notification_service.py
```

### Implementation Steps
1. ⬜ Define domain models with proper validation
2. ⬜ Create abstract interfaces for all external dependencies
3. ⬜ Implement use case classes with single responsibilities
4. ⬜ Move provider implementations to infrastructure layer
5. ⬜ Implement dependency injection container
6. ⬜ Update service layer to use clean architecture

## Phase 4: Improve Error Handling (Week 6)

### Goals
- Create proper exception hierarchy
- Implement user-friendly error messages
- Add retry mechanisms

### Tasks
1. ⬜ Create custom exceptions:
   ```python
   PotterException (base)
   ├── ConfigurationException
   │   ├── MissingApiKeyException
   │   ├── InvalidApiKeyException
   │   └── InvalidSettingsException
   ├── ProcessingException
   │   ├── ClipboardAccessException
   │   ├── LLMProviderException
   │   └── PromptNotFoundException
   └── SystemException
       ├── PermissionDeniedException
       ├── HotkeyRegistrationException
       └── InstanceAlreadyRunningException
   ```

2. ⬜ Implement error recovery strategies:
   - Automatic retry with exponential backoff
   - Fallback to cached responses
   - Graceful degradation

3. ⬜ Create user-friendly error messages:
   - Map technical errors to user actions
   - Provide clear resolution steps
   - Include relevant context

## Phase 5: Security Improvements (Week 7)

### Goals
- Implement secure API key storage
- Add input validation
- Improve logging security

### Tasks
1. ⬜ Implement secure storage:
   - Use macOS Keychain for API keys
   - Encrypt settings file
   - Clear sensitive data from memory

2. ⬜ Add input validation:
   - Sanitize clipboard content
   - Validate file paths
   - Limit prompt lengths

3. ⬜ Improve logging:
   - Remove sensitive data from logs
   - Implement log rotation
   - Add log level configuration

## Phase 6: Performance Optimization (Week 8)

### Goals
- Implement async processing
- Add caching layer
- Optimize resource usage

### Tasks
1. ⬜ Async implementation:
   - Make LLM calls asynchronous
   - Use background threads properly
   - Implement proper cancellation

2. ⬜ Caching:
   - Cache LLM responses (with TTL)
   - Cache settings in memory
   - Implement smart cache invalidation

3. ⬜ Resource optimization:
   - Lazy load UI components
   - Implement connection pooling
   - Optimize memory usage

## Phase 7: Documentation and Deployment (Week 9)

### Goals
- Complete documentation
- Set up automated deployment
- Create developer guidelines

### Tasks
1. ⬜ Documentation:
   - API documentation
   - Architecture diagrams
   - Developer setup guide
   - Contributing guidelines

2. ⬜ Deployment:
   - Automated builds
   - Release management
   - Update notifications

3. ⬜ Developer experience:
   - Pre-commit hooks
   - Code formatting
   - Linting rules

## Success Metrics

1. **Code Quality**
   - Test coverage > 80%
   - No files > 500 lines
   - Cyclomatic complexity < 10

2. **Performance**
   - Text processing < 2 seconds
   - Startup time < 1 second
   - Memory usage < 100MB

3. **Reliability**
   - Zero crashes in normal operation
   - Graceful error handling
   - No data loss

4. **Maintainability**
   - Clear module boundaries
   - Comprehensive documentation
   - Easy to add new features

## Risk Mitigation

1. **Feature Flags**: Use feature flags to enable/disable new code
2. **Parallel Development**: Keep old code until new code is proven
3. **Incremental Rollout**: Test with small group before full release
4. **Rollback Plan**: Maintain ability to revert to previous version
5. **Continuous Testing**: Run full test suite after each change

## Timeline Summary

- **Week 1**: Testing foundation
- **Week 2-3**: Extract UI components
- **Week 4-5**: Clean architecture
- **Week 6**: Error handling
- **Week 7**: Security
- **Week 8**: Performance
- **Week 9**: Documentation and deployment

Total estimated time: 9 weeks for complete refactoring

## Next Steps

1. Get stakeholder approval for the plan
2. Set up development environment
3. Begin Phase 1: Testing Foundation
4. Create progress tracking dashboard
5. Schedule weekly review meetings 