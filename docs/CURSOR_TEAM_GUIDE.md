# Cursor Team Collaboration Guide

This guide establishes best practices for using Cursor AI in our development workflow to ensure consistency and efficiency across the team.

## General Cursor Usage Guidelines

### 1. Chat vs Composer
- **Chat**: Use for quick questions, code explanations, debugging help, and small edits
- **Composer**: Use for multi-file changes, refactoring across modules, and feature implementation

### 2. Prompt Best Practices
- Be specific and clear about what you want
- Provide context about the file/project you're working on
- Reference existing code patterns when asking for new features
- Break down complex tasks into smaller, focused requests
- Include error messages or expected behavior when reporting issues

### 3. Code Review with Cursor
- Use Cursor to explain code before submitting PRs
- Ask Cursor to check for common issues (security, performance, best practices)
- Use Cursor to generate PR descriptions based on changes
- Review AI-generated code thoroughly before committing

### 4. Documentation Standards
- Don't ask Cursor to create markdown documentation files unless explicitly needed
- Prefer inline code documentation (docstrings, comments, type hints)
- Use Cursor to improve existing documentation, not create new files

## Project-Specific Rules

### Backend (gc-service)
- Always use type hints in Python code
- Follow FastAPI patterns for API endpoints
- Use async/await for all I/O operations
- Implement proper error handling with HTTPException
- Reference `.cursorrules` file for detailed standards

### Frontend (gc-ui)
- Use TypeScript strictly (no `any` types)
- Follow React Native best practices
- Use design system values from `designSystem.ts`
- Implement proper error boundaries
- Reference `.cursorrules` file for detailed standards

## Team Workflow

### 1. Before Starting Work
- Pull latest changes from main branch
- Review relevant `.cursorrules` file
- Check for existing similar implementations
- Understand the codebase context

### 2. During Development
- Use Cursor to maintain consistency with existing code patterns
- Ask Cursor to explain unfamiliar code before modifying
- Use Cursor to suggest improvements, but review carefully
- Test AI-generated code thoroughly

### 3. Before Committing
- Review all AI-generated code
- Ensure code follows project standards
- Run linters and formatters
- Test functionality manually
- Check for security issues

### 4. Code Sharing
- When sharing code snippets, include file paths and line numbers
- Reference specific functions/classes when asking questions
- Provide context about the problem you're solving

## Common Patterns

### Asking for New Features
```
Good: "Add a new API endpoint POST /api/v1/clothes/{id}/favorite that 
      marks a clothing item as favorite. Follow the same pattern as 
      the existing clothes router, use the ClothesService, and return 
      the updated clothing item."

Bad: "Add favorite functionality"
```

### Debugging
```
Good: "I'm getting a 500 error when calling POST /api/v1/clothes. 
      The error occurs in app/services/clothing_service.py at line 45. 
      Here's the stack trace: [trace]. Can you help identify the issue?"

Bad: "API is broken"
```

### Refactoring
```
Good: "Refactor the image upload logic in app/services/storage_service.py 
      to extract the validation logic into a separate function. Keep the 
      same functionality but improve code organization."

Bad: "Make the code better"
```

## Avoiding Common Pitfalls

### 1. Don't Blindly Accept AI Suggestions
- Always review and understand AI-generated code
- Test thoroughly before committing
- Ensure it follows project standards

### 2. Don't Create Unnecessary Files
- Avoid asking Cursor to create documentation files
- Don't create duplicate utility functions
- Check if functionality already exists

### 3. Don't Ignore Project Standards
- Always follow the `.cursorrules` file
- Maintain consistency with existing code
- Use established patterns and conventions

### 4. Don't Skip Code Review
- AI-generated code still needs human review
- Check for edge cases and security issues
- Ensure proper error handling

## Cursor Settings Recommendations

### Recommended Settings
- Enable "Auto-format on save"
- Use project-specific `.cursorrules` files
- Enable code suggestions
- Use consistent indentation settings

### Workspace Configuration
- Each developer should have their own workspace settings
- Share common settings via `.cursorrules` files
- Use consistent formatter configurations

## Communication

### When to Ask for Help
- If Cursor suggests something that conflicts with project standards
- When unsure about the best approach
- Before making significant architectural changes
- When dealing with security-sensitive code

### Sharing Cursor Insights
- Share useful prompts that worked well
- Document patterns that Cursor helped establish
- Update `.cursorrules` based on team learnings

## Best Practices Summary

1. ✅ Be specific in prompts
2. ✅ Review all AI-generated code
3. ✅ Follow project standards
4. ✅ Test thoroughly
5. ✅ Use appropriate Cursor features (Chat vs Composer)
6. ✅ Maintain code consistency
7. ✅ Document complex logic
8. ✅ Share learnings with team

## Questions or Issues?

If you encounter issues with Cursor or have suggestions for improving these guidelines, discuss with the team and update this document accordingly.

