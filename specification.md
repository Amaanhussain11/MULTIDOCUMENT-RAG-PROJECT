# Multi-Document RAG Service Platform

## Development Specification

**Version:** 1.0  
**Status:** Active Development Specification  
**Last Updated:** September 2026

> **IMPORTANT:** This document is the single source of truth for product behavior, UI/UX, architecture, data flow, security, coding conventions, and AI-assisted development.

> Every developer and AI coding tool MUST follow this specification before creating or modifying any part of the application.


# 1. Product Requirements

## 1.1 Product

Build a modern web-based Multi-Document RAG Service Platform that allows users to upload multiple documents and ask natural-language questions about their contents.

The application MUST support:

- Multiple document uploads.

- PDF, DOCX, and TXT files.

- Document processing status.

- Document listing.

- Document deletion.

- Natural-language querying.

- Semantic document retrieval.

- Context filtering.

- Context construction.

- Gemini-based answer generation.

- Source references.

- User/document isolation.

- Concurrent document processing.

## 1.2 Primary User Flow

The primary experience MUST remain:

```
Upload Documents
       ↓
Documents Processed
       ↓
Documents Ready
       ↓
Ask Question
       ↓
Retrieve Relevant Content
       ↓
Construct Context
       ↓
Generate Answer
       ↓
Display Answer + Sources
```

Do not add unnecessary user steps.

## 1.3 Product Behavior

The application SHOULD feel like a polished AI product rather than a developer tool.

The user should immediately understand:

- Where to upload documents.

- Which documents are ready.

- Where to ask questions.

- Whether the system is processing something.

- Where an answer came from.


# 2. UI/UX Requirements

## 2.1 Design Direction

The application MUST use a:

> **Modern, sleek, minimal, premium dark SaaS/AI interface.**

The UI MUST NOT look cluttered, overly colorful, old-fashioned, corporate-heavy, excessively animated, or like a generic dashboard.

## 2.2 Visual Principles

Prioritize:

1. Clean spacing.

2. Strong typography.

3. Subtle borders.

4. Clear hierarchy.

5. Minimal shadows.

6. Consistent components.

7. Restrained use of accent color.

8. Smooth but subtle interactions.

The interface should feel calm and focused.

## 2.3 Layout

Use a spacious centered layout.

Recommended maximum content width:

```
1400px
```

Content sections SHOULD generally use:

```
1200px
```

where appropriate.

## 2.4 Responsive Design

The application MUST support:

- Desktop

- Laptop

- Tablet

- Mobile

Desktop is the primary target. Do not simply shrink desktop layouts for mobile; layouts should intelligently reflow.

## 2.5 Navigation

Navigation MUST remain simple.

Preferred conceptual structure:

```
Logo / Product Name

Documents
Chat

                 User / Profile
```

Do not add navigation items unless they provide real product value.

## 2.6 Chat Experience

The chat interface MUST include:

```
Conversation Area
       ↓
Messages
       ↓
Sources
       ↓
Input
       ↓
Send
```

The input area should be visually prominent without dominating the page.

## 2.7 Document Experience

Documents should be presented as clean cards/list items.

Each document SHOULD display:

```
File Icon
Document Name
File Type / Size
Processing Status
Actions
```

## 2.8 Empty States

Empty states MUST explain what the user should do next.

Example:

```
No documents yet

Upload your first documents to start
asking questions about them.

[ Upload Documents ]
```

## 2.9 Loading States

Every asynchronous operation MUST have visible feedback.

Examples:

```
Uploading...
Processing...
Searching documents...
Generating answer...
```

Prefer skeletons, subtle spinners, or progress indicators over blocking full-screen loaders.

## 2.10 Animations

Animations MUST be subtle.

Use animation primarily for:

- Hover states.

- Button interactions.

- Modal transitions.

- Dropdown transitions.

- Loading indicators.

- Message appearance.

Avoid excessive parallax, bouncing, flashing, large page transitions, or decorative motion.


# 3. Frontend Architecture

## 3.1 Technology

Use:

```
React.js
Vite
Tailwind CSS
```

## 3.2 Responsibility

React MUST handle:

- UI rendering.

- User interactions.

- Frontend state.

- File selection.

- Upload requests.

- Processing status.

- Chat interaction.

- Source display.

- Loading states.

- Error states.

React MUST NOT:

- Call Gemini directly.

- Call Qdrant directly.

- Store private credentials.

- Perform vector retrieval.

- Generate embeddings.

- Implement backend RAG logic.

## 3.3 Structure

Use the following structure unless there is a strong reason to change it:

```
src/
│
├── components/
│   ├── ui/
│   ├── documents/
│   ├── chat/
│   └── layout/
│
├── pages/
│   ├── Home/
│   ├── Documents/
│   └── Chat/
│
├── services/
│   └── api.js
│
├── hooks/
├── state/
├── utils/
├── constants/
├── assets/
├── styles/
│
└── App.jsx
```

The structure MAY evolve, but responsibilities MUST remain separated.

## 3.4 Central API Layer

All backend communication MUST go through the API service layer.

Example:

```
services/api.js
```

Prefer functions such as:

```
uploadDocuments()
getDocuments()
getDocument()
deleteDocument()
sendChatQuery()
```

Components MUST NOT repeatedly implement raw HTTP requests.


# 4. Backend Architecture

## 4.1 Technology

Use:

```
Python
FastAPI
```

## 4.2 Architecture

The backend MUST follow:

```
React
   ↓
FastAPI Routes
   ↓
Service Layer
   ↓
External Services
```

External services:

```
Gemini
Qdrant
```

## 4.3 Structure

```
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── documents.py
│   │       ├── chat.py
│   │       └── health.py
│   │
│   ├── services/
│   │   ├── document_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── generation_service.py
│   │   └── qdrant_service.py
│   │
│   ├── parsers/
│   │   ├── base_parser.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   └── txt_parser.py
│   │
│   ├── schemas/
│   │   ├── document.py
│   │   └── query.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   └── utils/
│       ├── chunker.py
│       ├── cleaner.py
│       └── validator.py
│
└── tests/
    ├── test_chunker.py
    ├── test_cleaner.py
    ├── test_generation_service.py
    ├── test_ingestion_pipeline.py
    ├── test_parsers.py
    ├── test_retrieval_service.py
    ├── test_routes_chat.py
    ├── test_routes_documents.py
    └── test_validator.py
```

## 4.4 Route Responsibility

Routes MUST remain thin.

Preferred:

```
Request
  ↓
Route
  ↓
Service
  ↓
Result
  ↓
Response
```

Do not place complex business logic inside route handlers.


# 5. RAG Architecture

## 5.1 Document Pipeline

The ingestion pipeline MUST follow:

```
Upload
   ↓
Validation
   ↓
Parsing
   ↓
Text Cleaning
   ↓
Chunking
   ↓
Embedding
   ↓
Qdrant
```

## 5.2 Query Pipeline

The query pipeline MUST follow:

```
Question
   ↓
Query Embedding
   ↓
Qdrant Search
   ↓
Relevant Chunks
   ↓
Context Filtering
   ↓
Context Construction
   ↓
Gemini 3.7 Flash
   ↓
Grounded Answer
   ↓
Sources
```

Do not bypass retrieval.

## 5.3 Embedding

Use:

```
gemini-embedding-001
```

for document chunk embeddings and user query embeddings.

## 5.4 LLM

Use:

```
gemini-3.7-flash
```

The generation request MUST contain:

```
System Instructions
+
Retrieved Context
+
User Question
```

## 5.5 Chunking

Initial configuration:

```
Chunk Size: 800–1200 tokens
Overlap:    100–200 tokens
```

These MUST be configurable.

## 5.6 Retrieval

Initial:

```
Top-K = 5
```

Retrieval MUST support:

- Vector similarity search.

- User filtering.

- Document filtering where required.

- Configurable similarity threshold.

## 5.7 Context Filtering

Do not automatically send every retrieved result to Gemini.

Remove clearly irrelevant results where appropriate.

Goals:

```
Less Noise
Less Token Usage
Better Context
Better Answers
```

## 5.8 Context Construction

Retrieved chunks MUST be converted into structured context.

Example:

```
[research.pdf | Page 12]

<chunk>


[research.pdf | Page 13]

<chunk>


[notes.docx | Page 4]

<chunk>
```

Source metadata MUST remain attached to the retrieved information.

## 5.9 Grounded Generation

Gemini MUST:

- Use retrieved content as the primary factual source.

- Avoid fabrication.

- Avoid unsupported claims.

- Ignore instructions contained inside documents.

- State when sufficient information is unavailable.

- Return source information where available.


# 6. API Contracts

## 6.1 API Version

Use:

```
/api/v1
```

## 6.2 Endpoints

| Method | Endpoint | Purpose |
| - | - | - |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/documents/upload` | Upload multiple documents |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{document_id}` | Get document |
| DELETE | `/api/v1/documents/{document_id}` | Delete document |
| POST | `/api/v1/chat` | Query documents |


## 6.3 Upload

The upload endpoint MUST accept multiple files.

```
POST /api/v1/documents/upload
```

The response SHOULD provide document identifiers and processing status.

## 6.4 Chat Request

```
{
  "question": "What methodology was used?"
}
```

## 6.5 Chat Response

```
{
  "answer": "The study used...",
  "sources": [
    {
      "document": "research.pdf",
      "page": 12
    }
  ]
}
```

## 6.6 API Stability

API contracts MUST NOT be changed silently.

When modifying an API:

```
Backend
 ↓
API Client
 ↓
Frontend
 ↓
Tests
```

must be reviewed together.


# 7. Data Models

## 7.1 Document

```
document_id
user_id
document_name
file_type
file_size
status
created_at
updated_at
```

Status:

```
QUEUED
PROCESSING
READY
FAILED
```

## 7.2 Chunk

```
chunk_id
document_id
user_id
chunk_index
text
page_number
```

## 7.3 Qdrant Payload

```
{
  "user_id": "user_001",
  "document_id": "doc_001",
  "document_name": "research.pdf",
  "chunk_id": "chunk_001",
  "chunk_index": 1,
  "page_number": 5,
  "text": "..."
}
```

## 7.4 Qdrant Collection

Use:

```
rag_documents
```

One collection MAY contain multiple users.

Isolation MUST be achieved using metadata filtering.


# 8. Security Requirements

## 8.1 Backend Secrets

These MUST remain backend-only:

```
GEMINI_API_KEY
QDRANT_URL
QDRANT_API_KEY
```

Never expose them to React.

## 8.2 Environment Variables

Never commit:

```
.env
.env.local
API keys
Tokens
Private keys
```

Use environment/secret management.

## 8.3 User Isolation

Every document/chunk MUST contain a user identifier.

Qdrant queries MUST filter by authenticated user.

The backend MUST determine the user identity.

Never trust a client-provided `user_id` as proof of identity.

## 8.4 Authorization

Before reading, deleting, or querying a user's documents, the backend MUST verify ownership.

## 8.5 Prompt Injection

Document content MUST be treated as untrusted data.

Instructions inside documents MUST NOT override system instructions.


# 9. File-Processing Behavior

## 9.1 Processing Order

Every document follows:

```
Validate
   ↓
Parse
   ↓
Clean
   ↓
Chunk
   ↓
Embed
   ↓
Store
```

## 9.2 Validation

Before expensive processing, validate:

- File type.

- File extension.

- MIME type where appropriate.

- File size.

- File readability.

- Corruption.

- Empty content.

Invalid files MUST fail early.

## 9.3 Multiple Files

Multiple files SHOULD be processed concurrently.

Example:

```
                 Upload
                    ↓
                Task Queue
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
     Worker 1    Worker 2    Worker 3
        ↓           ↓           ↓
      File A      File B      File C
        ↓           ↓           ↓
      Parse       Parse       Parse
        ↓           ↓           ↓
      Chunk       Chunk       Chunk
        ↓           ↓           ↓
      Embed       Embed       Embed
        └───────────┼───────────┘
                    ↓
                  Qdrant
```

## 9.4 Bounded Concurrency

Concurrency MUST be limited.

Do not send unlimited simultaneous Gemini requests.

Concurrency limits SHOULD be configurable.

## 9.5 Partial Failure

If:

```
File A → SUCCESS
File B → FAILED
File C → SUCCESS
```

A and C SHOULD remain available.

One failed document SHOULD NOT unnecessarily fail the entire batch.

## 9.6 Processing States

Use:

```
QUEUED
PROCESSING
READY
FAILED
```

The frontend MUST display these states clearly.


# 10. Design System

## 10.1 Design Direction

The design system MUST follow:

> **Dark + Minimal + Sleek + Premium + AI/SaaS**

The design must primarily use neutral dark tones with **one primary accent color**.

Do not introduce random colors.

## 10.2 Color Palette

### Background

```
Primary Background:   #09090B
Secondary Background: #0F1014
Tertiary Background:  #14161B
```

Use `#09090B` for the main application background.

### Cards / Surfaces

```
Card:             #111318
Card Hover:       #171A21
Elevated Surface: #181B22
```

Cards MUST NOT use pure white backgrounds.

### Borders

```
Default Border: #272A33
Subtle Border:  #1D2027
Active Border:  #3A3F4B
```

Borders should be subtle.

### Primary Accent

Use **Electric Indigo**:

```
Primary:        #6366F1
Primary Hover:  #818CF8
Primary Active: #4F46E5
```

Use the primary accent for:

- Primary buttons.

- Active navigation.

- Focus states.

- Important links.

- Selected elements.

- Key interactive elements.

Do NOT use the accent color everywhere.

### Text

```
Primary Text:   #F4F4F5
Secondary Text: #A1A1AA
Muted Text:     #71717A
Disabled Text:  #52525B
```

### Status Colors

```
Success: #22C55E
Warning: #F59E0B
Error:   #EF4444
Info:    #38BDF8
```

Status colors should primarily communicate state rather than decoration.

## 10.3 Color Usage Rules

The visual hierarchy MUST generally follow:

```
Background
    ↓
Surface
    ↓
Card
    ↓
Interactive Element
    ↓
Primary Accent
```

Avoid using more than one strong accent color in the same component.

Do not use gradients by default.

If gradients are introduced later, they must remain subtle and use the established palette.

## 10.4 Buttons

### Primary Button

```
Background: #6366F1
Text:       #FFFFFF
Hover:      #818CF8
Active:     #4F46E5
```

Use for main actions such as:

```
Upload Documents
Ask
Send
Continue
```

### Secondary Button

```
Background: #181B22
Text:       #F4F4F5
Border:     #272A33
Hover:      #22252D
```

### Ghost Button

```
Background: transparent
Text:       #A1A1AA
Hover:      #181B22
```

### Destructive Button

```
Background: #EF4444
Text:       #FFFFFF
```

Use ONLY for destructive actions such as permanent deletion.

## 10.5 Cards

Cards MUST use:

```
Background: #111318
Border:     #272A33
Radius:     12px
```

Use subtle shadows only when necessary.

## 10.6 Inputs

Inputs MUST use:

```
Background:    #111318
Border:        #272A33
Text:          #F4F4F5
Placeholder:   #71717A
Focus Border:  #6366F1
```

Focus states must be clearly visible.

## 10.7 Border Radius

Use:

```
Small:        6px
Medium:       8px
Large:        12px
Extra Large:  16px
```

Preferred defaults:

```
Buttons: 8px
Inputs: 8px
Cards: 12px
Large Containers: 16px
```

## 10.8 Shadows

Shadows should be subtle.

The application should rely primarily on:

```
Contrast
Borders
Spacing
```

rather than large shadows.

## 10.9 Typography

Use:

```
Inter
```

Fallback:

```
system-ui
sans-serif
```

Typography hierarchy:

```
Page Heading:    32–40px
Section Heading: 24–28px
Subheading:      18–20px
Body:            14–16px
Small:           12–14px
```

Avoid excessive font sizes.

## 10.10 Icons

Use one consistent icon library throughout the application.

Icons MUST have a consistent visual style.

Do not mix random icon sets.


# 11. Coding Conventions

## 11.1 General

Code MUST prioritize:

```
Readability
Maintainability
Reusability
Testability
Separation of Concerns
```

## 11.2 Naming

Use descriptive names.

Good:

```
document_service
retrieve_chunks
generate_embedding
process_document
```

Bad:

```
ds
temp
foo
data2
thing
```

## 11.3 Functions

Functions should have one responsibility.

Avoid functions that simultaneously perform:

```
Validation
Parsing
Chunking
Embedding
Database Operations
Response Formatting
```

## 11.4 React Components

Components should primarily handle:

```
UI
Interaction
Presentation
```

Complex logic should be moved into hooks, services, utilities, or state management where appropriate.

## 11.5 Backend

Backend routes MUST remain thin.

Business logic belongs in services.

External service communication belongs in dedicated service modules.

## 11.6 Dependencies

Do not add a dependency unless it provides meaningful value.

Prefer existing project dependencies.

## 11.7 Configuration

Centralize configurable values:

```
Chunk Size
Chunk Overlap
Top-K
Similarity Threshold
Concurrency Limit
API URLs
```

Do not duplicate these values throughout the codebase.


# 12. Error-Handling Rules

## 12.1 Error Structure

Use:

```
{
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Only PDF, DOCX and TXT files are supported."
  }
}
```

## 12.2 User-Facing Errors

Errors must be understandable.

Bad:

```
500 Internal Server Error
```

Better:

```
We couldn't process this document.
Please check the file and try again.
```

## 12.3 Backend Errors

Never expose:

```
Stack traces
API keys
Internal paths
Database credentials
Raw provider errors
```

to users.

## 12.4 Retry

Retry transient failures such as:

```
Timeout
Temporary network failure
Rate limiting
Transient service failure
```

Do not retry permanent errors such as:

```
Invalid API key
Invalid request
Unsupported file
Authorization failure
```

## 12.5 UI Recovery

After an error, the UI should remain usable.

Where appropriate provide:

```
Retry
Remove
Try Again
```


# 13. Deployment Architecture

## 13.1 Frontend

```
GitHub
   ↓
Vercel
   ↓
React + Vite
   ↓
Production
```

## 13.2 Backend

Initial target:

```
GitHub
   ↓
GitHub Actions
   ↓
Google Cloud Functions
   ↓
FastAPI
```

Google Cloud Functions is provisional.

The architecture MUST remain portable to another backend deployment platform.

## 13.3 External Services

```
                 FastAPI
                /                      /                   Gemini         Qdrant
```

Gemini handles:

```
Embeddings
Generation
```

Qdrant handles:

```
Vector Storage
Vector Search
```

## 13.4 Docker

Docker MUST be used for reproducible backend development and testing.

The Docker environment should behave consistently across:

```
Developer Machine
CI
Deployment
```

## 13.5 CI/CD

Pull Request:

```
Install
 ↓
Lint
 ↓
Tests
 ↓
Build
 ↓
Docker Validation
```

Production:

```
Checks Pass
 ↓
Merge to main
 ↓
Production Deployment
```


# 14. AI-Assisted Development Rules

> **This section is mandatory for every AI coding agent working on this project.**

## 14.1 Specification First

Before writing code, the AI MUST:

```
Read specification.md
        ↓
Understand the requested feature
        ↓
Identify affected architecture
        ↓
Inspect existing code
        ↓
Implement consistently
```

Never immediately start creating files without inspecting the existing implementation.

## 14.2 Existing Code First

Before creating a new:

```
Component
Service
Hook
Utility
API
Parser
Model
```

the AI MUST check whether equivalent functionality already exists.

Reuse existing implementations whenever possible.

## 14.3 UI Consistency

The AI MUST follow the existing design system.

Before creating UI, check:

```
Colors
Typography
Spacing
Buttons
Inputs
Cards
Icons
Borders
Radius
Loading States
Error States
```

Do not invent new colors or styles.

Do NOT introduce arbitrary colors, random gradients, random card colors, or unrelated visual patterns without explicitly updating the design system.

## 14.4 UI Modification Rule

The AI MUST NOT redesign existing UI simply because it prefers another style.

If the user asks to add a feature, implement it using the existing design system.

Do not redesign unrelated components.

## 14.5 Architecture Rule

The AI MUST preserve:

```
React
 ↓
FastAPI
 ↓
Service Layer
 ↓
Gemini / Qdrant
```

Never create shortcuts such as:

```
React → Gemini
React → Qdrant
React → Database
```

## 14.6 RAG Rule

The AI MUST preserve:

```
Upload
 ↓
Validate
 ↓
Parse
 ↓
Clean
 ↓
Chunk
 ↓
Embed
 ↓
Qdrant
```

and:

```
Question
 ↓
Embed
 ↓
Retrieve
 ↓
Filter
 ↓
Construct Context
 ↓
Gemini
 ↓
Answer
```

Do not bypass retrieval unless explicitly requested.

## 14.7 API Rule

Never silently change:

```
Endpoint
Request Structure
Response Structure
Field Names
HTTP Methods
```

If an API contract needs to change, update:

```
Backend
Frontend API Client
Frontend Components
Tests
Specification
```

together.

## 14.8 Security Rule

The AI MUST NEVER:

- Expose Gemini credentials.

- Expose Qdrant credentials.

- Hardcode secrets.

- Commit `.env`.

- Put private credentials in Vite environment variables.

- Trust client-provided user IDs for authorization.

## 14.9 Dependency Rule

Before installing a package, check whether the project already contains functionality that solves the requirement.

Avoid unnecessary dependencies.

## 14.10 No Unnecessary Refactoring

If asked to modify one feature, do not refactor unrelated code.

Keep changes scoped.

## 14.11 No Duplicate Implementations

Do not create multiple services/components performing the same responsibility.

Prefer one clearly defined service for one responsibility.

## 14.12 Preserve Existing Behavior

Existing functionality MUST continue working unless the requested change intentionally modifies it.

## 14.13 Testing

When behavior changes:

```
Modify Code
 ↓
Add/Update Tests
 ↓
Run Tests
 ↓
Verify Existing Behavior
```

## 14.14 Documentation Synchronization

If a change affects:

```
Product Requirements
UI
Architecture
API
Data Models
RAG Flow
Security
Deployment
```

the AI MUST update `specification.md`.

## 14.15 Major Decisions

The AI MUST NOT silently make major architectural decisions.

If a request would significantly change:

- Authentication

- Database architecture

- RAG strategy

- API contracts

- Design system

- Deployment architecture

- Security model

the AI SHOULD ask the developer before proceeding.

## 14.16 Final Implementation Checklist

Before completing a task, the AI MUST verify:

```
[ ] specification.md was followed
[ ] Existing architecture was preserved
[ ] Existing components were reused where possible
[ ] UI follows the design system
[ ] No arbitrary colors were introduced
[ ] API contracts remain synchronized
[ ] Security requirements are satisfied
[ ] No unnecessary dependencies were added
[ ] No unnecessary refactoring was performed
[ ] Loading states are handled
[ ] Error states are handled
[ ] Tests were updated where necessary
[ ] Documentation was updated if required
```


# FINAL RULE

**Do not build features in isolation.**

Every change MUST fit into the existing product, UI, frontend architecture, backend architecture, RAG pipeline, API contracts, data models, security requirements, and design system.

The project should always feel like **one intentionally designed product**, regardless of whether the code was written by a human developer or an AI coding agent.

> **When in doubt: inspect existing code first, follow this specification second, and ask before making a major architectural or design decision.**

